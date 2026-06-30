# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-06-30

### Added

- **Step catalog formatter** (`-f steps`): statically analyses `features/steps/` and produces an HTML catalog of all step definitions without running the suite.
- New `step_scanner` module that uses `ast` to find `@given`, `@when`, `@then`, `@step` decorators.
- Extracts pattern, function name, file path, line number, parameters, docstring and source code per step.
- Catalog HTML with searchable/sortable table, keyword filters, metrics view and detail panel.
- New `bmr.steps_dir` userdata option to customise the steps directory.
- `StepCatalogFormatter`, `StepCatalog`, `scan_directory`, `scan_file` added to public API.
- 13 new tests covering the scanner, catalog metrics and HTML rendering.
- Updated `docs/usage.md`, `docs/configuration.md`, `README.md` and example project.

### Fixed

- Step catalog HTML layout: removed `.layout` wrapper that broke `body{display:grid}` from `report.css`.

## [2.1.0] - 2026-06-29

### Added

- New report customization options via `behave.userdata`:
  - `bmr.favicon`, `bmr.primary_color`, `bmr.accent_color`.
  - `bmr.default_view`, `bmr.hidden_views`, `bmr.expand_by_default`.
  - `bmr.max_slowest`, `bmr.show_copy_command`, `bmr.show_environment_vars`.
  - `bmr.footer_text`, `bmr.link_to_ci`.
- `View in CI` button in the header when `bmr.link_to_ci` is set.
- Custom footer text support.
- Option to hide the environment variables card.
- Option to hide the copy reproduce command button on scenarios.
- Programmatic color override via CSS custom properties.

### Changed

- Updated README, `docs/configuration.md`, `docs/views.md`, `docs/examples.md` and the example project README to document the new options.
- Demo generator now uses `default_view`, `footer_text`, `show_copy_command` and `show_environment_vars`.
- Regenerated demo report and screenshots.

## [2.0.0] - 2026-06-29

### Added

- Full **Background** and **Scenario Outline** support with `Examples` tables.
- **Gherkin Rules** support (requires Behave 1.3.x): scenarios under a `Rule` are grouped correctly.
- **Compact / Detailed** view modes for Features, Rules, and Scenarios with `localStorage` persistence.
- New top-level **Results** view showing a compact table of all scenarios.
- Expanded **Environment** section with user, CPU, memory, git branch/commit/remote, and selected env vars.
- New **Statistics** raw-metrics view: status distribution, duration percentiles, per-feature summary, and error distribution.
- Functional **Behave example project** under `examples/behave_project/` with features, steps, hooks, and `behave.ini`.
- New documentation pages under `docs/`: usage, configuration, views, examples, architecture, contributing.
- Screenshots of every report view embedded in the README.
- Contributor setup files: `requirements.txt`, `requirements-dev.txt`, `Makefile`, `.editorconfig`, `.pre-commit-config.yaml`.

### Changed

- Tags view now relies solely on the table for pass rate information; the chart was removed.
- Demo generator moved to `examples/demo_generator/`.
- Obsolete `examples/features/` and `examples/behave.ini` removed.
- Pass rate bars in tables now have color-coded fills (low/medium/high).

### Removed

- Redundant Tag pass rate chart from the Tags view.
- Duplicated charts from the Statistics view in favor of raw data tables.

## [0.2.0] - 2026-06-28

### Added

- New **Tags** page with per-tag scenario counts, pass rate, duration, and a pass-rate chart.
- `behave_modern_html_report.attach` helper API: `attach_screenshot`, `attach_file`, `attach_text`, `attach_json`, `log` for easy `environment.py` integration.
- **JSON sidecar output** (`bmr.json_sidecar = true`) writes `report.json` next to the HTML report.
- Inline step duration bar showing each step's relative cost within the scenario.
- Copy-reproduce-command button on every scenario (`behave features/example.feature:3`).

### Changed

- Promoted PyPI classifier from `Beta` to `Production/Stable`.
- README badges now point to PyPI and CI.

## [0.1.0] - 2026-06-28

### Added

- Initial release of **Behave Modern Report**.
- Layered architecture: `formatter`, `collector`, `models`, `statistics`, `renderer`, `assets`.
- Single-file, fully offline HTML report.
- Dark / Light / Auto themes.
- Dashboard with execution summary and environment metadata.
- Interactive Chart.js statistics (status pie, duration bar, slowest scenarios).
- Sidebar navigation: Dashboard, Features, Scenarios, Statistics, Environment.
- Client-side instant search and multi-criteria filtering.
- Expandable features, scenarios and steps with rich metadata.
- Modern error viewer with copy-to-clipboard.
- Attachment support (images, text, JSON, etc.) with lightbox gallery.
- Configurable title, company, logo, custom CSS/JS.
- Accessibility: keyboard navigation, ARIA labels, high-contrast palette.
- GitHub Actions CI workflow (ruff + pytest).
