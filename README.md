# Behave Modern HTML Report

> The modern, beautiful, single-file HTML report formatter for [Behave](https://behave.readthedocs.io/).
> Dark mode, charts, instant search, attachments, zero external requests.

[![PyPI](https://img.shields.io/pypi/v/behave-modern-html-report.svg)](https://pypi.org/project/behave-modern-html-report/)
[![Python](https://img.shields.io/pypi/pyversions/behave-modern-html-report.svg)](https://pypi.org/project/behave-modern-html-report/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/MathiasPaulenko/behave-modern-html-report/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-modern-html-report/actions/workflows/ci.yml)

`behave-modern-html-report` is a drop-in formatter for Behave that produces a single,
self-contained HTML file — everything (CSS, JS, fonts, icons, attachments) is
embedded so the report works offline, on any machine, forever.

## Features

- 🌓 **Dark / Light / Auto** themes, modern Material-3 inspired UI
- 📊 **Interactive charts** (status pie, duration histogram, slowest scenarios, tag pass rate, timeline) — pure vanilla JS, no Chart.js CDN
- 🏷️ **Tag analytics** page: per-tag counts, pass rate, duration, and a dedicated chart
- � **Gherkin Rules** support: scenarios under a `Rule` are grouped and tagged correctly (Behave 1.3.x)
- �🔍 **Instant client-side search** across features, scenarios, steps and tags
- 🎚️ **Filter by status** with one click
- 📁 **Expandable** features → scenarios → steps with rich metadata
- 🧯 **Modern error viewer** with copy-to-clipboard tracebacks
- 🖼️ **Attachments**: images (with lightbox), JSON, text, binaries
- 🚀 **Copy-reproduce-command** per scenario (`behave features/example.feature:3`)
- 📊 **Inline step duration bars** to spot slow steps at a glance
- ♿ **Accessible**: keyboard navigation, ARIA labels, reduced-motion support
- 📦 **Single HTML file**, works offline, no web server, no CDN
- 🧩 **Clean architecture** — formatter / collector / models / renderer separation, fully testable
- 🛠️ **Extensible** — custom CSS/JS, custom title/logo/company, JSON sidecar, future plugin system

## Installation

```bash
pip install behave-modern-html-report
```

## Quick start

In your project's `behave.ini` (or `setup.cfg`):

```ini
[behave.formatters]
modern = behave_modern_html_report.formatter:ModernHTMLFormatter
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
bmr.title         = My Awesome Suite
bmr.company       = Acme Inc.
bmr.logo          = https://example.com/logo.svg
bmr.theme         = auto          ; auto | dark | light
bmr.json_sidecar  = true          ; writes report.json next to report.html
bmr.custom_css    = path/to/extra.css
bmr.custom_js     = path/to/extra.js
```

## Behave 1.3.x and Gherkin Rules compatibility

`behave-modern-html-report` is tested against Behave 1.3.x and fully supports the Gherkin `Rule` keyword.

- Scenarios under a `Rule` keep their parent rule name and inherit their Rule tags correctly.
- Extended final statuses (`error`, `hook_error`, `cleanup_error`, `xfailed`, `xpassed`, `pending_warn`) are normalised and displayed in the UI.
- Error-like statuses are grouped as failures for feature status and tag analytics.

```gherkin
Feature: Checkout

  Rule: Payment required
    @payment
    Scenario: Card payment succeeds
      Given the user has items in cart
      When they pay with a valid card
      Then the order is confirmed
```

## Attachments from your `environment.py`

Use the public helper API — no need to reach into the formatter:

```python
from behave_modern_html_report import attach_screenshot, attach_text, log

def after_step(context, step):
    if step.status == "failed":
        attach_screenshot(context, context.browser, name="failure.png")
        attach_text(context, str(step.exception), name="error.txt")
        log(f"URL at failure: {context.browser.current_url}")
```

The helpers also work with Playwright, Selenium, PIL images, bytes, files, and JSON data.

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
   models.py  ── pure dataclasses
                (Execution → Feature → Rule-aware Scenario → Step)
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

## License

[MIT](LICENSE) © Mathias Paulenko
