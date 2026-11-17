"""Regression tests for bugs discovered during the complete audit."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from behave_modern_html_report import statistics as stats_mod
from behave_modern_html_report.formatter import ModernHTMLFormatter, _read_optional
from behave_modern_html_report.models import (
    Attachment,
    Execution,
    Feature,
    Scenario,
    Statistics,
    Step,
)
from behave_modern_html_report.renderer import Renderer, RenderOptions
from behave_modern_html_report.step_catalog_formatter import StepCatalogFormatter
from behave_modern_html_report.step_scanner import scan_file
from behave_modern_html_report.utils import format_duration

# ---------------------------------------------------------------------------
# BUG 1: Version mismatch between __init__.py and pyproject.toml
# ---------------------------------------------------------------------------


def test_version_matches_pyproject():
    """__version__ in __init__.py must match version in pyproject.toml."""
    import behave_modern_html_report as bmr

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    from pathlib import Path

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert bmr.__version__ == data["project"]["version"]


# ---------------------------------------------------------------------------
# BUG 2 & 3: Formatter class name attributes must match entry point names
# ---------------------------------------------------------------------------


def test_formatter_name_matches_entry_point():
    """ModernHTMLFormatter.name must be 'modern-html' to match the entry point."""
    assert ModernHTMLFormatter.name == "modern-html"


def test_step_catalog_formatter_name_matches_entry_point():
    """StepCatalogFormatter.name must be 'steps-catalog' to match the entry point."""
    assert StepCatalogFormatter.name == "steps-catalog"


# ---------------------------------------------------------------------------
# BUG 4: _derive_feature_status returns order-dependent status for mixed
#         non-failed scenarios (e.g. [skipped, passed] -> "skipped")
# ---------------------------------------------------------------------------


def test_derive_feature_status_passed_with_mixed_passed_skipped():
    """A feature with both passed and skipped scenarios should be 'passed'."""
    feature = Feature(
        name="F",
        scenarios=[
            Scenario(name="S1", status="skipped"),
            Scenario(name="S2", status="passed"),
        ],
    )
    execution = Execution(features=[feature], statistics=Statistics())
    stats_mod.compute(execution)
    assert feature.status == "passed"


def test_derive_feature_status_passed_order_independent():
    """Feature status should not depend on scenario ordering."""
    feature_a = Feature(
        name="F",
        scenarios=[
            Scenario(name="S1", status="skipped"),
            Scenario(name="S2", status="passed"),
        ],
    )
    feature_b = Feature(
        name="F",
        scenarios=[
            Scenario(name="S1", status="passed"),
            Scenario(name="S2", status="skipped"),
        ],
    )
    exec_a = Execution(features=[feature_a], statistics=Statistics())
    exec_b = Execution(features=[feature_b], statistics=Statistics())
    stats_mod.compute(exec_a)
    stats_mod.compute(exec_b)
    assert feature_a.status == feature_b.status == "passed"


# ---------------------------------------------------------------------------
# BUG 5: Execution.overall_status returns STATUS_UNTESTED for mixed
#         passed+skipped features (should be "passed")
# ---------------------------------------------------------------------------


def test_overall_status_passed_with_mixed_passed_skipped():
    """Overall status should be 'passed' when some features pass and others skip."""
    execution = Execution(
        features=[
            Feature(name="F1", status="passed"),
            Feature(name="F2", status="skipped"),
        ],
    )
    assert execution.overall_status == "passed"


# ---------------------------------------------------------------------------
# BUG 6: _read_optional doesn't catch UnicodeDecodeError
# ---------------------------------------------------------------------------


def test_read_optional_handles_non_utf8_file(tmp_path):
    """_read_optional should return empty string for non-UTF-8 files."""
    p = tmp_path / "bad.css"
    p.write_bytes(b"\xff\xfe\x00invalid")
    assert _read_optional(str(p)) == ""


# ---------------------------------------------------------------------------
# BUG 7: StepCatalogFormatter.close() doesn't create parent directories
# ---------------------------------------------------------------------------


def test_step_catalog_formatter_creates_parent_dirs(tmp_path):
    """StepCatalogFormatter should create parent directories for output."""
    from behave_modern_html_report.step_catalog_formatter import StepCatalogFormatter

    steps_dir = tmp_path / "steps"
    steps_dir.mkdir()
    (steps_dir / "steps.py").write_text(
        'from behave import given\n@given("a step")\ndef step_impl(context):\n    pass\n',
        encoding="utf-8",
    )

    output_path = tmp_path / "deep" / "nested" / "output.html"

    class _MockStream:
        def __init__(self):
            self.content = ""

        def write(self, data):
            self.content = data

        def close(self):
            pass

    mock_stream = _MockStream()

    class _MockStreamOpener:
        def __init__(self, name):
            self.name = name
            self.stream = mock_stream

        def open(self):
            return mock_stream

    stream_opener = _MockStreamOpener(str(output_path))
    config = SimpleNamespace(
        base_dir=str(tmp_path),
        userdata={"bmr.steps_dir": "steps"},
    )

    formatter = StepCatalogFormatter(stream_opener, config)
    formatter.close()
    assert output_path.parent.exists()
    assert "<!doctype html>" in output_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# BUG 12: _extract_pattern can return non-string pattern for re.compile(42)
# ---------------------------------------------------------------------------


def test_scan_file_non_string_regex_pattern(tmp_path):
    """scan_file should handle non-string regex arguments gracefully."""
    source = (
        "import re\n"
        "from behave import given\n"
        "@given(re.compile(42))\n"
        "def step_impl(context):\n"
        "    pass\n"
    )
    f = tmp_path / "steps.py"
    f.write_text(source, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    assert len(defs) == 1
    assert isinstance(defs[0].pattern, str)


# ---------------------------------------------------------------------------
# BUG 13: format_duration doesn't handle negative values
# ---------------------------------------------------------------------------


def test_format_duration_negative():
    """format_duration should return '0ms' for negative values."""
    assert format_duration(-1.0) == "0ms"
    assert format_duration(-0.001) == "0ms"


# ---------------------------------------------------------------------------
# BUG 14: socket.gethostname() not in try/except
# ---------------------------------------------------------------------------


def test_collector_hostname_safe_on_failure(monkeypatch):
    """Collector should handle socket.gethostname() failure gracefully."""
    import socket

    from behave_modern_html_report.collector import Collector

    def raise_hostname_error():
        raise OSError("hostname unavailable")

    monkeypatch.setattr(socket, "gethostname", raise_hostname_error)
    collector = Collector()
    assert collector.execution.environment.hostname == ""


# ---------------------------------------------------------------------------
# BUG 16: step_scanner.py only checks ast.FunctionDef, missing
#         ast.AsyncFunctionDef for async step definitions
# ---------------------------------------------------------------------------


def test_scan_file_finds_async_step_definitions(tmp_path):
    """scan_file should detect async step definitions (AsyncFunctionDef)."""
    source = (
        "from behave import given, when, then\n"
        "@given('an async setup')\n"
        "async def step_async_setup(context):\n"
        "    pass\n"
        "@when('an async action runs')\n"
        "async def step_async_action(context):\n"
        "    pass\n"
    )
    f = tmp_path / "async_steps.py"
    f.write_text(source, encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path)
    assert len(defs) == 2
    func_names = {d.func_name for d in defs}
    assert "step_async_setup" in func_names
    assert "step_async_action" in func_names


# ---------------------------------------------------------------------------
# BUG 17: STATUS_XFAILED (expected failure) incorrectly included in
#         _FAILED_STATUSES, causing expected failures to be counted as
#         actual failures in statistics and feature status derivation
# ---------------------------------------------------------------------------


def test_xfailed_not_treated_as_failure():
    """xfailed (expected failure) should not be counted as a failure."""
    from behave_modern_html_report.models import STATUS_XFAILED

    feature = Feature(
        name="F",
        scenarios=[Scenario(name="S1", status=STATUS_XFAILED)],
    )
    execution = Execution(features=[feature], statistics=Statistics())
    stats_mod.compute(execution)
    assert feature.status != "failed"
    assert stats_mod.compute(execution).error_count == 0


def test_xfailed_does_not_make_feature_failed():
    """A feature with only xfailed scenarios should not be marked as failed."""
    from behave_modern_html_report.models import STATUS_XFAILED

    feature = Feature(
        name="F",
        scenarios=[
            Scenario(name="S1", status=STATUS_XFAILED),
            Scenario(name="S2", status=STATUS_XFAILED),
        ],
    )
    execution = Execution(features=[feature], statistics=Statistics())
    stats_mod.compute(execution)
    assert feature.status != "failed"


# ---------------------------------------------------------------------------
# BUG 18: Collector._make_attachment was called but never defined, causing
#         AttributeError when Behave steps have embeddings
# ---------------------------------------------------------------------------


def test_collector_make_attachment_exists():
    """Collector should have a _make_attachment method."""
    from behave_modern_html_report.collector import Collector

    c = Collector()
    assert hasattr(c, "_make_attachment")
    assert callable(c._make_attachment)


def test_collector_make_attachment_with_bytes():
    """_make_attachment should convert raw bytes into an Attachment."""
    import base64

    from behave_modern_html_report.collector import Collector

    class FakeEmbedding:
        mime_type = "image/png"
        filename = "screenshot.png"
        data = b"\x89PNG\r\n\x1a\n"

    c = Collector()
    att = c._make_attachment(FakeEmbedding())
    assert att.name == "screenshot.png"
    assert att.mime_type == "image/png"
    assert att.data_base64 == base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("ascii")
    assert att.is_image


def test_collector_make_attachment_with_text():
    """_make_attachment should decode text attachments."""
    from behave_modern_html_report.collector import Collector

    class FakeEmbedding:
        mime_type = "text/plain"
        filename = "log.txt"
        data = b"hello world"

    c = Collector()
    att = c._make_attachment(FakeEmbedding())
    assert att.name == "log.txt"
    assert att.mime_type == "text/plain"
    assert att.text == "hello world"
    assert att.is_text


def test_collector_make_attachment_with_no_data():
    """_make_attachment should handle missing data gracefully."""
    from behave_modern_html_report.collector import Collector

    class FakeEmbedding:
        mime_type = "application/octet-stream"
        filename = "empty.bin"

    c = Collector()
    att = c._make_attachment(FakeEmbedding())
    assert att.name == "empty.bin"
    assert att.data_base64 == ""


def test_collector_step_with_embeddings():
    """_make_step should not crash when step has embeddings."""
    from behave_modern_html_report.collector import Collector

    class FakeEmbedding:
        mime_type = "image/png"
        filename = "shot.png"
        data = b"\x89PNG"

    class FakeStep:
        keyword = "Given"
        name = "a step"
        status = "passed"
        duration = 0.1
        location = "test.feature:1"
        embeddings = [FakeEmbedding()]

    c = Collector()
    step = c._make_step(FakeStep())
    assert len(step.attachments) == 1
    assert step.attachments[0].name == "shot.png"


# ---------------------------------------------------------------------------
# BUG 19: Python 3.13 classifier missing from pyproject.toml
# ---------------------------------------------------------------------------


def test_pyproject_has_python_313_classifier():
    """pyproject.toml should list Python 3.13 in classifiers."""
    import tomllib
    from pathlib import Path

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    classifiers = data["project"]["classifiers"]
    assert "Programming Language :: Python :: 3.13" in classifiers


# ---------------------------------------------------------------------------
# BUG 20: Templates referenced scenario.error but Scenario has no error
#         attribute, so error text was always empty in the results table
#         and scenario items. Fix: derive from first failed step's error.
# ---------------------------------------------------------------------------


def test_scenario_error_appears_in_rendered_html():
    """Rendered HTML should contain the error message from a failed step."""
    from behave_modern_html_report.models import ErrorInfo
    from behave_modern_html_report.renderer import Renderer, RenderOptions

    step = Step(
        keyword="Then",
        name="assertion fails",
        status="failed",
        duration=0.1,
        error=ErrorInfo(message="Expected 200 but got 500", exception_type="AssertionError"),
    )
    scenario = Scenario(name="Failing scenario", status="failed", feature_name="Test", steps=[step])
    feature = Feature(name="Test", scenarios=[scenario])
    execution = Execution(features=[feature], statistics=Statistics())
    stats_mod.compute(execution)

    renderer = Renderer(RenderOptions())
    html = renderer.render(execution)
    assert "expected 200 but got 500" in html.lower()


# ---------------------------------------------------------------------------
# BUG 21: StepCatalogFormatter.close() had a resource leak — if
#         stream.write(html) raised, the stream was never closed.
# ---------------------------------------------------------------------------


def test_step_catalog_formatter_close_resource_leak():
    """StepCatalogFormatter.close() should close stream even if write fails."""
    from behave_modern_html_report.step_catalog_formatter import StepCatalogFormatter

    class FailingStream:
        def write(self, data):
            raise OSError("write failed")

        def close(self):
            self.closed = True

    class FakeStreamOpener:
        name = None
        stream = None

        def open(self):
            self.stream = FailingStream()
            return self.stream

    class FakeConfig:
        base_dir = "."
        userdata = {}

    opener = FakeStreamOpener()
    fmt = StepCatalogFormatter(opener, FakeConfig())
    # Should not raise — the IOError from write should propagate but stream
    # should still be closed via finally.
    try:
        fmt.close()
        raise AssertionError("Should have raised OSError")
    except OSError:
        pass
    # The stream should have been closed despite the error.
    assert opener.stream.closed


# ---------------------------------------------------------------------------
# BUG 22: report.js querySelector for default_view could throw SyntaxError
#         if default_view contains CSS selector metacharacters, crashing
#         the entire IIFE. Fixed by wrapping in try/catch.
#         (JS fix — regression test verifies the fix is present in source.)
# ---------------------------------------------------------------------------


def test_report_js_has_try_catch_default_view():
    """report.js should wrap default_view querySelector in try/catch."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/report.js")
    assert "try {" in js and "DATA.default_view" in js
    # Verify the try/catch is near the default_view logic
    idx = js.index("DATA.default_view")
    surrounding = js[max(0, idx - 100) : idx + 200]
    assert "try" in surrounding or "catch" in surrounding


