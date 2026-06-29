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
