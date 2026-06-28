"""Jinja2-based renderer that turns an :class:`Execution` into HTML.

The renderer is intentionally decoupled from Behave so it can also be used by
tooling that reads pre-existing JSON reports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import assets
from . import statistics as stats_mod
from .models import Execution, as_dict
from .utils import format_duration

TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass(slots=True)
class RenderOptions:
    """User-facing rendering options."""

    title: str = "Behave Modern Report"
    company: str = ""
    logo_url: str = ""
    theme: str = "auto"  # auto | dark | light
    embed_assets: bool = True
    json_sidecar: bool = False
    custom_css: str = ""
    custom_js: str = ""
    extra: dict[str, str] = field(default_factory=dict)


class Renderer:
    """Renders an :class:`Execution` into a single-file HTML document."""

    def __init__(self, options: RenderOptions | None = None) -> None:
        self.options = options or RenderOptions()
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["duration"] = format_duration
        self.env.filters["status_icon"] = _status_icon
        self.env.filters["status_label"] = _status_label

    def render(self, execution: Execution) -> str:
        # Make sure statistics are up to date even if the caller skipped it.
        stats_mod.compute(execution)

        data = as_dict(execution)
        slowest = [as_dict(s) for s in stats_mod.slowest_scenarios(execution, limit=10)]
        buckets = stats_mod.duration_buckets(execution)
        tags = stats_mod.tag_ranking(execution)

        template = self.env.get_template("report.html.jinja")
        return template.render(
            execution=execution,
            data=data,
            tags=tags,
            data_json=json.dumps(
                {
                    "execution": data,
                    "slowest": slowest,
                    "buckets": buckets,
                    "tags": tags,
                },
                default=str,
            ),
            options=self.options,
            css=assets.css_bundle(self.options.custom_css),
            js=assets.js_bundle(self.options.custom_js),
            now=datetime.now(),
        )

    def render_to_file(self, execution: Execution, path: str | Path) -> Path:
        html = self.render(execution)
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        if self.options.json_sidecar:
            self._write_json_sidecar(execution, out)
        return out

    def render_json(self, execution: Execution) -> str:
        """Return a JSON representation of the execution and derived stats."""
        stats_mod.compute(execution)
        data = as_dict(execution)
        return json.dumps(
            {
                "execution": data,
                "slowest": [as_dict(s) for s in stats_mod.slowest_scenarios(execution, limit=10)],
                "buckets": stats_mod.duration_buckets(execution),
                "tags": stats_mod.tag_ranking(execution),
            },
            default=str,
            indent=2,
        )

    def _write_json_sidecar(self, execution: Execution, html_path: Path) -> None:
        json_path = html_path.with_suffix(".json")
        json_path.write_text(self.render_json(execution), encoding="utf-8")


# ---------------------------------------------------------------------------
# Jinja filters
# ---------------------------------------------------------------------------

_STATUS_ICONS = {
    "passed": "check",
    "failed": "x",
    "skipped": "skip",
    "undefined": "help",
    "pending": "clock",
    "untested": "dot",
    "error": "alert",
}

_STATUS_LABELS = {
    "passed": "Passed",
    "failed": "Failed",
    "skipped": "Skipped",
    "undefined": "Undefined",
    "pending": "Pending",
    "untested": "Untested",
    "error": "Error",
}


def _status_icon(status: str) -> str:
    return _STATUS_ICONS.get(status, "dot")


def _status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status.title())
