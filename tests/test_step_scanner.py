"""Tests for the step scanner and catalog formatter."""

from __future__ import annotations

import textwrap
from pathlib import Path

from behave_modern_html_report.step_catalog_formatter import render_catalog
from behave_modern_html_report.step_scanner import StepCatalog, scan_directory, scan_file

_STEPS_SOURCE = textwrap.dedent('''
    from behave import given, then, when, step

    @given('the database is reset')
    def step_reset_db(context):
        context.database = {}

    @given('the username is "{username}"')
    def step_set_username(context, username):
        context.username = username

    @when('the user logs in')
    def step_login(context):
        pass

    @then('an error is shown')
    def step_error(context):
        """Assert that an error message is visible."""
        assert True

    @step('a generic step')
    def step_generic(context):
        pass
''').strip()


def test_scan_file_finds_all_decorators(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    keywords = sorted(d.keyword for d in defs)
    assert keywords == ["given", "given", "step", "then", "when"]


def test_scan_file_extracts_patterns(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    patterns = {d.func_name: d.pattern for d in defs}
    assert patterns["step_reset_db"] == "the database is reset"
    assert patterns["step_set_username"] == 'the username is "{username}"'
    assert patterns["step_login"] == "the user logs in"


def test_scan_file_extracts_params(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    by_name = {d.func_name: d for d in defs}
    assert by_name["step_set_username"].params == ["username"]
    assert by_name["step_reset_db"].params == []


def test_scan_file_extracts_docstring(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    by_name = {d.func_name: d for d in defs}
    assert "error message" in by_name["step_error"].docstring
    assert by_name["step_reset_db"].docstring == ""


def test_scan_file_extracts_source(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    by_name = {d.func_name: d for d in defs}
    assert "def step_reset_db" in by_name["step_reset_db"].source
    assert "context.database" in by_name["step_reset_db"].source


def test_scan_file_extracts_location(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    by_name = {d.func_name: d for d in defs}
    assert by_name["step_reset_db"].file_path == "steps.py"
    assert by_name["step_reset_db"].line > 0


def test_scan_directory_aggregates(tmp_path: Path) -> None:
    steps_dir = tmp_path / "steps"
    steps_dir.mkdir()
    (steps_dir / "login.py").write_text(_STEPS_SOURCE, encoding="utf-8")
    (steps_dir / "checkout.py").write_text(
        'from behave import given\n@given("a cart exists")\ndef step_cart(context):\n    pass\n',
        encoding="utf-8",
    )
    catalog = scan_directory(steps_dir)
    assert catalog.total == 6
    assert catalog.by_keyword.get("given", 0) == 3
    assert len(catalog.by_file) == 2


def test_scan_directory_skips_dunder_files(tmp_path: Path) -> None:
    steps_dir = tmp_path / "steps"
    steps_dir.mkdir()
    (steps_dir / "__init__.py").write_text(
        'from behave import given\n@given("hidden")\ndef step_hidden(context):\n    pass\n',
        encoding="utf-8",
    )
    (steps_dir / "real.py").write_text(
        'from behave import given\n@given("visible")\ndef step_visible(context):\n    pass\n',
        encoding="utf-8",
    )
    catalog = scan_directory(steps_dir)
    assert catalog.total == 1
    assert catalog.steps[0].func_name == "step_visible"


def test_catalog_metrics(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    catalog = StepCatalog(steps=defs)
    assert catalog.total == 5
    assert catalog.with_params == 1
    assert catalog.with_docstring == 1
    assert catalog.regex_steps == 0


def test_render_catalog_produces_valid_html(tmp_path: Path) -> None:
    f = tmp_path / "steps.py"
    f.write_text(_STEPS_SOURCE, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    catalog = StepCatalog(steps=defs)
    html = render_catalog(catalog, title="Test Catalog")
    assert "<!doctype html>" in html
    assert "Test Catalog" in html
    assert "step_reset_db" in html
    assert "the database is reset" in html


def test_render_catalog_empty_catalog() -> None:
    catalog = StepCatalog(steps=[])
    html = render_catalog(catalog, title="Empty")
    assert "<!doctype html>" in html
    assert "No step definitions found" in html


def test_scan_file_handles_syntax_error(tmp_path: Path) -> None:
    f = tmp_path / "bad.py"
    f.write_text("def broken(:\n", encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    assert defs == []


def test_scan_file_handles_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "empty.py"
    f.write_text("", encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    assert defs == []