# ---------------------------------------------------------------------------
# BUG 23: charts.js formatDuration didn't handle negative values, unlike
#         the Python format_duration which was already fixed.
# ---------------------------------------------------------------------------


def test_charts_js_format_duration_negative():
    """charts.js formatDuration should handle negative/null values."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/charts.js")
    assert "s < 0" in js or "s == null" in js


# ---------------------------------------------------------------------------
# BUG 24: charts.js roundRect could produce negative radius via arcTo
#         when width or height is zero/negative, causing IndexSizeError.
#         Fixed by clamping w/h to >= 0 and r to >= 0, with rect fallback.
# ---------------------------------------------------------------------------


def test_charts_js_round_rect_clamped():
    """charts.js roundRect should clamp width/height/radius to >= 0."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/charts.js")
    assert "Math.max(w, 0)" in js
    assert "Math.max(0" in js


# ---------------------------------------------------------------------------
# BUG 25: (Not a bug — Jinja2 autoescape prevents CSS injection breakout.
#          User controls behave.ini and has custom_css for custom styling.)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BUG 26: Execution.overall_status didn't handle xfailed/xpassed feature
#         statuses, returning "untested" when tests actually ran.
# ---------------------------------------------------------------------------


def test_overall_status_with_xfailed():
    """overall_status should return 'passed' when features have xfailed status."""
    from behave_modern_html_report.models import STATUS_XFAILED

    scenario = Scenario(name="xfail", status=STATUS_XFAILED)
    feature = Feature(name="F", scenarios=[scenario])
    execution = Execution(features=[feature], statistics=Statistics())
    stats_mod.compute(execution)
    assert execution.overall_status == "passed"


