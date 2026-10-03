# Behave Modern HTML Report

> The modern, beautiful, single-file HTML report formatter for [Behave](https://behave.readthedocs.io/).
> Dark mode, charts, instant search, attachments, zero external requests.

[![PyPI](https://img.shields.io/pypi/v/behave-modern-html-report.svg)](https://pypi.org/project/behave-modern-html-report/)
[![Python](https://img.shields.io/pypi/pyversions/behave-modern-html-report.svg)](https://pypi.org/project/behave-modern-html-report/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/MathiasPaulenko/behave-modern-html-report/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-modern-html-report/actions/workflows/ci.yml)

`behave-modern-html-report` is a drop-in formatter for Behave that produces a single,
self-contained HTML file — everything (CSS, JS, icons, attachments) is
embedded so the report works offline, on any machine, forever.

## Features

- 🌓 **Dark / Light / Auto** themes, modern Material-3 inspired UI
- 📊 **Interactive charts** (status pie, duration histogram, slowest scenarios, tag pass rate, timeline) — pure vanilla JS, no Chart.js CDN
- 🏷️ **Tag analytics** page: per-tag counts, pass rate, duration, and a dedicated chart
- 📋 **Gherkin Rules** support: scenarios under a `Rule` are grouped and tagged correctly (Behave 1.3.x)
- 🔍 **Instant client-side search** across features, scenarios, steps and tags
- 🎚️ **Filter by status** with one click
- 📁 **Expandable** features → scenarios → steps with rich metadata
- 🧯 **Modern error viewer** with copy-to-clipboard tracebacks
- 🖼️ **Attachments**: images (with lightbox), JSON, text, binaries
- 🚀 **Copy-reproduce-command** per scenario (`behave "features/example.feature:3"`)
- 📊 **Inline step duration bars** to spot slow steps at a glance
- ♿ **Accessible**: keyboard navigation, ARIA labels, reduced-motion support
- 📦 **Single HTML file**, works offline, no web server, no CDN
- 📌 **Fixed sidebar** navigation that stays in place while content scrolls
- 🧩 **Clean architecture** — formatter / collector / models / renderer separation, fully testable
- 🛠️ **Extensible** — custom CSS/JS, custom title/logo/company, JSON sidecar, future plugin system
- 📋 **Step catalog** — static analysis formatter that extracts all step definitions with patterns, params, source and metrics

## Installation

```bash
pip install behave-modern-html-report
```

## Quick start

In your project's `behave.ini` (or `setup.cfg` / `tox.ini` with the same section):

```ini
[behave.formatters]
modern-html = behave_modern_html_report.formatter:ModernHTMLFormatter
steps-catalog = behave_modern_html_report.step_catalog_formatter:StepCatalogFormatter
```

Then run:

```bash
behave -f modern-html -o report.html
```

Open `report.html` in any browser. Done.

### Useful variations

Run a single feature file:

```bash
behave -f modern-html -o report.html features/login.feature
```

Keep the console output while generating the report (Behave supports multiple
formatters at once):

```bash
behave -f pretty -o /dev/null -f modern-html -o report.html
```

On Windows use `NUL` instead of `/dev/null`.

## Configuration

All reporter options are read from `behave`'s `userdata` section. Set them in `behave.ini`, `setup.cfg`, or via `-D` on the command line:

```ini
[behave.userdata]
bmr.title         = My Awesome Suite
bmr.company       = Acme Inc.
bmr.logo          = https://example.com/logo.svg
bmr.favicon       = https://example.com/favicon.ico
bmr.theme         = auto          ; auto | dark | light
bmr.primary_color = #3b82f6
bmr.accent_color  = #22c55e
bmr.default_view  = dashboard     ; dashboard | features | scenarios | ...
bmr.hidden_views    = rules,statistics
bmr.expand_by_default = false
bmr.max_slowest   = 10
bmr.show_copy_command = true
bmr.show_environment_vars = true
bmr.footer_text   = Build #12345
bmr.link_to_ci    = https://ci.example.com/build/12345
bmr.json_sidecar  = true          ; writes report.json next to report.html
bmr.custom_css    = path/to/extra.css
bmr.custom_js     = path/to/extra.js
```

Available options:

- `bmr.title` — report title (default `Behave Modern Report`).
- `bmr.company` — company name shown under the title.
- `bmr.logo` / `bmr.favicon` — URL or base64 data URI for a logo/favicon.
- `bmr.theme` — `auto`, `dark` or `light`.
- `bmr.primary_color` / `bmr.accent_color` — override the report colors.
- `bmr.default_view` — initial view (`dashboard`, `features`, `rules`, `scenarios`, `results`, `tags`, `statistics`, `environment`).
- `bmr.hidden_views` — comma-separated views to hide (e.g. `rules,statistics`).
- `bmr.expand_by_default` — expand all features, rules and scenarios on load (default `false`).
- `bmr.max_slowest` — number of slowest scenarios on the dashboard (default `10`).
- `bmr.show_copy_command` — show the copy reproduce command button (default `true`).
- `bmr.show_environment_vars` — show the environment variables card (default `true`).
- `bmr.footer_text` — custom footer line.
- `bmr.link_to_ci` — "View in CI" button URL.
- `bmr.json_sidecar` — write `report.json` next to the HTML report (default `false`).
- `bmr.custom_css` / `bmr.custom_js` — embed custom CSS/JS files (paths must be readable from where Behave runs).
- `bmr.steps_dir` — directory to scan for step definitions when using the `steps-catalog` formatter (default `features/steps`).

Note: `bmr.*` options must be set in `behave.ini` or via `-D` — setting them from
`environment.py` has no effect, because the formatter reads `userdata` when it
is instantiated, before `before_all` runs.

### Setting options from the command line

Use `-D` / `--define` to override any option without touching `behave.ini`:

```bash
behave -f modern-html -o report.html -D bmr.title="API Tests" -D bmr.theme=dark
```

### Full example `behave.ini`

```ini
[behave]
format = modern-html
outfiles = report.html
show_skipped = true
show_timings = true

[behave.formatters]
modern-html = behave_modern_html_report.formatter:ModernHTMLFormatter

[behave.userdata]
bmr.title = My Suite
bmr.company = Acme Inc.
bmr.theme = auto
bmr.json_sidecar = true
```

### Environment variables and secrets

The Environment view captures CI-related environment variables (prefixed `CI`,
`GITHUB`, `GITLAB`, `BITBUCKET`, `JENKINS`, `TRAVIS`, `CIRCLE`, `BUILD`,
`AGENT`, `TF_`, `AZURE`, plus `PATH`, `HOME`, `USER`, `SHELL`, `LANG` and
`TERM`). Names containing `TOKEN`, `SECRET`, `PASSWORD`, `PASSWD`,
`CREDENTIAL`, `PRIVATE`, `AUTH`, `COOKIE`, `CERT`, `APIKEY`, `API_KEY` or
`_KEY` are automatically redacted as `***` so secrets are never embedded into
the report.

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
        log(context, f"URL at failure: {context.browser.current_url}")
```

The helpers also work with Playwright, Selenium, PIL images, bytes, files, and JSON data.
Behave's native `context.attach(mime_type, data)` is captured too, via the
formatter's `embedding()` hook.

> Reminder: `environment.py` hooks must live inside `features/` (Behave only
> loads `features/environment.py`), not at the project root.

## Step Catalog

The package also includes a **step catalog** formatter that statically analyses
your `features/steps/` directory and produces an HTML catalog of all step
definitions. Behave still executes the suite normally (the catalog ignores the
test events) — add `--dry-run` if you only want the catalog.

Register it in `behave.ini`:

```ini
[behave.formatters]
steps-catalog = behave_modern_html_report.step_catalog_formatter:StepCatalogFormatter
```

Then run:

```bash
behave -f steps-catalog -o steps.html --dry-run
```

The catalog includes:

- All `@given`, `@when`, `@then` and `@step` decorated functions.
- Step pattern, function name, file path and line number.
- Extracted parameters from `{placeholder}` patterns.
- Function docstrings and source code snippets.
- Metrics: total steps, by keyword, by file, parameterised, documented, regex.
- Searchable, sortable table with keyword filters.
- Detail panel showing the full source code of each step.

You can customise the steps directory with `bmr.steps_dir`:

```ini
[behave.userdata]
bmr.steps_dir = features/steps
```

### Programmatic usage

```python
from behave_modern_html_report import scan_directory
from behave_modern_html_report.step_catalog_formatter import render_catalog
from pathlib import Path

catalog = scan_directory(Path("features/steps"))
html = render_catalog(catalog, title="My Step Catalog")
Path("steps.html").write_text(html, encoding="utf-8")
```

## Report views

The generated report is a single-page application with a sidebar navigation.
Change the initial view with `bmr.default_view` and hide views with
`bmr.hidden_views`.

- **Dashboard** — high-level summary: totals, pass rate, status distribution,
  duration histogram, slowest scenarios, tag pass rate, error distribution, and
  a one-click summary for Slack or chat.
- **Features** — all features with status badges, tags, description and
  duration. Expand a feature to see its scenarios; Compact/Detailed toggle
  shows or hides rule and scenario details.
- **Rules** — all Gherkin `Rule` groups across every feature (Behave 1.3.x).
- **Scenarios** — all scenarios as collapsible cards with steps, background
  steps, attachments, error traces and scenario outline banners.
- **Results** — compact table of every scenario with status, feature, rule,
  duration and tags.
- **Tags** — per-tag analytics: scenario count, pass rate with colour bars and
  accumulated duration.
- **Statistics** — raw metrics: status distribution, duration percentiles,
  per-feature summary and error distribution by exception type.
- **Environment** — host and runtime info captured at execution time: Python
  and Behave versions, platform, hostname, CPU, memory, git data, and CI
  environment variables (with secret redaction).

## Examples

The repository includes two example projects under `examples/`.

### Demo generator

`examples/demo_generator/` builds a synthetic execution and renders it as HTML —
useful for previews, screenshots and design iteration without a real suite:

```bash
python examples/demo_generator/generate_demo.py
```

Output: `examples/demo_generator/demo-report.html`.

### Functional Behave project

`examples/behave_project/` is a complete Behave project with features, steps,
`environment.py` hooks, and `behave.ini` configured for the formatter:

```bash
cd examples/behave_project
pip install -r requirements.txt   # installs behave + this package (-e ../..)
behave                            # generates report.html
```

It exercises: backgrounds and scenario outlines, Gherkin `Rule` groups,
passing/failing/skipped/undefined scenarios, attachments on failure, slow
scenarios, and custom `bmr.*` userdata options. Run a subset with
`behave --tags=login|checkout|smoke`.

## Report screenshots

<details>
<summary>Report views (click to expand)</summary>

### Dashboard view

![Dashboard](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/dashboard.png)

### Features view

![Features](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/features.png)

### Rules view

![Rules](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/rules.png)

### Scenarios view

![Scenarios](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/scenarios.png)

### Results view

![Results](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/results.png)

### Tags view

![Tags](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/tags.png)

### Statistics view

![Statistics](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/statistics.png)

### Environment view

![Environment](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/environment.png)

</details>

<details>
<summary>Step catalog</summary>

![Step Catalog](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/step_catalog.png)

![Step detail panel](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/step_catalog_detail.png)

![Step metrics](https://raw.githubusercontent.com/MathiasPaulenko/behave-modern-html-report/main/.github/images/step_catalog_metrics.png)

</details>

## Architecture

`behave-modern-html-report` follows a strict layered architecture — each layer
has a single responsibility and depends only on the layers above it:

```text
┌──────────────────────────────────────────┐
│  formatter.py   (Behave adapter)         │  ← only this layer knows about Behave
├──────────────────────────────────────────┤
│  collector.py   (event → model builder)  │
├──────────────────────────────────────────┤
│  models.py      (pure dataclasses)       │  ← no I/O, no framework imports
│  statistics.py  (aggregations)           │
├──────────────────────────────────────────┤
│  renderer.py    (Jinja2 → single HTML)   │
│  assets.py      (CSS/JS bundling)        │
│  templates/     (HTML components)        │
│  assets/        (CSS / JS / icons)       │
└──────────────────────────────────────────┘
```

Data flow:

1. Behave invokes the formatter for each feature/scenario/step result.
2. The formatter delegates to a `Collector`, which builds an `Execution` tree
   of dataclasses.
3. On `close()`, the formatter calls `Collector.finalize()` which runs
   `statistics.compute()` to derive aggregates.
4. A `Renderer` loads Jinja2 templates and the bundled CSS/JS, embeds
   everything (and the execution as JSON for client-side rendering), and writes
   a single `.html` file.

Why it matters:

- **Testability** — the collector accepts duck-typed stubs; the renderer
  accepts an `Execution`, so both can be tested without ever running Behave.
- **Reusability** — anything that can build an `Execution` (e.g. a JSON loader)
  can render the same report.
- **Future-proofing** — new outputs or plugins only touch one layer.

The renderer never references external URLs: CSS, JS, icons (inline SVG
sprite), attachments (base64) and the execution payload are all embedded. The
output file works offline forever.

## Development

```bash
git clone https://github.com/MathiasPaulenko/behave-modern-html-report.git
cd behave-modern-html-report
python -m venv .venv
. .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
ruff check .
```

Or use the `Makefile`: `make install-dev`, `make test`, `make lint`,
`make format`, `make demo`, `make report`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full process, conventions and
release steps, and [SECURITY.md](SECURITY.md) for the security policy.

## License

[MIT](LICENSE) © Mathias Paulenko
