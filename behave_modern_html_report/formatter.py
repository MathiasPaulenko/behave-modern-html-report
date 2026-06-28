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
        super().__init__(stream_opener, config)

        userdata = getattr(config, "userdata", {}) or {}
        options = RenderOptions(
            title=userdata.get("bmr.title", "Behave Modern Report"),
            company=userdata.get("bmr.company", ""),
            logo_url=userdata.get("bmr.logo", ""),
            theme=userdata.get("bmr.theme", "auto"),
            embed_assets=userdata.get("bmr.embed", "true").lower() != "false",
            json_sidecar=userdata.get("bmr.json_sidecar", "false").lower() == "true",
            custom_css=_read_optional(userdata.get("bmr.custom_css")),
            custom_js=_read_optional(userdata.get("bmr.custom_js")),
        )
        self._options = options
        self._collector = Collector(title=options.title)
        self._renderer = Renderer(options)

        self._output_path = self._resolve_output_path(stream_opener, config)

    # ------------------------------------------------------------------
    # Behave lifecycle
    # ------------------------------------------------------------------

    def feature(self, feature: Any) -> None:  # noqa: D401 - behave signature
        self._collector.start_feature(feature)

    def background(self, background: Any) -> None:
        # Background steps are surfaced via the scenario's own steps in Behave.
        pass

    def scenario(self, scenario: Any) -> None:
        self._collector.start_scenario(scenario)

    def step(self, step: Any) -> None:
        # Called when a step is queued; the final state arrives in `result`.
        pass

    def match(self, match: Any) -> None:
        pass

    def result(self, step: Any) -> None:
        self._collector.add_step(step)

    def eof(self) -> None:
        # End of file = end of feature in Behave.
        feature = self._collector._current_feature  # noqa: SLF001 - intentional
        if feature is not None:
            self._collector.end_feature(_FakeFinal(feature))

        # Also finalize the last scenario if Behave didn't call us back.
        scenario = self._collector._current_scenario  # noqa: SLF001
        if scenario is not None:
            self._collector.end_scenario(_FakeFinal(scenario))

    def close(self) -> None:
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
        """Attach a file (will be base64-embedded in the report)."""
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
        self._collector.attach(Attachment(name=name, mime_type=mime, text=text))

    def log(self, message: str) -> None:
        self._collector.log(message)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_output_path(stream_opener: Any, config: Any) -> Path:
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
        self.status = getattr(source, "status", None)
        self.duration = getattr(source, "duration", 0.0)


def _read_optional(path: str | None) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""