def test_overall_status_with_xpassed():
    """overall_status should return 'passed' when features have xpassed status."""
    from behave_modern_html_report.models import STATUS_XPASSED

    scenario = Scenario(name="xpass", status=STATUS_XPASSED)
    feature = Feature(name="F", scenarios=[scenario])
    execution = Execution(features=[feature], statistics=Statistics())
    stats_mod.compute(execution)
    assert execution.overall_status == "passed"


# ---------------------------------------------------------------------------
# BUG 27: collector._make_attachment stored raw string in data_base64
#         instead of base64-encoding it, producing broken data: URLs and
#         causing text extraction to fail on non-bytes data.
# ---------------------------------------------------------------------------


def test_make_attachment_with_string_data():
    """_make_attachment should base64-encode string data properly."""
    import base64

    from behave_modern_html_report.collector import Collector

    class FakeEmbedding:
        mime_type = "text/plain"
        filename = "note.txt"
        data = "Hello, world!"

    collector = Collector()
    att = collector._make_attachment(FakeEmbedding())
    decoded = base64.b64decode(att.data_base64).decode("utf-8")
    assert decoded == "Hello, world!"
    assert att.text == "Hello, world!"


def test_make_attachment_with_bytes_data():
    """_make_attachment should base64-encode bytes data properly."""
    import base64

    from behave_modern_html_report.collector import Collector

    class FakeEmbedding:
        mime_type = "image/png"
        filename = "screenshot.png"
        data = b"\x89PNG\r\n\x1a\n"

    collector = Collector()
    att = collector._make_attachment(FakeEmbedding())
    decoded = base64.b64decode(att.data_base64)
    assert decoded == b"\x89PNG\r\n\x1a\n"
    assert att.text is None


def test_make_attachment_with_none_data():
    """_make_attachment should handle None data gracefully."""
    from behave_modern_html_report.collector import Collector

    class FakeEmbedding:
        mime_type = "application/octet-stream"
        filename = "empty.bin"
        data = None

    collector = Collector()
    att = collector._make_attachment(FakeEmbedding())
    assert att.data_base64 == ""
    assert att.text is None


# ---------------------------------------------------------------------------
# BUG 30: step_catalog.html.jinja JSON.parse had no try/catch, could crash
#         all interactivity if data was malformed.
# ---------------------------------------------------------------------------


def test_step_catalog_json_parse_has_try_catch():
    """step_catalog template should wrap JSON.parse in try/catch."""
    from pathlib import Path

    template = (
        Path(__file__).resolve().parent.parent
        / "behave_modern_html_report"
        / "templates"
        / "step_catalog.html.jinja"
    )
    content = template.read_text(encoding="utf-8")
    assert "try" in content and "JSON.parse" in content
    idx = content.index("JSON.parse")
    surrounding = content[max(0, idx - 100) : idx + 200]
    assert "try" in surrounding or "catch" in surrounding


# ---------------------------------------------------------------------------
# BUG 31: step_catalog.html.jinja window.matchMedia call was unguarded,
#         could crash in browsers without matchMedia support.
# ---------------------------------------------------------------------------


def test_step_catalog_matchmedia_guarded():
    """step_catalog template should guard window.matchMedia with &&."""
    from pathlib import Path

    template = (
        Path(__file__).resolve().parent.parent
        / "behave_modern_html_report"
        / "templates"
        / "step_catalog.html.jinja"
    )
    content = template.read_text(encoding="utf-8")
    assert "window.matchMedia &&" in content


# ---------------------------------------------------------------------------
# BUG 32: json.dumps in renderer.py didn't escape < and >, allowing XSS
#         via crafted scenario/step names containing </script> tags.
# ---------------------------------------------------------------------------


def test_json_data_escaped_for_xss():
    """JSON data embedded in script tag should have < and > escaped."""
    from behave_modern_html_report.models import STATUS_PASSED

    xss_step = Step(
        keyword="Given", name="</script><script>alert(1)</script>", status=STATUS_PASSED
    )
    xss_scenario = Scenario(
        name="</script><script>alert(1)</script>", status=STATUS_PASSED, steps=[xss_step]
    )
    xss_feature = Feature(name="</script><script>alert(1)</script>", scenarios=[xss_scenario])
    execution = Execution(features=[xss_feature], statistics=Statistics())
    renderer = Renderer(RenderOptions())
    html = renderer.render(execution)
    # The raw </script> should not appear inside the JSON data block
    json_start = html.index('id="bmr-data"')
    json_end = html.index("</script>", json_start)
    json_block = html[json_start:json_end]
    assert "<script>alert(1)</script>" not in json_block
    assert "\\u003c" in json_block or "\\u003e" in json_block


