"""Step catalog formatter for Behave.

Register in ``behave.ini``::

    [behave.formatters]
    steps = behave_modern_html_report.step_catalog_formatter:StepCatalogFormatter

Then run::

    behave -f steps -o steps.html
"""

from __future__ import annotations

import contextlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from behave.formatter.base import Formatter  # type: ignore
except Exception:  # pragma: no cover
    Formatter = object  # type: ignore[misc,assignment]

from . import assets
from .step_scanner import StepCatalog, scan_directory


class StepCatalogFormatter(Formatter):  # type: ignore[misc,valid-type]
    """Behave formatter that produces a step definition catalog HTML."""

    name = "steps"
    description = "Step definition catalog (static analysis)"

    def __init__(self, stream_opener: Any, config: Any) -> None:
        super().__init__(stream_opener, config)

        userdata = getattr(config, "userdata", {}) or {}
        self._title = userdata.get("bmr.title", "Step Catalog")
        self._company = userdata.get("bmr.company", "")
        self._theme = userdata.get("bmr.theme", "auto")
        self._steps_dir = userdata.get("bmr.steps_dir", "features/steps")

        self._stream_opener = stream_opener
        self._config = config

    def _find_steps_dir(self) -> Path:
        base = Path(getattr(self._config, "base_dir", ".") or ".")
        candidates = [
            base / self._steps_dir,
            Path(self._steps_dir),
            base / "features" / "steps",
        ]
        for c in candidates:
            if c.is_dir():
                return c.resolve()
        return candidates[0].resolve()

    def close(self) -> None:
        steps_dir = self._find_steps_dir()
        catalog = scan_directory(steps_dir)
        html = render_catalog(catalog, title=self._title, company=self._company, theme=self._theme)

        stream = self._stream_opener.open()
        stream.write(html)
        with contextlib.suppress(Exception):
            stream.close()


def render_catalog(
    catalog: StepCatalog,
    title: str = "Step Catalog",
    company: str = "",
    theme: str = "auto",
) -> str:
    """Render a step catalog into a single-file HTML document."""
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("step_catalog.html.jinja")

    steps_data = [
        {
            "keyword": s.keyword,
            "pattern": s.pattern,
            "is_regex": s.is_regex,
            "func_name": s.func_name,
            "file_path": s.file_path,
            "line": s.line,
            "end_line": s.end_line,
            "docstring": s.docstring,
            "params": s.params,
            "source": s.source,
        }
        for s in catalog.steps
    ]

    return template.render(
        title=title,
        company=company,
        theme=theme,
        catalog=catalog,
        steps=steps_data,
        css=assets.css_bundle(),
        js=assets.read_text("js/step_catalog.js"),
        now=datetime.now(),
        data_json=json.dumps(
            {"steps": steps_data, "total": catalog.total, "by_keyword": catalog.by_keyword},
            default=str,
        ),
    )
