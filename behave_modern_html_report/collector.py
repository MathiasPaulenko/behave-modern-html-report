"""Collects Behave events and builds an :class:`Execution` tree.

The collector is intentionally decoupled from Behave's internals: it accepts
loosely-typed objects with the well-known attributes Behave exposes, which
keeps this layer easy to unit-test with simple stubs.
"""

from __future__ import annotations

import platform
import socket
import sys
from datetime import datetime
from typing import Any

from . import statistics as stats_mod
from .models import (
    Attachment,
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


class Collector:
    """Builds an :class:`Execution` from formatter events.

    The collector keeps minimal state: the root :class:`Execution`, the
    current feature and the current scenario.
    """

    def __init__(self, title: str = "Behave Modern Report") -> None:
        """Initialize a collector with an empty execution tree."""
        self.execution = Execution(title=title)
        self.execution.environment = self._capture_environment()
        self.execution.statistics = Statistics(start_time=datetime.now())
        self._current_feature: Feature | None = None
        self._current_scenario: Scenario | None = None

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------

    @staticmethod
    def _capture_environment() -> Environment:
        """Capture runtime environment metadata (Python, Behave, host)."""
        try:
            from behave import __version__ as behave_version  # type: ignore
        except Exception:  # pragma: no cover
            behave_version = "unknown"
        return Environment(
            python_version=sys.version.split()[0],
            behave_version=behave_version,
            platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
            hostname=socket.gethostname(),
            cwd=safe_str(sys.argv[0] if sys.argv else ""),
            command=" ".join(sys.argv),
        )

    # ------------------------------------------------------------------
    # Feature
    # ------------------------------------------------------------------

    def start_feature(self, behave_feature: Any) -> Feature:
        """Start a new feature and add it to the execution tree."""
        feature = Feature(
            name=getattr(behave_feature, "name", "") or "",
            description="\n".join(getattr(behave_feature, "description", []) or []),
            location=safe_str(getattr(behave_feature, "location", "")),
            tags=[safe_str(t) for t in getattr(behave_feature, "tags", []) or []],
        )
        self._current_feature = feature
        self.execution.features.append(feature)
        return feature

    def end_feature(self, behave_feature: Any) -> None:
        """Finalize the current feature with its final status and duration."""
        if self._current_feature is None:
            return
        self._current_feature.status = normalize_status(getattr(behave_feature, "status", None))
        self._current_feature.duration = float(getattr(behave_feature, "duration", 0.0) or 0.0)
        self._current_feature = None

    # ------------------------------------------------------------------
    # Scenario
    # ------------------------------------------------------------------

    def start_scenario(self, behave_scenario: Any) -> Scenario:
        """Start a new scenario under the current feature."""
        scenario = Scenario(
            name=getattr(behave_scenario, "name", "") or "",
            description="\n".join(getattr(behave_scenario, "description", []) or []),
            location=safe_str(getattr(behave_scenario, "location", "")),
            tags=[safe_str(t) for t in getattr(behave_scenario, "tags", []) or []],
            feature_name=self._current_feature.name if self._current_feature else "",
        )
        self._current_scenario = scenario
        if self._current_feature is not None:
            self._current_feature.scenarios.append(scenario)
        return scenario

    def end_scenario(self, behave_scenario: Any) -> None:
        """Finalize the current scenario with its final status and duration."""
        if self._current_scenario is None:
            return
        self._current_scenario.status = normalize_status(getattr(behave_scenario, "status", None))
        self._current_scenario.duration = float(getattr(behave_scenario, "duration", 0.0) or 0.0)
        self._current_scenario = None

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def add_step(self, behave_step: Any) -> Step | None:
        """Add a step result to the current scenario."""
        if self._current_scenario is None:
            return None
        step = Step(
            keyword=(getattr(behave_step, "keyword", "") or "").strip(),
            name=getattr(behave_step, "name", "") or "",
            status=normalize_status(getattr(behave_step, "status", None)),
            duration=float(getattr(behave_step, "duration", 0.0) or 0.0),
            location=safe_str(getattr(behave_step, "location", "")),
            text=getattr(behave_step, "text", None),
        )

        table = getattr(behave_step, "table", None)
        if table is not None:
            try:
                step.table = DataTable(
                    headings=list(table.headings),
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

        self._current_scenario.steps.append(step)
        return step

    # ------------------------------------------------------------------
    # Attachments / logs (extension API for environment.py hooks)
    # ------------------------------------------------------------------

    def attach(self, attachment: Attachment) -> None:
        """Attach a file to the current step (last step) or scenario."""
        if self._current_scenario is None:
            return
        if self._current_scenario.steps:
            self._current_scenario.steps[-1].attachments.append(attachment)
        else:  # pragma: no cover - rare
            # Scenario-level attachment: stash on a virtual "setup" step.
            self._current_scenario.steps.append(
                Step(keyword="", name="(attachment)", attachments=[attachment])
            )

    def log(self, message: str) -> None:
        """Append a log line to the current step."""
        if self._current_scenario and self._current_scenario.steps:
            self._current_scenario.steps[-1].logs.append(message)

    # ------------------------------------------------------------------
    # Finalize
    # ------------------------------------------------------------------

    def finalize(self) -> Execution:
        """Finalize the execution tree and compute statistics."""
        self.execution.statistics.end_time = datetime.now()
        stats_mod.compute(self.execution)
        return self.execution