# ---------------------------------------------------------------------------
# BUG 33: report.js lightbox used innerHTML with unsanitized data-attach-img,
#         allowing XSS via crafted attachment mime_type.
# ---------------------------------------------------------------------------


def test_report_js_lightbox_no_innerhtml_injection():
    """report.js lightbox should use DOM API (createElement) not innerHTML for img."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/report.js")
    assert "createElement" in js
    # Verify the lightbox section doesn't use string concatenation for img src
    idx = js.index("data-attach-img")
    surrounding = js[idx : idx + 300]
    assert "createElement" in surrounding


# ---------------------------------------------------------------------------
# BUG 34: attach_screenshot didn't handle file read errors, raising raw
#         FileNotFoundError/PermissionError without context.
# ---------------------------------------------------------------------------


def test_attach_screenshot_file_error_message():
    """attach_screenshot should raise OSError with descriptive message for missing file."""
    from unittest.mock import patch

    from behave_modern_html_report.attach import attach_screenshot

    class FakeFormatter:
        def attach(self, attachment):
            pass

    class FakeContext:
        pass

    with (
        patch("behave_modern_html_report.attach._find_formatters", return_value=[FakeFormatter()]),
        pytest.raises(OSError, match="Cannot read screenshot file"),
    ):
        attach_screenshot(FakeContext(), "nonexistent_screenshot.png")


# ---------------------------------------------------------------------------
# BUG 35: formatter.attach_file didn't handle file read errors, raising raw
#         FileNotFoundError/PermissionError without context.
# ---------------------------------------------------------------------------


def test_attach_file_error_message():
    """attach_file should raise OSError with descriptive message for missing file."""
    from behave_modern_html_report.formatter import ModernHTMLFormatter

    class FakeStreamOpener:
        name = "output/report.html"
        stream = None

    class FakeConfig:
        base_dir = "."
        userdata = {}

    fmt = ModernHTMLFormatter(FakeStreamOpener(), FakeConfig())
    with pytest.raises(OSError, match="Cannot read attachment file"):
        fmt.attach_file("nonexistent_file.txt")


# ---------------------------------------------------------------------------
# BUG 36: report.js copy button querySelector could throw SyntaxError when
#         data-copy-target contains CSS selector metacharacters from step
#         names/locations, killing the click handler.
# ---------------------------------------------------------------------------


def test_report_js_copy_queryselector_guarded():
    """report.js copy button should wrap querySelector in try/catch."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/report.js")
    idx = js.index("copyTarget")
    surrounding = js[idx : idx + 200]
    assert "try" in surrounding or "catch" in surrounding


# ---------------------------------------------------------------------------
# BUG 37: format_duration crashed on float('nan') and float('inf') due to
#         int() raising ValueError on non-finite values.
# ---------------------------------------------------------------------------


def test_format_duration_nan():
    """format_duration should return '0ms' for NaN."""
    from behave_modern_html_report.utils import format_duration

    assert format_duration(float("nan")) == "0ms"


def test_format_duration_inf():
    """format_duration should return '0ms' for infinity."""
    from behave_modern_html_report.utils import format_duration

    assert format_duration(float("inf")) == "0ms"


def test_format_duration_negative_inf():
    """format_duration should return '0ms' for negative infinity."""
    from behave_modern_html_report.utils import format_duration

    assert format_duration(float("-inf")) == "0ms"


