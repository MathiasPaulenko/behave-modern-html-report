# Usage

## Installation

```bash
pip install behave-modern-html-report
```

## Basic configuration

Register the formatter in your `behave.ini`:

```ini
[behave.formatters]
modern = behave_modern_html_report.formatter:ModernHTMLFormatter
```

Then run Behave as usual:

```bash
behave -f modern -o report.html
```

You can also use it via `setup.cfg` or `tox.ini` with the same `[behave.formatters]` section.

## Using a single feature file

```bash
behave -f modern -o report.html features/login.feature
```

## Combining with other formatters

Behave supports multiple formatters at once. For example, keep the console
output while generating the HTML report:

```bash
behave -f pretty -o /dev/null -f modern -o report.html
```

On Windows use `NUL` instead of `/dev/null`.

## Generating a demo report

If you want to see the report without a real Behave suite, use the demo
generator:

```bash
python examples/demo_generator/generate_demo.py
```

This writes `examples/demo_generator/demo-report.html` with a realistic-looking
execution and opens it in the default browser.

## Step catalog formatter

The package also includes a **step catalog** formatter that statically analyses
your `features/steps/` directory and produces an HTML catalog of all step
definitions — without running the suite.

Register it in `behave.ini`:

```ini
[behave.formatters]
steps = behave_modern_html_report.step_catalog_formatter:StepCatalogFormatter
```

Then run:

```bash
behave -f steps -o steps.html
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

You can also use the scanner directly without Behave:

```python
from behave_modern_html_report import scan_directory
from behave_modern_html_report.step_catalog_formatter import render_catalog
from pathlib import Path

catalog = scan_directory(Path("features/steps"))
html = render_catalog(catalog, title="My Step Catalog")
Path("steps.html").write_text(html, encoding="utf-8")
```
