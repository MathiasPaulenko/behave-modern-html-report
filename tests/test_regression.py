"""Regression tests for bugs discovered during the complete audit."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from behave_modern_html_report import statistics as stats_mod
from behave_modern_html_report.formatter import ModernHTMLFormatter, _read_optional
from behave_modern_html_report.models import (
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
    assert "<!doctype html>" in mock_stream.content


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
        keyword="Then", name="assertion fails", status="failed", duration=0.1,
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
        name = "output/steps.html"
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
    assert 'try {' in js and 'DATA.default_view' in js
    # Verify the try/catch is near the default_view logic
    idx = js.index('DATA.default_view')
    surrounding = js[max(0, idx - 100):idx + 200]
    assert 'try' in surrounding or 'catch' in surrounding


# ---------------------------------------------------------------------------
# BUG 23: charts.js formatDuration didn't handle negative values, unlike
#         the Python format_duration which was already fixed.
# ---------------------------------------------------------------------------

def test_charts_js_format_duration_negative():
    """charts.js formatDuration should handle negative/null values."""
    from behave_modern_html_report.assets import read_text
    js = read_text("js/charts.js")
    assert 's < 0' in js or 's == null' in js


# ---------------------------------------------------------------------------
# BUG 24: charts.js roundRect could produce negative radius via arcTo
#         when width or height is zero/negative, causing IndexSizeError.
#         Fixed by clamping w/h to >= 0 and r to >= 0, with rect fallback.
# ---------------------------------------------------------------------------

def test_charts_js_round_rect_clamped():
    """charts.js roundRect should clamp width/height/radius to >= 0."""
    from behave_modern_html_report.assets import read_text
    js = read_text("js/charts.js")
    assert 'Math.max(w, 0)' in js
    assert 'Math.max(0' in js


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
    template = Path(__file__).resolve().parent.parent / "behave_modern_html_report" / "templates" / "step_catalog.html.jinja"
    content = template.read_text(encoding="utf-8")
    assert "try" in content and "JSON.parse" in content
    idx = content.index("JSON.parse")
    surrounding = content[max(0, idx - 100):idx + 200]
    assert "try" in surrounding or "catch" in surrounding


# ---------------------------------------------------------------------------
# BUG 31: step_catalog.html.jinja window.matchMedia call was unguarded,
#         could crash in browsers without matchMedia support.
# ---------------------------------------------------------------------------

def test_step_catalog_matchmedia_guarded():
    """step_catalog template should guard window.matchMedia with &&."""
    from pathlib import Path
    template = Path(__file__).resolve().parent.parent / "behave_modern_html_report" / "templates" / "step_catalog.html.jinja"
    content = template.read_text(encoding="utf-8")
    assert "window.matchMedia &&" in content


# ---------------------------------------------------------------------------
# BUG 32: json.dumps in renderer.py didn't escape < and >, allowing XSS
#         via crafted scenario/step names containing </script> tags.
# ---------------------------------------------------------------------------

def test_json_data_escaped_for_xss():
    """JSON data embedded in script tag should have < and > escaped."""
    from behave_modern_html_report.models import STATUS_PASSED
    xss_step = Step(keyword="Given", name='</script><script>alert(1)</script>', status=STATUS_PASSED)
    xss_scenario = Scenario(name='</script><script>alert(1)</script>', status=STATUS_PASSED, steps=[xss_step])
    xss_feature = Feature(name='</script><script>alert(1)</script>', scenarios=[xss_scenario])
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
    surrounding = js[idx:idx + 300]
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

    with patch("behave_modern_html_report.attach._find_formatter", return_value=FakeFormatter()), \
         pytest.raises(OSError, match="Cannot read screenshot file"):
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
    surrounding = js[idx:idx + 200]
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

    with patch("behave_modern_html_report.attach._find_formatter", return_value=FakeFormatter()), \
         pytest.raises(OSError, match="Cannot read attachment file"):
        attach_file(FakeContext(), "nonexistent_file.txt")


# ---------------------------------------------------------------------------
# BUG 39: _derive_feature_status didn't handle xfailed/xpassed statuses,
#         falling through to unreliable statuses[0] return.
# ---------------------------------------------------------------------------

def test_derive_feature_status_xfailed():
    """_derive_feature_status should return 'passed' for all-xfailed features."""
    from behave_modern_html_report.models import STATUS_XFAILED, Feature, Scenario
    from behave_modern_html_report.statistics import _derive_feature_status
    feature = Feature(name="test", scenarios=[
        Scenario(name="s1", status=STATUS_XFAILED),
        Scenario(name="s2", status=STATUS_XFAILED),
    ])
    assert _derive_feature_status(feature) == "passed"


def test_derive_feature_status_xpassed():
    """_derive_feature_status should return 'passed' for xpassed scenarios."""
    from behave_modern_html_report.models import STATUS_XPASSED, Feature, Scenario
    from behave_modern_html_report.statistics import _derive_feature_status
    feature = Feature(name="test", scenarios=[
        Scenario(name="s1", status=STATUS_XPASSED),
    ])
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
    collector.start_feature(type("F", (), {"name": "f", "description": [], "location": "", "tags": [], "background": None})())
    collector.start_scenario(type("S", (), {"name": "s", "description": [], "location": "", "tags": [], "type": "scenario", "examples": None})())
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
    collector.start_feature(type("F", (), {"name": "f", "description": [], "location": "", "tags": [], "background": None})())
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
