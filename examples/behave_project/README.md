# Behave Project Example

A functional Behave project used to test `behave-modern-html-report`.

## Features

- **Login**: background, scenario outline, pending/undefined steps.
- **Checkout**: background, passing and failing scenarios.
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
