"""Tests for the high-level attachment helpers."""

from __future__ import annotations

from types import SimpleNamespace

from behave_modern_html_report import attach_file, attach_json, attach_screenshot, attach_text, log
from behave_modern_html_report.models import Attachment


class _FakeFormatter:
    """In-memory formatter stub for attachment helper tests."""

    def __init__(self):
        self.last_attachment: Attachment | None = None
        self.logs: list[str] = []

    def attach(self, att: Attachment) -> None:
        """Record the last attached object."""
        self.last_attachment = att

    def log(self, msg: str) -> None:
        """Record a log message."""
        self.logs.append(msg)


def _make_context(fmt: _FakeFormatter | None = None):
    """Build a minimal Behave-like context wrapping the formatter stub."""
    runner = SimpleNamespace(formatters=[fmt] if fmt else [])
    return SimpleNamespace(_runner=runner)


def test_attach_text_finds_formatter():
    """attach_text creates a plain text attachment on the current step."""
    fmt = _FakeFormatter()
    attach_text(_make_context(fmt), "hello", "note.txt")
    assert fmt.last_attachment is not None
    assert fmt.last_attachment.name == "note.txt"
    assert fmt.last_attachment.text == "hello"
    assert fmt.last_attachment.mime_type == "text/plain"


def test_attach_json_serializes_data():
    """attach_json serializes the payload and sets the JSON MIME type."""
    fmt = _FakeFormatter()
    attach_json(_make_context(fmt), {"x": 1}, "payload.json")
    assert fmt.last_attachment.name == "payload.json"
    assert '"x": 1' in fmt.last_attachment.text
    assert fmt.last_attachment.mime_type == "application/json"


def test_attach_file(tmp_path):
    """attach_file reads a file from disk and base64-encodes it."""
    fmt = _FakeFormatter()
    p = tmp_path / "data.bin"
    p.write_bytes(b"abc")
    attach_file(_make_context(fmt), str(p))
    assert fmt.last_attachment is not None
    assert fmt.last_attachment.name == "data.bin"
    assert fmt.last_attachment.data_base64 == "YWJj"


def test_attach_screenshot_bytes():
    """attach_screenshot accepts raw bytes as PNG data."""
    fmt = _FakeFormatter()
    attach_screenshot(_make_context(fmt), b"\x89PNG\r\n\x1a\n", "shot.png")
    assert fmt.last_attachment.name == "shot.png"
    assert fmt.last_attachment.mime_type == "image/png"
    assert fmt.last_attachment.data_base64


def test_log_appends_message():
    """Log appends a message to the current step."""
    fmt = _FakeFormatter()
    log(_make_context(fmt), "checkpoint alpha")
    assert fmt.logs == ["checkpoint alpha"]


def test_helpers_noop_when_formatter_missing():
    """Attachment helpers must not raise when the formatter is unavailable."""
    attach_text(SimpleNamespace(_runner=None), "text", "n.txt")
    attach_file(SimpleNamespace(_runner=SimpleNamespace(formatters=[])), "nope")
    log(SimpleNamespace(_runner=SimpleNamespace(formatters=[object()])), "msg")
