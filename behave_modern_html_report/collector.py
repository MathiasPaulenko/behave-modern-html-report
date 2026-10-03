"""Collects Behave events and builds an :class:`Execution` tree.

The collector is intentionally decoupled from Behave's internals: it accepts
loosely-typed objects with the well-known attributes Behave exposes, which
keeps this layer easy to unit-test with simple stubs.
"""

from __future__ import annotations

import getpass
import os
import platform
import socket
import sys
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from . import statistics as stats_mod
from .models import (
    Attachment,
    Background,
    DataTable,
    Environment,
    ErrorInfo,
    Execution,
    Feature,
    Scenario,
    Statistics,
    Step,
    normalize_status,
)
from .utils import safe_str

_SENSITIVE_ENV_MARKERS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "CREDENTIAL",
    "PRIVATE",
    "AUTH",
    "COOKIE",
    "CERT",
    "APIKEY",
    "API_KEY",
    "_KEY",
)


def _is_sensitive_env_key(key: str) -> bool:
    """Return True if an env var name looks like it may hold a secret."""
    upper = key.upper()
    return any(marker in upper for marker in _SENSITIVE_ENV_MARKERS)


class Collector:
    """Builds an :class:`Execution` from formatter events.

    The collector keeps minimal state: the root :class:`Execution`, the
    current feature, the current rule (Gherkin v6 / Behave 1.3.x) and the
    current scenario.
    """

    def __init__(self, title: str = "Behave Modern Report") -> None:
        """Initialize a collector with an empty execution tree.

        Args:
            title (str, optional): Execution title. Defaults to
                "Behave Modern Report".

        """
        self.execution = Execution(title=title)
        self.execution.environment = self._capture_environment()
        self.execution.statistics = Statistics(start_time=datetime.now())
        self._current_feature: Feature | None = None
        self._current_rule_name: str = ""
        self._current_scenario: Scenario | None = None
        # Behave runs ``after_step`` hooks before reporting the step result,
        # so attachments/logs produced there land here and are flushed into
        # the step when it is added (or into the scenario at end_scenario).
        self._pending_attachments: list[Attachment] = []
        self._pending_logs: list[str] = []

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------

    @staticmethod
    def _capture_environment() -> Environment:
        """Capture runtime environment metadata (Python, Behave, host).

        Returns:
            Environment: Populated environment record.

        """
        try:
            from behave import __version__ as behave_version  # type: ignore
        except Exception:  # pragma: no cover
            behave_version = "unknown"

        try:
            cpu_count = os.cpu_count() or 0
        except Exception:  # pragma: no cover
            cpu_count = 0

        memory_mb = 0
        try:
            import psutil  # type: ignore

            memory_mb = int(psutil.virtual_memory().total / (1024 * 1024))
        except Exception:  # pragma: no cover
            pass

        try:
            user = getpass.getuser()
        except Exception:  # pragma: no cover
            user = ""

        git_info = Collector._capture_git_info()

        env_vars = {}
        for key in os.environ:
            if any(
                key.upper().startswith(prefix)
                for prefix in (
                    "CI",
                    "GITHUB",
                    "GITLAB",
                    "BITBUCKET",
                    "JENKINS",
                    "TRAVIS",
                    "CIRCLE",
                    "BUILD",
                    "AGENT",
                    "TF_",
                    "AZURE",
                )
            ) or key.upper() in {"PATH", "HOME", "USER", "USERPROFILE", "SHELL", "LANG", "TERM"}:
                env_vars[key] = "***" if _is_sensitive_env_key(key) else safe_str(os.environ[key])

        try:
            hostname = socket.gethostname()
        except Exception:  # pragma: no cover
            hostname = ""

        return Environment(
            python_version=sys.version.split()[0],
            behave_version=behave_version,
            platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
            hostname=hostname,
            cwd=safe_str(os.getcwd()),
            command=" ".join(sys.argv),
            user=user,
            cpu_count=cpu_count,
            memory_mb=memory_mb,
            git_branch=git_info.get("branch", ""),
            git_commit=git_info.get("commit", ""),
            git_remote=git_info.get("remote", ""),
            env_vars=env_vars,
        )

    @staticmethod
    def _capture_git_info() -> dict[str, str]:
        """Capture git branch, commit and remote if available."""
        info: dict[str, str] = {}
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0:
                info["branch"] = result.stdout.strip()
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0:
                info["commit"] = result.stdout.strip()
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0:
                info["remote"] = result.stdout.strip()
        except Exception:  # pragma: no cover
            pass
        return info

    # ------------------------------------------------------------------
    # Feature
    # ------------------------------------------------------------------

    def _make_background(self, behave_background: Any) -> Background:
        """Convert a Behave background object into a Background model."""
        bg = Background(
            name=getattr(behave_background, "name", "") or "",
            keyword=(getattr(behave_background, "keyword", "Background") or "Background"),
            location=safe_str(getattr(behave_background, "location", "")),
        )
        for behave_step in getattr(behave_background, "steps", []) or []:
            bg.steps.append(self._make_step(behave_step))
        return bg

    def _make_attachment(self, behave_attachment: Any) -> Attachment:
        """Convert a Behave embedding object into an Attachment model.

        Args:
            behave_attachment (Any): Behave embedding object.

        Returns:
            Attachment: Created attachment model.

        """
        import base64 as _b64

        mime_type = getattr(behave_attachment, "mime_type", "") or "application/octet-stream"
        name = (
            getattr(behave_attachment, "filename", "")
            or getattr(behave_attachment, "name", "")
            or "attachment"
        )

        raw_data = getattr(behave_attachment, "data", None)
        if raw_data is None:
            data_base64 = ""
        elif isinstance(raw_data, (bytes, bytearray)):
            data_base64 = _b64.b64encode(raw_data).decode("ascii")
        elif isinstance(raw_data, str):
            data_base64 = _b64.b64encode(raw_data.encode("utf-8")).decode("ascii")
        else:
            data_base64 = _b64.b64encode(str(raw_data).encode("utf-8")).decode("ascii")

        text = None
        if mime_type.startswith("text/") or mime_type in ("application/json", "application/xml"):
            try:
                if isinstance(raw_data, (bytes, bytearray)):
                    text = raw_data.decode("utf-8", errors="replace")
                elif isinstance(raw_data, str):
                    text = raw_data
                elif data_base64:
                    text = _b64.b64decode(data_base64).decode("utf-8", errors="replace")
            except Exception:
                text = None

        return Attachment(
            name=safe_str(name),
            mime_type=safe_str(mime_type),
            data_base64=data_base64,
            text=text,
        )

    def _make_step(self, behave_step: Any) -> Step:
        """Convert a Behave step object into a Step model."""
        try:
            duration = float(getattr(behave_step, "duration", 0.0) or 0.0)
        except (TypeError, ValueError):
            duration = 0.0
        step = Step(
            keyword=(getattr(behave_step, "keyword", "") or "").strip(),
            name=getattr(behave_step, "name", "") or "",
            status=normalize_status(getattr(behave_step, "status", None)),
            duration=duration,
            location=safe_str(getattr(behave_step, "location", "")),
            text=getattr(behave_step, "text", None),
        )

        table = getattr(behave_step, "table", None)
        if table is not None:
            try:
                step.table = DataTable(
                    headings=[safe_str(h) for h in getattr(table, "headings", []) or []],
                    rows=[[safe_str(c) for c in row.cells] for row in table.rows],
                )
            except Exception:  # pragma: no cover - defensive
                step.table = None

        error_message = getattr(behave_step, "error_message", None) or ""
        exception = getattr(behave_step, "exception", None)
        if error_message or exception:
            step.error = ErrorInfo(
                message=safe_str(error_message or exception),
                traceback=safe_str(getattr(behave_step, "exc_traceback", "") or error_message),
                exception_type=type(exception).__name__ if exception else "",
            )

        for behave_att in getattr(behave_step, "embeddings", []) or []:
            step.attachments.append(self._make_attachment(behave_att))

        step.logs = [safe_str(line) for line in getattr(behave_step, "log", []) or []]
        return step

    def start_feature(self, behave_feature: Any) -> Feature:
        """Start a new feature and add it to the execution tree.

        Args:
            behave_feature (Any): Behave feature object.

        Returns:
            Feature: Created feature model.

        """
        feature = Feature(
            name=getattr(behave_feature, "name", "") or "",
            description="\n".join(getattr(behave_feature, "description", []) or []),
            location=safe_str(getattr(behave_feature, "location", "")),
            tags=[safe_str(t) for t in getattr(behave_feature, "tags", []) or []],
        )
        behave_background = getattr(behave_feature, "background", None)
        if behave_background:
            feature.background = self._make_background(behave_background)
        self._current_feature = feature
        self.execution.features.append(feature)
        return feature

    def end_feature(self, behave_feature: Any) -> None:
        """Finalize the current feature with its final status and duration.

        Args:
            behave_feature (Any): Behave feature object with final state.

        """
        if self._current_feature is None:
            return
        self._current_feature.status = normalize_status(getattr(behave_feature, "status", None))
        try:
            self._current_feature.duration = float(getattr(behave_feature, "duration", 0.0) or 0.0)
        except (TypeError, ValueError):
            self._current_feature.duration = 0.0
        self._current_feature = None
        self._current_rule_name = ""

    # ------------------------------------------------------------------
    # Rule
    # ------------------------------------------------------------------

    def start_rule(self, behave_rule: Any) -> None:
        """Start a new rule under the current feature.

        Args:
            behave_rule (Any): Behave rule object.

        """
        self._current_rule_name = getattr(behave_rule, "name", "") or ""

    def end_rule(self) -> None:
        """Finalize the current rule."""
        self._current_rule_name = ""

    # ------------------------------------------------------------------
    # Scenario
    # ------------------------------------------------------------------

    def start_scenario(self, behave_scenario: Any) -> Scenario:
        """Start a new scenario under the current feature.

        Args:
            behave_scenario (Any): Behave scenario object.

        Returns:
            Scenario: Created scenario model.

        """
        scenario_type = safe_str(getattr(behave_scenario, "type", ""))
        parent = getattr(behave_scenario, "parent", None)
        # Behave calls the formatter with each expanded Scenario of an outline
        # (type="scenario"), never with the ScenarioOutline itself. Expanded
        # instances carry ``_row`` and point at the outline via ``parent``.
        parent_is_outline = getattr(parent, "type", "") == "scenario_outline"
        is_outline = (
            scenario_type in ("scenario_outline", "outline")
            or parent_is_outline
            or getattr(behave_scenario, "_row", None) is not None
        )
        outline_name = ""
        examples = None
        if is_outline:
            outline = parent if parent_is_outline else behave_scenario
            outline_name = (
                getattr(behave_scenario, "outline_name", "")
                or getattr(outline, "name", "")
                or getattr(behave_scenario, "name", "")
                or ""
            )
            examples = self._make_examples(getattr(outline, "examples", None))

        scenario = Scenario(
            name=getattr(behave_scenario, "name", "") or "",
            description="\n".join(getattr(behave_scenario, "description", []) or []),
            location=safe_str(getattr(behave_scenario, "location", "")),
            tags=[safe_str(t) for t in getattr(behave_scenario, "tags", []) or []],
            feature_name=self._current_feature.name if self._current_feature else "",
            rule_name=self._current_rule_name,
            is_outline=is_outline,
            outline_name=outline_name,
            examples=examples,
        )
        # Metadata-only background: executed background steps arrive via
        # add_step(is_background=True) so they carry their real status.
        behave_background = getattr(behave_scenario, "background", None)
        if behave_background is not None:
            scenario.background = Background(
                name=getattr(behave_background, "name", "") or "",
                keyword=(getattr(behave_background, "keyword", "Background") or "Background"),
                location=safe_str(getattr(behave_background, "location", "")),
            )
        self._current_scenario = scenario
        if self._current_feature is not None:
            self._current_feature.scenarios.append(scenario)
        return scenario

    def _make_examples(self, behave_examples: Any) -> DataTable | None:
        """Convert Behave examples tables into a DataTable model."""
        if not behave_examples:
            return None
        source = behave_examples
        if isinstance(source, (list, tuple)):
            if not source:
                return None
            source = source[0]
        # Behave 1.3.x ``Examples`` objects expose ``.table``; older objects
        # expose ``.tables``; a bare Table exposes ``.headings`` directly.
        table = getattr(source, "table", None)
        if table is None:
            tables = getattr(source, "tables", None)
            if tables:
                table = tables[0] if isinstance(tables, list) else tables
        if table is None and hasattr(source, "headings"):
            table = source
        if table is None:
            return None
        try:
            headings = [safe_str(h) for h in getattr(table, "headings", []) or []]
            rows = [[safe_str(c) for c in row.cells] for row in table.rows]
            return DataTable(headings=headings, rows=rows)
        except Exception:
            return None

    def end_scenario(self, behave_scenario: Any) -> None:
        """Finalize the current scenario with its final status and duration.

        Args:
            behave_scenario (Any): Behave scenario object with final state.

        """
        if self._current_scenario is None:
            return
        scenario = self._current_scenario
        scenario.attachments.extend(self._pending_attachments)
        scenario.logs.extend(self._pending_logs)
        self._pending_attachments.clear()
        self._pending_logs.clear()
        scenario.status = normalize_status(getattr(behave_scenario, "status", None))
        try:
            scenario.duration = float(getattr(behave_scenario, "duration", 0.0) or 0.0)
        except (TypeError, ValueError):
            scenario.duration = 0.0
        self._current_scenario = None

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def add_step(self, behave_step: Any, is_background: bool = False) -> Step | None:
        """Add a step result to the current scenario.

        Args:
            behave_step (Any): Behave step object with final state.
            is_background (bool, optional): True when the step belongs to the
                scenario's background (they are reported separately so they
                keep their real status instead of duplicating the feature
                background template steps).

        Returns:
            Step | None: Created step model, or None if no scenario is active.

        """
        if self._current_scenario is None:
            return None
        step = self._make_step(behave_step)
        step.attachments.extend(self._pending_attachments)
        step.logs.extend(self._pending_logs)
        self._pending_attachments.clear()
        self._pending_logs.clear()
        scenario = self._current_scenario
        if is_background and scenario.background is not None:
            scenario.background.steps.append(step)
        else:
            scenario.steps.append(step)
        return step

    # ------------------------------------------------------------------
    # Attachments / logs (extension API for environment.py hooks)
    # ------------------------------------------------------------------

    def _last_step(self) -> Step | None:
        """Return the most recently executed step, including background steps."""
        scenario = self._current_scenario
        if scenario is None:
            return None
        if scenario.steps:
            return scenario.steps[-1]
        if scenario.background and scenario.background.steps:
            return scenario.background.steps[-1]
        return None

    def attach(self, attachment: Attachment) -> None:
        """Attach a file to the current step (last step) or scenario.

        Args:
            attachment (Attachment): Attachment to store.

        """
        if self._current_scenario is None:
            return
        last_step = self._last_step()
        if last_step is not None:
            last_step.attachments.append(attachment)
        else:
            self._pending_attachments.append(attachment)

    def attach_embedding(self, mime_type: str, data: Any, name: str = "attachment") -> None:
        """Attach raw embedded data as Behave's ``formatter.embedding`` does.

        Args:
            mime_type (str): MIME type of the embedded data.
            data (Any): Raw data (bytes or str) to embed.
            name (str, optional): Display name. Defaults to ``attachment``.

        """
        self.attach(
            self._make_attachment(SimpleNamespace(mime_type=mime_type, filename=name, data=data))
        )

    def log(self, message: str) -> None:
        """Append a log line to the current step.

        Args:
            message (str): Log message to store.

        """
        last_step = self._last_step()
        if last_step is not None:
            last_step.logs.append(message)
        elif self._current_scenario is not None:
            self._pending_logs.append(message)

    # ------------------------------------------------------------------
    # Finalize
    # ------------------------------------------------------------------

    def finalize(self) -> Execution:
        """Finalize the execution tree and compute statistics.

        Returns:
            Execution: Fully populated execution model.

        """
        self.execution.statistics.end_time = datetime.now()
        stats_mod.compute(self.execution)
        return self.execution
