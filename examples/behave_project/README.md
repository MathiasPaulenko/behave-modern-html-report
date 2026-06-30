# Behave Project Example

A functional Behave project used to test `behave-modern-html-report`.

## Features

- **Login**: background, scenario outline, pending/undefined steps.
- **Checkout**: Gherkin `Rule` grouping, background, passing and failing scenarios.
- **Reporting**: skipped/pending scenario, slow scenario, attachment on failure.

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

You can also override them from `environment.py`:

```python
def before_all(context):
    context.config.userdata.set("bmr.title", "My Custom Title")
    context.config.userdata.set("bmr.link_to_ci", "https://ci.example.com/build/123")
```

See the main [Configuration](../../docs/configuration.md) docs for the full list of options.

## Step catalog

Generate a static catalog of all step definitions:

```bash
behave -f steps -o steps.html
```

Open `steps.html` to see all `@given`, `@when`, `@then` steps with patterns,
parameters, source code and metrics.

See the main [Usage](../../docs/usage.md) docs for more information.

## Advanced

Run a subset of features:

```bash
behave --tags=login
behave --tags=checkout
behave --tags=smoke
```

Run without installing the package (from the repo root):

```bash
PYTHONPATH=. python -m behave examples/behave_project/features
```
