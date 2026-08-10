# Contributing

Thanks for your interest in making **Behave Modern HTML Report** better!

## Local setup

```bash
git clone https://github.com/MathiasPaulenko/behave-modern-html-report.git
cd behave-modern-html-report
python -m venv .venv
. .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -e .
```

Or use the provided `Makefile`:

```bash
make install-dev
```

## Running checks

```bash
make test
make lint
```

Equivalently:

```bash
python -m pytest -ra
python -m ruff check .
python -m black --check .
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

## Iterating on the UI

The fastest loop is to regenerate the demo report and reload it:

```bash
python examples/demo_generator/generate_demo.py
```

Open `examples/demo_generator/demo-report.html` in your browser and refresh
after each change.

## Project conventions

- Python 3.11+, type hints everywhere, Google-style docstrings.
- Dataclasses for models (no Pydantic dependency).
- No external CSS/JS — everything must be embeddable.
- No frameworks in the frontend (no React/Vue/Bootstrap/jQuery).
- Keep layers separated: formatter ↔ collector ↔ models ↔ renderer.

## Adding a new chart

1. Add a helper to `behave_modern_html_report/assets/js/charts.js` (small
   Canvas API).
2. Add a `<canvas>` to the relevant template component.
3. Wire it up inside `renderCharts()` in `assets/js/report.js`.

## Adding a new model field

1. Add the field to the dataclass in `models.py`.
2. Populate it in `collector.py`.
3. Surface it in the template that needs it.
4. Add a unit test.

## Pull request process

1. Fork the repository and create a branch from `main`.
2. Write tests for your changes.
3. Ensure `pytest`, `ruff check .`, and `black --check .` all pass.
4. Update documentation if your change affects the public API or user-facing
   behaviour.
5. Open a pull request using the provided template.
6. Reference any related issues in your PR description (e.g. `Closes #123`).

## Reporting issues

Use the provided issue templates to report bugs or request features. Include
as much context as possible: Python version, Behave version, OS, and a
minimal reproduction case.
