"""Tests for small utility helpers."""

from behave_modern_html_report.utils import format_duration, guess_mime


def test_format_duration():
    """format_duration returns human-readable strings for various durations."""
    assert format_duration(0.0) == "0ms"
    assert format_duration(0.5) == "500ms"
    assert format_duration(2.5) == "2.50s"
    assert format_duration(75) == "1m 15s"
    assert format_duration(3725).startswith("1h")


def test_guess_mime():
    """guess_mime returns known MIME types and a fallback for unknowns."""
    assert guess_mime("a.png") == "image/png"
    assert guess_mime("a.unknown") == "application/octet-stream"
