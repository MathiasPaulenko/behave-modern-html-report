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
        """Initialize the renderer with options and Jinja environment.

        Args:
            options (RenderOptions | None, optional): Rendering options.
                Defaults to a fresh RenderOptions instance.

        """
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
        """Render an execution into a single-file HTML report.

        Args:
            execution (Execution): Execution tree to render.

        Returns:
            str: Self-contained HTML document.

        """
        # Make sure statistics are up to date even if the caller skipped it.
        stats_mod.compute(execution)

        data = as_dict(execution)
        slowest = [as_dict(s) for s in stats_mod.slowest_scenarios(execution, limit=10)]
        buckets = stats_mod.duration_buckets(execution)
        tags = stats_mod.tag_ranking(execution)
        errors = stats_mod.error_distribution(execution)
        features_stats = stats_mod.feature_stats(execution)
        percentiles = stats_mod.duration_percentiles(execution)
        status_distribution = execution.statistics.by_status

        template = self.env.get_template("report.html.jinja")
        return template.render(
            execution=execution,
            data=data,
            tags=tags,
            buckets=buckets,
            errors=errors,
            slowest=slowest,
            features_stats=features_stats,
            percentiles=percentiles,
            status_distribution=status_distribution,
            data_json=json.dumps(
                {
                    "execution": data,
                    "slowest": slowest,
                    "buckets": buckets,
                    "tags": tags,
                    "errors": errors,
                },
                default=str,
            ),
            options=self.options,
            css=assets.css_bundle(self.options.custom_css),
            js=assets.js_bundle(self.options.custom_js),
            now=datetime.now(),
        )

    def render_to_file(self, execution: Execution, path: str | Path) -> Path:
        """Render the report and write it to the given path.

        Also writes a JSON sidecar if the option is enabled.

        Args:
            execution (Execution): Execution tree to render.
            path (str | Path): Output path for the HTML report.

        Returns:
            Path: Path to the written HTML report.

        """
        html = self.render(execution)
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        if self.options.json_sidecar:
            self._write_json_sidecar(execution, out)
        return out

    def render_json(self, execution: Execution) -> str:
        """Return a JSON representation of the execution and derived stats.

        Args:
            execution (Execution): Execution tree to serialize.

        Returns:
            str: Pretty-printed JSON document.

        """
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
        """Write a JSON sidecar next to the HTML report path.

        Args:
            execution (Execution): Execution tree to serialize.
            html_path (Path): Path of the HTML report; ``.json`` is appended.

        """
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
    "pending_warn": "clock",
    "untested": "dot",
    "error": "alert",
    "hook_error": "alert",
    "cleanup_error": "alert",
    "xfailed": "x",
    "xpassed": "check",
}

_STATUS_LABELS = {
    "passed": "Passed",
    "failed": "Failed",
    "skipped": "Skipped",
    "undefined": "Undefined",
    "pending": "Pending",
    "pending_warn": "Pending",
    "untested": "Untested",
    "error": "Error",
    "hook_error": "Hook Error",
    "cleanup_error": "Cleanup Error",
    "xfailed": "Expected Failure",
    "xpassed": "Unexpected Pass",
}


def _status_icon(status: str) -> str:
    """Return the SVG icon id for a given status.

    Args:
        status (str): Canonical status name.

    Returns:
        str: SVG icon id.

    """
    return _STATUS_ICONS.get(status, "dot")


def _status_label(status: str) -> str:
    """Return a human-readable label for a given status.

    Args:
        status (str): Canonical status name.

    Returns:
        str: Human-readable label.

    """
    return _STATUS_LABELS.get(status, status.title())
