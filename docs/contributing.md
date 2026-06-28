# Contributing

Thanks for your interest in making **Behave Modern Report** better!

## Local setup

```bash
git clone https://github.com/MathiasPaulenko/behave-modern-report.git
cd behave-modern-report
python -m venv .venv
. .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Releasing

Releases are **fully automatic**. To cut a new version:

1. Bump the `version` field in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Commit and push to `main`.

The `Release` GitHub Actions workflow detects the version bump, creates the
matching `vX.Y.Z` tag, builds the distribution, publishes to PyPI via
Trusted Publishing, and creates a GitHub Release with auto-generated notes.

If the version was not changed, the workflow exits cleanly without releasing.

## Running checks

```bash
pytest -ra
ruff check .
black --check .
```

## Iterating on the UI

The fastest loop is to regenerate the demo report and reload it:

```bash
python examples/generate_demo.py
```

Open `examples/demo-report.html` in your browser and refresh after each change.

## Project conventions

- Python 3.11+, type hints everywhere, Google-style docstrings.
- Dataclasses for models (no Pydantic dependency).
- No external CSS/JS — everything must be embeddable.
- No frameworks in the frontend (no React/Vue/Bootstrap/jQuery).
- Keep layers separated: formatter ↔ collector ↔ models ↔ renderer.

## Adding a new chart

1. Add a helper to `behave_modern_report/assets/js/charts.js` (small Canvas API).
2. Add a `<canvas>` to the relevant template component.
3. Wire it up inside `renderCharts()` in `assets/js/report.js`.

## Adding a new model field

1. Add the field to the dataclass in `models.py`.
2. Populate it in `collector.py`.
3. Surface it in the template that needs it.
4. Add a unit test.
