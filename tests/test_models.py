"""Tests for the domain models and utilities."""

from behave_modern_html_report import statistics as stats_mod
from behave_modern_html_report.models import (
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_UNTESTED,
    as_dict,
    normalize_status,
)


def test_normalize_status_handles_strings_and_enums():
    """normalize_status converts strings, enums and unknown values safely."""
    class E:
        name = "PASSED"
    assert normalize_status("passed") == "passed"
    assert normalize_status("FAILED") == "failed"
    assert normalize_status(E()) == "passed"
    assert normalize_status(None) == STATUS_UNTESTED
    assert normalize_status("garbage") == STATUS_UNTESTED


def test_overall_status(sample_execution):
    """Overall status is failed when any scenario failed."""
    stats_mod.compute(sample_execution)
    assert sample_execution.overall_status == STATUS_FAILED


def test_overall_status_passed_when_all_passed(sample_execution):
    """Overall status is passed when all scenarios passed."""
    for f in sample_execution.features:
        for s in f.scenarios:
            s.status = STATUS_PASSED
            for st in s.steps:
                st.status = STATUS_PASSED
    stats_mod.compute(sample_execution)
    assert sample_execution.overall_status == STATUS_PASSED


def test_as_dict_is_json_safe(sample_execution):
    """as_dict recursively converts dataclasses into JSON-safe structures."""
    d = as_dict(sample_execution)
    assert d["title"] == "Sample Suite"
    assert isinstance(d["features"], list)
    assert d["features"][0]["scenarios"][0]["steps"][0]["keyword"] == "Given"


def test_package_version():
    """The package exposes the expected version and public API."""
    import behave_modern_html_report as bmr

    assert bmr.__version__ == "1.0.0"
    assert "attach_screenshot" in bmr.__all__
