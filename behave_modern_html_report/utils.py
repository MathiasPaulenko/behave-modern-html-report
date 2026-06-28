"""Small utility helpers used across the package."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string."""
    if seconds is None:
        return "0ms"
    if seconds < 1.0:
        return f"{int(seconds * 1000)}ms"
    if seconds < 60.0:
        return f"{seconds:.2f}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {int(secs)}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {int(secs)}s"


def guess_mime(path: str | Path) -> str:
    """Guess the MIME type of a file path, falling back to octet-stream."""
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def file_to_base64(path: str | Path) -> str:
    """Read a file and return its base64-encoded content."""
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def safe_str(value: object) -> str:
    """Return a printable string for arbitrary values, never raising."""
    try:
        return str(value)
    except Exception:  # pragma: no cover - defensive
        return repr(value)
