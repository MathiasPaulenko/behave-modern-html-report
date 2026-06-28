# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-28

### Added

- New **Tags** page with per-tag scenario counts, pass rate, duration, and a pass-rate chart.
- `behave_modern_report.attach` helper API: `attach_screenshot`, `attach_file`, `attach_text`, `attach_json`, `log` for easy `environment.py` integration.
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