def test_charts_js_format_duration_isfinite():
    """charts.js formatDuration should check isFinite."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/charts.js")
    assert "isFinite" in js


# ---------------------------------------------------------------------------
# BUG 38: attach_file in attach.py had no error handling for file reads,
#         raising raw FileNotFoundError without context.
# ---------------------------------------------------------------------------


def test_attach_file_module_level_error_message():
    """attach_file (module-level) should raise OSError with descriptive message."""
    from unittest.mock import patch

    from behave_modern_html_report.attach import attach_file

    class FakeFormatter:
        def attach(self, attachment):
            pass

    class FakeContext:
        pass

    with (
        patch("behave_modern_html_report.attach._find_formatters", return_value=[FakeFormatter()]),
        pytest.raises(OSError, match="Cannot read attachment file"),
    ):
        attach_file(FakeContext(), "nonexistent_file.txt")


# ---------------------------------------------------------------------------
# BUG 39: _derive_feature_status didn't handle xfailed/xpassed statuses,
#         falling through to unreliable statuses[0] return.
# ---------------------------------------------------------------------------


def test_derive_feature_status_xfailed():
    """_derive_feature_status should return 'passed' for all-xfailed features."""
    from behave_modern_html_report.models import STATUS_XFAILED, Feature, Scenario
    from behave_modern_html_report.statistics import _derive_feature_status

    feature = Feature(
        name="test",
        scenarios=[
            Scenario(name="s1", status=STATUS_XFAILED),
            Scenario(name="s2", status=STATUS_XFAILED),
        ],
    )
    assert _derive_feature_status(feature) == "passed"


def test_derive_feature_status_xpassed():
    """_derive_feature_status should return 'passed' for xpassed scenarios."""
    from behave_modern_html_report.models import STATUS_XPASSED, Feature, Scenario
    from behave_modern_html_report.statistics import _derive_feature_status

    feature = Feature(
        name="test",
        scenarios=[
            Scenario(name="s1", status=STATUS_XPASSED),
        ],
    )
    assert _derive_feature_status(feature) == "passed"


# ---------------------------------------------------------------------------
# BUG 44: _make_step crashed on non-numeric duration values (e.g. "unknown")
#         due to float() raising ValueError.
# ---------------------------------------------------------------------------


def test_make_step_non_numeric_duration():
    """_make_step should handle non-numeric duration gracefully."""
    from behave_modern_html_report.collector import Collector

    class FakeStep:
        keyword = "Given"
        name = "test step"
        status = "passed"
        duration = "not_a_number"
        location = "test.feature:1"
        text = None
        table = None
        error_message = None
        exception = None
        embeddings = []
        log = []

    collector = Collector()
    collector.start_feature(
        type(
            "F",
            (),
            {"name": "f", "description": [], "location": "", "tags": [], "background": None},
        )()
    )
    collector.start_scenario(
        type(
            "S",
            (),
            {
                "name": "s",
                "description": [],
                "location": "",
                "tags": [],
                "type": "scenario",
                "examples": None,
            },
        )()
    )
    step = collector.add_step(FakeStep())
    assert step is not None
    assert step.duration == 0.0


# ---------------------------------------------------------------------------
# BUG 45: end_feature and end_scenario crashed on non-numeric duration values
#         due to float() raising ValueError.
# ---------------------------------------------------------------------------


def test_end_scenario_non_numeric_duration():
    """end_scenario should handle non-numeric duration gracefully."""
    from behave_modern_html_report.collector import Collector

    class FakeScenario:
        name = "s"
        description = []
        location = ""
        tags = []
        type = "scenario"
        examples = None

    class FakeFinal:
        status = "passed"
        duration = "invalid"

    collector = Collector()
    collector.start_feature(
        type(
            "F",
            (),
            {"name": "f", "description": [], "location": "", "tags": [], "background": None},
        )()
    )
    collector.start_scenario(FakeScenario())
    collector.end_scenario(FakeFinal())
    # Should not raise, duration should be 0.0


def test_end_feature_non_numeric_duration():
    """end_feature should handle non-numeric duration gracefully."""
    from behave_modern_html_report.collector import Collector

    class FakeFeature:
        name = "f"
        description = []
        location = ""
        tags = []
        background = None

    class FakeFinal:
        status = "passed"
        duration = "invalid"

    collector = Collector()
    collector.start_feature(FakeFeature())
    collector.end_feature(FakeFinal())
    # Should not raise, duration should be 0.0


# ---------------------------------------------------------------------------
# BUG 46: attach_* helpers silently no-op'd because ModernHTMLFormatter had
#         no .attach attribute, so _find_formatter never matched it.
# ---------------------------------------------------------------------------


def _make_formatter(userdata=None, name="report.html"):
    from behave_modern_html_report.formatter import ModernHTMLFormatter

    opener = SimpleNamespace(name=name, stream=None)
    config = SimpleNamespace(base_dir=".", userdata=userdata or {})
    return ModernHTMLFormatter(opener, config)


def test_find_formatter_matches_real_formatter():
    """_find_formatter must find a real ModernHTMLFormatter."""
    from behave_modern_html_report.attach import _find_formatter

    fmt = _make_formatter()
    ctx = SimpleNamespace(_runner=SimpleNamespace(formatters=[fmt]))
    assert _find_formatter(ctx) is fmt


def test_attach_text_reaches_collector_via_real_formatter():
    """attach_text must deliver an attachment through the real formatter."""
    from behave_modern_html_report.attach import attach_text

    fmt = _make_formatter()
    ctx = SimpleNamespace(_runner=SimpleNamespace(formatters=[fmt]))
    fmt._collector._current_scenario = Scenario(name="s")
    attach_text(ctx, "hello", name="n.txt")
    # Attachments queue during step execution and flush into the next result.
    fmt._collector.add_step(SimpleNamespace(keyword="Given", name="x"))
    assert fmt._collector._current_scenario.steps[-1].attachments[0].text == "hello"


def test_formatter_embedding_via_context_attach():
    """context.attach() must reach the collector through embedding()."""
    fmt = _make_formatter()
    fmt._collector._current_scenario = Scenario(name="s")
    fmt.embedding("image/png", b"\x89PNG")
    fmt._collector.add_step(SimpleNamespace(keyword="Given", name="x"))
    att = fmt._collector._current_scenario.steps[-1].attachments[0]
    assert att.mime_type == "image/png"
    assert att.is_image


# ---------------------------------------------------------------------------
# BUG 47: formatter.close() ignored bmr.json_sidecar.
# ---------------------------------------------------------------------------


def test_close_writes_json_sidecar(tmp_path):
    """close() must write report.json next to report.html when enabled."""
    import json
    import sys

    out = tmp_path / "report.html"
    fmt = _make_formatter(userdata={"bmr.json_sidecar": "true"}, name=str(out))
    feature = SimpleNamespace(
        name="F", description=[], location="f:1", tags=[], background=None, filename="f.feature"
    )
    fmt.uri("f.feature")
    fmt.feature(feature)
    fmt.eof()
    import io

    old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        fmt.close()
    finally:
        sys.stdout = old
    assert out.exists()
    sidecar = out.with_suffix(".json")
    assert sidecar.exists()
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    assert "execution" in data


# ---------------------------------------------------------------------------
# BUG 48: scenario outlines never detected — Behave passes expanded Scenario
#         instances (type="scenario") with _row and a ScenarioOutline parent.
# ---------------------------------------------------------------------------


def test_collector_detects_expanded_outline_scenario():
    """Expanded outline instances must set is_outline/outline_name/examples."""
    from behave_modern_html_report.collector import Collector

    table = SimpleNamespace(
        headings=["u", "p"],
        rows=[SimpleNamespace(cells=["a", "1"]), SimpleNamespace(cells=["b", "2"])],
    )
    outline = SimpleNamespace(
        type="scenario_outline",
        name="Login",
        examples=[SimpleNamespace(table=table)],
    )
    expanded = SimpleNamespace(
        name="Login -- @1.1 ",
        description=[],
        location="f:10",
        tags=[],
        status="passed",
        duration=0.0,
        type="scenario",
        _row=SimpleNamespace(),
        parent=outline,
        background=None,
    )
    c = Collector()
    c.start_feature(
        SimpleNamespace(name="F", description=[], location="f:1", tags=[], background=None)
    )
    c.start_scenario(expanded)
    scenario = c._current_scenario
    assert scenario.is_outline
    assert scenario.outline_name == "Login"
    assert scenario.examples.headings == ["u", "p"]
    assert scenario.examples.rows == [["a", "1"], ["b", "2"]]


# ---------------------------------------------------------------------------
# BUG 49: charts.js hidpi() used the DPR-scaled buffer height, doubling the
#         canvas height on every re-render when devicePixelRatio > 1.
# ---------------------------------------------------------------------------


def test_charts_hidpi_uses_rect_height():
    """hidpi() must derive height from the layout rect, not canvas.height."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/charts.js")
    assert "rect.height" in js


# ---------------------------------------------------------------------------
# BUG 50: env vars like GITHUB_TOKEN were embedded verbatim into the report.
# ---------------------------------------------------------------------------


def test_env_var_secrets_are_redacted(monkeypatch):
    """Captured CI env vars with sensitive names must be masked."""
    from behave_modern_html_report.collector import Collector

    monkeypatch.setenv("GITHUB_TOKEN", "super-secret-value")
    env = Collector().execution.environment
    assert env.env_vars.get("GITHUB_TOKEN") == "***"
    assert "super-secret-value" not in str(env.env_vars)


# ---------------------------------------------------------------------------
# BUG 51: data-error only carried the first step's error, so "Search in
#         error text" missed errors in later steps.
# ---------------------------------------------------------------------------


def test_data_error_includes_all_errors():
    """data-error must contain every step error message."""
    from behave_modern_html_report.models import STATUS_FAILED, ErrorInfo

    steps = [
        Step(
            keyword="Given",
            name="a",
            status=STATUS_FAILED,
            error=ErrorInfo(exception_type="E", message="first boom"),
        ),
        Step(
            keyword="Then",
            name="b",
            status=STATUS_FAILED,
            error=ErrorInfo(exception_type="E", message="second boom"),
        ),
    ]
    scenario = Scenario(name="s", status=STATUS_FAILED, steps=steps)
    execution = Execution(
        features=[Feature(name="f", scenarios=[scenario])], statistics=Statistics()
    )
    html = Renderer(RenderOptions()).render(execution)
    assert "first boom" in html and "second boom" in html
    import re

    m = re.search(r'data-error="([^"]*)"', html)
    assert m and "first boom" in m.group(1) and "second boom" in m.group(1)


