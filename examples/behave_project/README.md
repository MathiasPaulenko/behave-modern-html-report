# Behave Project Example

A functional Behave project used to test `behave-modern-html-report`.

## Features

- **Login**: background, scenario outline, skipped/undefined steps.
- **Checkout**: Gherkin `Rule` grouping, background, passing and failing scenarios.
- **Reporting**: skipped scenario, slow scenario, attachment on failure.

## Requirements

Install the dependencies from this directory:

```bash
pip install -r requirements.txt
```

This installs `behave` and the reporter in editable mode (`-e ../..`).

## Run

From this directory:

```bash
behave
```

This uses `behave.ini` and generates `report.html` with the modern formatter.

## View report

Open `report.html` in a browser.

## Report customization

The example `behave.ini` configures a few reporter options through `userdata`:

```ini
[behave.userdata]
bmr.title = Behave Project Example
bmr.company = Open Source
bmr.theme = auto
bmr.default_view = dashboard
bmr.show_copy_command = true
bmr.show_environment_vars = true
```

Note: `bmr.*` options must be set in `behave.ini` (or `-D` on the command
line). The formatter reads `userdata` when it is instantiated, which happens
before `before_all` runs — overriding them from `environment.py` has no
effect on the report.

See the main [Configuration](../../README.md#configuration) docs for the full list of options.

## Step catalog

Generate a static catalog of all step definitions:

```bash
behave -f steps-catalog -o steps.html --dry-run
```

Open `steps.html` to see all `@given`, `@when`, `@then` steps with patterns,
parameters, source code and metrics.

See the main [README](../../README.md#step-catalog) for more information.

## Advanced

Run a subset of features:

```bash
behave --tags=login
behave --tags=checkout
behave --tags=smoke
```

Run without installing the package (from the repo root):

```bash
PYTHONPATH=. python -m behave -f behave_modern_html_report.formatter:ModernHTMLFormatter -o report.html examples/behave_project/features
```
