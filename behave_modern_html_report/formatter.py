"""Behave formatter entry point.

Register in `behave.ini`::

    [behave.formatters]
    modern = behave_modern_html_report.formatter:ModernHTMLFormatter

Then run::

    behave -f modern -o report.html
"""

from __future__ import annotations

import base64
import contextlib
import sys
from pathlib import Path
from typing import Any

try:
    from behave.formatter.base import Formatter  # type: ignore
except Exception:  # pragma: no cover - Behave optional at import time
    Formatter = object  # type: ignore[misc,assignment]

from .collector import Collector
from .models import Attachment
from .renderer import Renderer, RenderOptions
from .utils import guess_mime


class ModernHTMLFormatter(Formatter):  # type: ignore[misc,valid-type]
    """Behave formatter that produces a modern single-file HTML report."""

    name = "modern"
    description = "Modern single-file HTML report"

    def __init__(self, stream_opener: Any, config: Any) -> None:
        """Initialize the formatter with user options and a collector/renderer.

        Args:
            stream_opener (Any): Behave stream opener for the report output.
            config (Any): Behave configuration object.

        """
        super().__init__(stream_opener, config)

        userdata = getattr(config, "userdata", {}) or {}
        options = RenderOptions(
            title=userdata.get("bmr.title", "Behave Modern Report"),
            company=userdata.get("bmr.company", ""),
            logo_url=userdata.get("bmr.logo", ""),
            favicon_url=userdata.get("bmr.favicon", ""),
            theme=userdata.get("bmr.theme", "auto"),
            primary_color=userdata.get("bmr.primary_color", ""),
            accent_color=userdata.get("bmr.accent_color", ""),
            default_view=userdata.get("bmr.default_view", "dashboard"),
            hidden_views=_parse_list(userdata.get("bmr.hidden_views", "")),
            expand_by_default=_parse_bool(userdata.get("bmr.expand_by_default", "false")),
            max_slowest=_parse_int(userdata.get("bmr.max_slowest", "10"), 10),
            show_copy_command=_parse_bool(userdata.get("bmr.show_copy_command", "true")),
            show_environment_vars=_parse_bool(userdata.get("bmr.show_environment_vars", "true")),
            footer_text=userdata.get("bmr.footer_text", ""),
            link_to_ci=userdata.get("bmr.link_to_ci", ""),
            embed_assets=_parse_bool(userdata.get("bmr.embed", "true")),
            json_sidecar=_parse_bool(userdata.get("bmr.json_sidecar", "false")),
            custom_css=_read_optional(userdata.get("bmr.custom_css")),
            custom_js=_read_optional(userdata.get("bmr.custom_js")),
        )
        self._options = options
        self._collector = Collector(title=options.title)
        self._renderer = Renderer(options)

        self._output_path = self._resolve_output_path(stream_opener, config)

        # Keep references to the original Behave objects so that eof()
        # can read their final status/duration after execution completes.
        self._behave_feature: Any = None
        self._behave_scenario: Any = None

    # ------------------------------------------------------------------
    # Behave lifecycle
    # ------------------------------------------------------------------

    def feature(self, feature: Any) -> None:  # noqa: D401 - behave signature
        """Behave hook: a feature has started."""
        self._behave_feature = feature
        self._collector.start_feature(feature)

    def background(self, background: Any) -> None:
        """Behave hook: background steps are handled via the scenario."""
        pass

    def rule(self, rule: Any) -> None:
        """Behave hook: a rule has started (Gherkin v6, Behave 1.3.x)."""
        self._collector.start_rule(rule)

    def scenario(self, scenario: Any) -> None:
        """Behave hook: a scenario has started.

        Finalize the previous scenario (if any) using its original Behave
        object, which now has the final status/duration.
        """
        if self._behave_scenario is not None:
            self._collector.end_scenario(_FakeFinal(self._behave_scenario))
        self._behave_scenario = scenario
        self._collector.start_scenario(scenario)

    def step(self, step: Any) -> None:
        """Behave hook: step queued; final state arrives in ``result``."""
        pass

    def match(self, match: Any) -> None:
        """Behave hook: step matched to a step implementation."""
        pass

    def result(self, step: Any) -> None:
        """Behave hook: a step result is available."""
        self._collector.add_step(step)

    def eof(self) -> None:
        """Behave hook: end of feature; finalize current feature/scenario."""
        if self._behave_scenario is not None:
            self._collector.end_scenario(_FakeFinal(self._behave_scenario))
            self._behave_scenario = None

        if self._behave_feature is not None:
            self._collector.end_feature(_FakeFinal(self._behave_feature))
            self._behave_feature = None

    def close(self) -> None:
        """Behave hook: finalize the execution and write the HTML report."""
        execution = self._collector.finalize()
        html = self._renderer.render(execution)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html, encoding="utf-8")
        with contextlib.suppress(Exception):  # pragma: no cover
            sys.stdout.write(f"\nModern HTML report written to: {self._output_path}\n")

    # ------------------------------------------------------------------
    # Public attachment API for environment.py hooks.
    # ------------------------------------------------------------------

    def attach_file(self, path: str | Path, name: str | None = None) -> None:
        """Attach a file (will be base64-embedded in the report).

        Args:
            path (str | Path): Path to the file to attach.
            name (str | None, optional): Display name. Defaults to the file name.

        """
        p = Path(path)
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        self._collector.attach(
            Attachment(
                name=name or p.name,
                mime_type=guess_mime(p),
                data_base64=data,
            )
        )

    def attach_text(self, text: str, name: str = "log.txt", mime: str = "text/plain") -> None:
        """Attach a text snippet to the current step.

        Args:
            text (str): Text content to attach.
            name (str, optional): Display name. Defaults to ``log.txt``.
            mime (str, optional): MIME type. Defaults to ``text/plain``.

        """
        self._collector.attach(Attachment(name=name, mime_type=mime, text=text))

    def log(self, message: str) -> None:
        """Append a log line to the current step.

        Args:
            message (str): Log message to store.

        """
        self._collector.log(message)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_output_path(stream_opener: Any, config: Any) -> Path:
        """Resolve the output HTML path from Behave's stream opener or config.

        Args:
            stream_opener (Any): Behave stream opener.
            config (Any): Behave configuration object.

        Returns:
            Path: Output path for the HTML report.

        """
        candidate = getattr(stream_opener, "name", None) or getattr(stream_opener, "filename", None)
        if candidate:
            return Path(candidate)
        outputs = getattr(config, "outputs", None) or []
        for output in outputs:
            name = getattr(output, "name", None)
            if name and name not in ("<stdout>", "<stderr>"):
                return Path(name)
        return Path("behave-modern-html-report.html")


class _FakeFinal:
    """Wrap a Behave object so the collector's `end_*` reads its final status."""

    def __init__(self, source: Any) -> None:
        """Wrap a Behave object to expose its final status and duration.

        Args:
            source (Any): Behave object to wrap.

        """
        self.status = getattr(source, "status", None)
        self.duration = getattr(source, "duration", 0.0)


def _parse_bool(value: Any, default: bool = False) -> bool:
    """Parse a userdata string into a boolean."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() not in ("false", "0", "no", "")


def _parse_int(value: Any, default: int) -> int:
    """Parse a userdata string into an integer."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_list(value: Any) -> list[str]:
    """Parse a comma-separated userdata string into a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _read_optional(path: str | None) -> str:
    """Read a user-provided file path or return an empty string.

    Args:
        path (str | None): File path to read.

    Returns:
        str: File contents, or an empty string if the path is missing or invalid.

    """
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""
