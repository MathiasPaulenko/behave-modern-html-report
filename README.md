# Behave Modern Report

> The modern, beautiful, single-file HTML report formatter for [Behave](https://behave.readthedocs.io/).
> Dark mode, charts, instant search, attachments, zero external requests.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](./CHANGELOG.md)

`behave-modern-report` is a drop-in formatter for Behave that produces a single,
self-contained HTML file — everything (CSS, JS, fonts, icons, attachments) is
embedded so the report works offline, on any machine, forever.

## Features

- 🌓 **Dark / Light / Auto** themes, modern Material-3 inspired UI
- 📊 **Interactive charts** (status pie, duration histogram, slowest scenarios, timeline) — pure vanilla JS, no Chart.js CDN
- 🔍 **Instant client-side search** across features, scenarios, steps and tags
- 🎚️ **Filter by status** with one click
- 📁 **Expandable** features → scenarios → steps with rich metadata
- 🧯 **Modern error viewer** with copy-to-clipboard tracebacks
- 🖼️ **Attachments**: images (with lightbox), JSON, text, binaries
- ♿ **Accessible**: keyboard navigation, ARIA labels, reduced-motion support
- 📦 **Single HTML file**, works offline, no web server, no CDN
- 🧩 **Clean architecture** — formatter / collector / models / renderer separation, fully testable
- 🛠️ **Extensible** — custom CSS/JS, custom title/logo/company, future plugin system

## Installation

```bash
pip install behave-modern-report
```

## Quick start

In your project's `behave.ini` (or `setup.cfg`):

```ini
[behave.formatters]
modern = behave_modern_report.formatter:ModernHTMLFormatter
```

Then run:

```bash
behave -f modern -o report.html
```

Open `report.html` in any browser. Done.

## Configuration

All options are read from `behave`'s `userdata`:

```ini
[behave.userdata]
bmr.title    = My Awesome Suite
bmr.company  = Acme Inc.
bmr.logo     = https://example.com/logo.svg
bmr.theme    = auto          ; auto | dark | light
bmr.custom_css = path/to/extra.css
bmr.custom_js  = path/to/extra.js
```

## Attachments from your `environment.py`

```python
def after_step(context, step):
    formatter = context._runner.formatters[0]  # the modern formatter
    if step.status == "failed":
        formatter.attach_file("screenshot.png", name="failure.png")
        formatter.attach_text(str(step.exception), name="error.txt")
```

## Generate a demo without running Behave

```bash
python examples/generate_demo.py
```

This builds `examples/demo-report.html` with a realistic-looking suite —
useful for previews, screenshots, and design iteration.

## Architecture

```text
behave events
    │
    ▼
 formatter.py ── thin adapter
    │
    ▼
 collector.py ── builds the model tree
    │
    ▼
   models.py  ── pure dataclasses (Execution → Feature → Scenario → Step)
    │
    ▼
 statistics.py ── aggregates counters, durations, buckets
    │
    ▼
 renderer.py  + templates/ + assets/  ── Jinja2 → single HTML file
```

The renderer is **independent of Behave**, so any tool that can produce an
`Execution` object (e.g. a JSON loader) can use it.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Roadmap

The architecture is designed to support, without major refactors:

- Historical reports & report comparison
- Parallel execution timeline
- Plugin system (custom widgets, custom collectors)
- Localization
- PDF / JSON / CSV export
- AI-generated summaries
- MCP integration
- GitHub Actions annotations

## License

[MIT](LICENSE) © Behave Modern Report Contributors