# ---------------------------------------------------------------------------
# BUG 52: scan_file crashed with ValueError when base_dir didn't contain file.
# ---------------------------------------------------------------------------


def test_scan_file_outside_base_dir(tmp_path):
    """scan_file must not crash when file is outside base_dir."""
    f = tmp_path / "steps.py"
    f.write_text("from behave import given\n\n@given('x')\ndef s(c): pass\n", encoding="utf-8")
    defs = scan_file(f, base_dir=tmp_path / "elsewhere")
    assert len(defs) == 1


# ---------------------------------------------------------------------------
# BUG 53: Jinja autoescape only covered .html/.xml templates — every *.jinja
#         template rendered unescaped, allowing XSS via scenario/step names.
# ---------------------------------------------------------------------------


def test_renderer_autoescapes_jinja_templates():
    """Scenario/feature names with HTML must be escaped in the report."""
    from behave_modern_html_report.models import Execution, Feature, Scenario, Statistics

    sc = Scenario(name="<script>alert(1)</script>", status="failed", location="f:1")
    ex = Execution(
        features=[Feature(name="<img src=x onerror=alert(1)>", scenarios=[sc])],
        statistics=Statistics(),
    )
    html = Renderer(RenderOptions()).render(ex)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


# ---------------------------------------------------------------------------
# BUG 54: attachments/logs produced in after_step hooks landed on the PREVIOUS
#         step (often a background step) because Behave runs after_step before
#         the formatter's result event, so the current step was not yet stored.
# ---------------------------------------------------------------------------


def _stub_feature(name="F", tags=()):
    return SimpleNamespace(
        name=name, description=[], location="f.feature:1", tags=list(tags)
    )


def _stub_scenario(name="S", tags=()):
    return SimpleNamespace(
        name=name, description=[], location="f.feature:3", tags=list(tags)
    )


def _stub_step(name):
    return SimpleNamespace(
        keyword="Then", name=name, status="passed", duration=0.01,
        location="f.feature:4", text=None, table=None,
    )


def test_after_step_attachment_lands_on_current_step_not_previous():
    """Attachments queued after step N's result flush into step N+1."""
    from behave_modern_html_report.collector import Collector
    from behave_modern_html_report.models import Attachment

    c = Collector()
    c.start_feature(_stub_feature())
    scenario_stub = _stub_scenario()
    scenario_stub.background = SimpleNamespace(
        name="bg", keyword="Background", location="f.feature:2"
    )
    c.start_scenario(scenario_stub)
    c.add_step(_stub_step("first"), is_background=True)
    # after_step(second) runs here, before result(second) is reported.
    c.attach(Attachment(name="a.txt", mime_type="text/plain", text="mine"))
    c.add_step(_stub_step("second"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))

    scenario = c.execution.features[0].scenarios[0]
    assert scenario.background.steps[0].attachments == []
    assert scenario.steps[0].attachments[0].text == "mine"


def test_after_step_log_lands_on_current_step_not_previous():
    """Log lines queued between result events flush into the next step."""
    from behave_modern_html_report.collector import Collector

    c = Collector()
    c.start_feature(_stub_feature())
    c.start_scenario(_stub_scenario())
    c.add_step(_stub_step("first"))
    c.log("after_step log")
    c.add_step(_stub_step("second"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))

    scenario = c.execution.features[0].scenarios[0]
    assert scenario.steps[0].logs == []
    assert scenario.steps[1].logs == ["after_step log"]


def test_pending_cleared_between_scenarios():
    """Leftover pendings never leak into a later scenario."""
    from behave_modern_html_report.collector import Collector

    c = Collector()
    c.start_feature(_stub_feature())
    c.start_scenario(_stub_scenario("S1"))
    c.attach(Attachment(name="a.txt", mime_type="text/plain", text="x"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.start_scenario(_stub_scenario("S2"))
    c.add_step(_stub_step("step"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))

    s2 = c.execution.features[0].scenarios[1]
    assert s2.steps[0].attachments == []


# ---------------------------------------------------------------------------
# BUG 55: rule and feature tags were missing from scenario.tags, so tag
#         statistics and search ignored inherited (effective) tags.
# ---------------------------------------------------------------------------


def test_scenario_tags_include_rule_and_feature_tags():
    """Effective tags (own + rule + feature) are merged in document order."""
    from behave_modern_html_report.collector import Collector

    c = Collector()
    c.start_feature(_stub_feature("F", tags=["ftag"]))
    c.start_rule(SimpleNamespace(name="R", tags=["rtag"]))
    c.start_scenario(_stub_scenario("S", tags=["stag"]))

    scenario = c.execution.features[0].scenarios[0]
    assert scenario.tags == ["stag", "rtag", "ftag"]


def test_rule_tags_reset_between_rules_and_features():
    """Rule tags must not leak into scenarios outside the rule."""
    from behave_modern_html_report.collector import Collector

    c = Collector()
    c.start_feature(_stub_feature("F1", tags=["ftag"]))
    c.start_rule(SimpleNamespace(name="R", tags=["rtag"]))
    c.start_scenario(_stub_scenario("S1"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.end_rule()
    c.start_scenario(_stub_scenario("S2"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))

    scenarios = c.execution.features[0].scenarios
    assert scenarios[0].tags == ["rtag", "ftag"]
    assert scenarios[1].tags == ["ftag"]


# ---------------------------------------------------------------------------
# BUG 56: hook failures on scenarios/features (before_scenario, after_feature)
#         were silently dropped — the report showed hook_error with no detail.
# ---------------------------------------------------------------------------


def test_scenario_hook_error_captured():
    """error_message/exception on the behave scenario become scenario.error."""
    from behave_modern_html_report.collector import Collector

    c = Collector()
    c.start_feature(_stub_feature())
    c.start_scenario(_stub_scenario())
    c.end_scenario(
        SimpleNamespace(
            status="hook_error",
            duration=0.0,
            error_message="HOOK-ERROR in before_scenario: RuntimeError: boom",
            exception=RuntimeError("boom"),
            exc_traceback=None,
        )
    )

    scenario = c.execution.features[0].scenarios[0]
    assert scenario.error is not None
    assert "HOOK-ERROR" in scenario.error.message
    assert scenario.error.exception_type == "RuntimeError"


def test_feature_hook_error_captured():
    """error_message/exception on the behave feature become feature.error."""
    from behave_modern_html_report.collector import Collector

    c = Collector()
    c.start_feature(_stub_feature())
    c.end_feature(
        SimpleNamespace(
            status="error",
            duration=0.0,
            error_message="HOOK-ERROR in before_feature: OSError: nope",
            exception=OSError("nope"),
            exc_traceback=None,
        )
    )

    feature = c.execution.features[0]
    assert feature.error is not None
    assert feature.error.exception_type == "OSError"


def test_hook_error_renders_in_report():
    """A scenario-level hook error is rendered in the HTML body."""
    from behave_modern_html_report.collector import Collector
    from behave_modern_html_report.renderer import Renderer, RenderOptions

    c = Collector()
    c.start_feature(_stub_feature())
    c.start_scenario(_stub_scenario("hooked"))
    c.end_scenario(
        SimpleNamespace(
            status="hook_error",
            duration=0.0,
            error_message="HOOK-ERROR in before_scenario: RuntimeError: boom",
            exception=RuntimeError("boom"),
            exc_traceback=None,
        )
    )
    c.end_feature(SimpleNamespace(status="hook_error", duration=0.0))
    html = Renderer(RenderOptions()).render(c.finalize())
    assert "HOOK-ERROR in before_scenario" in html


# ---------------------------------------------------------------------------
# BUG 57: exc_traceback objects were str()-ed, producing
#         "<traceback object at 0x...>" instead of the real stack.
# ---------------------------------------------------------------------------


def test_step_error_formats_real_traceback():
    """exc_traceback objects are formatted into readable stack text."""
    import sys

    from behave_modern_html_report.collector import Collector

    try:
        raise ValueError("real failure")
    except ValueError:
        exc_type, exc, tb = sys.exc_info()

    step_stub = _stub_step("boom")
    step_stub.status = "failed"
    step_stub.error_message = "ValueError: real failure"
    step_stub.exception = exc
    step_stub.exc_traceback = tb

    step = Collector()._make_error(step_stub)
    assert step is not None
    assert "test_step_error_formats_real_traceback" in step.traceback
    assert "<traceback object" not in step.traceback
    assert step.exception_type == "ValueError"



# ---------------------------------------------------------------------------
# BUG 58: error_distribution ignored background steps and scenario/feature
#         hook errors, diverging from compute()'s exception counting.
# ---------------------------------------------------------------------------


def test_error_distribution_includes_background_and_scenario_errors():
    """error_distribution counts errors on bg steps, scenarios and features."""
    from behave_modern_html_report.models import Background, ErrorInfo

    bg_step = Step(
        keyword="Given", name="bg", status="failed",
        error=ErrorInfo(message="x", exception_type="BgpError"),
    )
    scenario = Scenario(
        name="S", status="failed",
        background=Background(name="bg", steps=[bg_step]),
        steps=[
            Step(
                keyword="Then", name="s", status="failed",
                error=ErrorInfo(message="y", exception_type="StepError"),
            )
        ],
        error=ErrorInfo(message="hook", exception_type="HookError"),
    )
    feature = Feature(
        name="F", scenarios=[scenario],
        error=ErrorInfo(message="feat", exception_type="FeatError"),
    )
    counts = stats_mod.error_distribution(Execution(features=[feature]))
    assert counts == {"BgpError": 1, "StepError": 1, "HookError": 1, "FeatError": 1}


# ---------------------------------------------------------------------------
# BUG 59: slowest_scenarios with a negative limit returned all-but-last-N
#         scenarios instead of an empty list.
# ---------------------------------------------------------------------------


def test_slowest_scenarios_negative_limit():
    """A negative limit must not return a wrong-tail slice."""
    feature = Feature(
        name="F",
        scenarios=[Scenario(name="S1", duration=1.0), Scenario(name="S2", duration=2.0)],
    )
    execution = Execution(features=[feature])
    assert stats_mod.slowest_scenarios(execution, limit=-1) == []


# ---------------------------------------------------------------------------
# BUG 60: format_duration crashed with TypeError on non-numeric input
#         (e.g. a string duration reaching the Jinja filter).
# ---------------------------------------------------------------------------


def test_format_duration_non_numeric():
    """format_duration returns '0ms' for non-numeric/invalid input."""
    assert format_duration("abc") == "0ms"
    assert format_duration(None) == "0ms"
    assert format_duration("1.5") == "1.50s"


# ---------------------------------------------------------------------------
# BUG 61: scan_file/scan_directory crashed when given a str instead of Path
#         (the public API hints Path but accepts str in docs).
# ---------------------------------------------------------------------------


def test_scan_file_and_directory_accept_str(tmp_path):
    """Scanner public API must accept string paths."""
    from behave_modern_html_report.step_scanner import scan_directory

    steps = tmp_path / "steps"
    steps.mkdir()
    (steps / "s.py").write_text(
        "from behave import given\n\n@given('x')\ndef s(c): pass\n", encoding="utf-8"
    )
    catalog = scan_directory(str(steps))
    assert len(catalog.steps) == 1
    defs = scan_file(str(steps / "s.py"))
    assert len(defs) == 1


# ---------------------------------------------------------------------------
# BUG 62: assets.read_text allowed path traversal outside the assets dir.
# ---------------------------------------------------------------------------


def test_read_text_rejects_path_traversal():
    """read_text must reject paths escaping the package assets directory."""
    from behave_modern_html_report.assets import read_text

    with pytest.raises(ValueError):
        read_text("../../../../etc/passwd")
    with pytest.raises(ValueError):
        read_text("../__init__.py")
    assert "BMRChart" in read_text("js/charts.js")


# ---------------------------------------------------------------------------
# BUG 63: _extract_params returned regex quantifiers ("1,3") and typed
#         placeholders ("count:d") as parameter names.
# ---------------------------------------------------------------------------


def test_extract_params_strips_types_and_ignores_regex_quantifiers(tmp_path):
    """Params come from {name}/{name:Type} only — not regex {m,n} braces."""
    (tmp_path / "s.py").write_text(
        "import re\nfrom behave import given\n\n"
        "@given('I have {count:d} items')\n"
        "def step_count(context, count): pass\n\n"
        "@given(re.compile(r'^I wait (\\d{1,3}) seconds$'))\n"
        "def step_wait(context, n): pass\n",
        encoding="utf-8",
    )
    defs = scan_file(tmp_path / "s.py")
    assert defs[0].params == ["count"]
    assert defs[1].params == ["n"]


# ---------------------------------------------------------------------------
# BUG 64: attach_screenshot crashed with TypeError when a source returned
#         str instead of bytes (b64encode needs bytes-like).
# ---------------------------------------------------------------------------


def test_attach_screenshot_handles_str_data():
    """Screenshot sources returning str are coerced to bytes, not crashed."""
    import base64

    from behave_modern_html_report.attach import attach_screenshot

    class _Fmt:
        def __init__(self):
            self.last_attachment = None

        def attach(self, att):
            self.last_attachment = att

        def log(self, msg):
            pass

    fmt = _Fmt()
    context = SimpleNamespace(_runner=SimpleNamespace(formatters=[fmt]))
    source = SimpleNamespace(get_screenshot_as_png=lambda: "faux-png")
    attach_screenshot(context, source, "shot.png")
    assert fmt.last_attachment.data_base64 == base64.b64encode(b"faux-png").decode()


# ---------------------------------------------------------------------------
# BUG 65: _resolve_output_path returned Path("<stdout>") when the stream
#         opener name was a behave pseudo-file, crashing the write on Windows.
# ---------------------------------------------------------------------------


def test_resolve_output_path_ignores_pseudo_streams():
    """'<stdout>'/'<stderr>'/'-' names must not become literal filenames."""
    config = SimpleNamespace(userdata={}, outputs=[])
    for pseudo in ("<stdout>", "<stderr>", "-"):
        fmt = ModernHTMLFormatter(SimpleNamespace(name=pseudo, stream=None), config)
        assert fmt._output_path.name == "behave-modern-html-report.html"


# ---------------------------------------------------------------------------
# BUG 66: formatter.attach_file never set `text` for text files, so text
#         attachments via the formatter API didn't render inline (unlike the
#         attach.py helper, which did).
# ---------------------------------------------------------------------------


def test_formatter_attach_file_sets_text_for_text_files(tmp_path):
    """formatter.attach_file decodes text files into Attachment.text."""
    p = tmp_path / "notes.txt"
    p.write_text("hello attachment", encoding="utf-8")
    config = SimpleNamespace(userdata={}, outputs=[])
    fmt = ModernHTMLFormatter(SimpleNamespace(name=None, stream=None), config)
    fmt.feature(_stub_feature())
    fmt.scenario(_stub_scenario())
    fmt.attach_file(str(p))
    att = fmt._collector._pending_attachments[0]
    assert att.text == "hello attachment"
    assert att.data_base64


# ---------------------------------------------------------------------------
# BUG 67: charts.js pie legend used 36px effective spacing for two-line items
#         (labels overlapped at 22px) and listed zero-value slices, overflowing
#         the canvas with many statuses.
# ---------------------------------------------------------------------------


def test_charts_js_pie_legend_filters_zero_and_wraps():
    """Legend must skip zero slices and wrap into columns."""
    from behave_modern_html_report.assets import read_text

    js = read_text("js/charts.js")
    assert "entries" in js and "perCol" in js
    assert "ly +=" not in js


# ---------------------------------------------------------------------------
# BUG 68: the search box promises "steps" but step names were never in any
#         data-* attribute, so searching a step text found nothing.
# ---------------------------------------------------------------------------


def test_search_matches_step_names():
    """Rendered scenarios expose step names via data-steps for search."""
    scenario = Scenario(
        name="S", status="passed", feature_name="F",
        steps=[Step(keyword="Then", name="a very specific step", status="passed")],
    )
    execution = Execution(features=[Feature(name="F", scenarios=[scenario])])
    stats_mod.compute(execution)
    html = Renderer(RenderOptions()).render(execution)
    assert 'data-steps="a very specific step"' in html


# ---------------------------------------------------------------------------
# BUG 69: Behave stores captured stdout/stderr/logging in step.captured, not
#         step.log, so printed output never appeared in the report. A plain
#         string in step.log was also exploded into one log per character.
# ---------------------------------------------------------------------------


def test_step_log_string_not_split_into_chars():
    """A string in behave_step.log is one entry, not one log per char."""
    from behave_modern_html_report.collector import Collector

    collector = Collector()
    behave_step = SimpleNamespace(
        keyword="Then", name="n", status="passed", duration=0.1,
        location="f:1", error_message=None, exception=None, exc_traceback=None,
        table=None, text=None, embeddings=[], log="whole log line",
    )
    step = collector._make_step(behave_step)
    assert step.logs == ["whole log line"]


def test_step_captured_output_included_in_logs():
    """behave_step.captured.output is appended to step.logs."""
    from behave_modern_html_report.collector import Collector

    captured = SimpleNamespace(output="hello stdout\noops stderr")
    behave_step = SimpleNamespace(
        keyword="Then", name="n", status="passed", duration=0.1,
        location="f:1", error_message=None, exception=None, exc_traceback=None,
        table=None, text=None, embeddings=[], log=[], captured=captured,
    )
    step = Collector()._make_step(behave_step)
    assert step.logs == ["hello stdout\noops stderr"]


def test_step_empty_captured_output_adds_nothing():
    """An empty capture produces no phantom log entry."""
    from behave_modern_html_report.collector import Collector

    captured = SimpleNamespace(output="")
    behave_step = SimpleNamespace(
        keyword="Then", name="n", status="passed", duration=0.1,
        location="f:1", error_message=None, exception=None, exc_traceback=None,
        table=None, text=None, embeddings=[], log=[], captured=captured,
    )
    step = Collector()._make_step(behave_step)
    assert step.logs == []


def test_make_error_accepts_preformatted_traceback_string():
    """exc_traceback as a str is used verbatim instead of being dropped."""
    from behave_modern_html_report.collector import Collector

    statement = SimpleNamespace(
        error_message="boom", exception=None,
        exc_traceback="File x.py line 1\nZeroDivisionError",
    )
    err = Collector._make_error(statement)
    assert err is not None
    assert "ZeroDivisionError" in err.traceback


# ---------------------------------------------------------------------------
# BUG 70: attach_* / log helpers only reached the FIRST ModernHTMLFormatter.
#         Running two instances (-f modern-html -o a.html -f modern-html -o
#         b.html) produced one report with attachments and one without, while
#         native context.attach() is broadcast to every formatter.
# ---------------------------------------------------------------------------


def test_attach_helpers_broadcast_to_all_formatters():
    """Every active formatter receives the attachment, not just the first."""
    from unittest.mock import patch

    from behave_modern_html_report.attach import attach_text, log

    received_a: list = []
    received_b: list = []
    logs_b: list = []

    class FakeA:
        def attach(self, att):
            received_a.append(att)

        def log(self, msg):
            pass

    class FakeB:
        def attach(self, att):
            received_b.append(att)

        def log(self, msg):
            logs_b.append(msg)

    with patch(
        "behave_modern_html_report.attach._find_formatters",
        return_value=[FakeA(), FakeB()],
    ):
        attach_text(object(), "hello", name="n.txt")
        log(object(), "msg")

    assert len(received_a) == 1 and len(received_b) == 1
    assert received_a[0] is not received_b[0]  # no aliasing between reports
    assert logs_b == ["msg"]


def test_attach_helpers_noop_without_formatters():
    """Helpers silently no-op when no formatter is active (outside behave)."""
    from behave_modern_html_report.attach import attach_json, attach_text, log

    class Ctx:
        _runner = None

    attach_text(Ctx(), "x")
    attach_json(Ctx(), {"a": 1})
    log(Ctx(), "x")
