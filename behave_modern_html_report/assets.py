"""Asset loading and inlining helpers.

All CSS / JS / fonts shipped with the package can be embedded directly into
the generated single-file HTML report so it works fully offline.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"


@cache
def _read(path: Path) -> str:
    """Read a text file from disk and cache the result.

    Args:
        path (Path): File path to read.

    Returns:
        str: File contents as text.

    """
    return path.read_text(encoding="utf-8")


def read_text(relative: str) -> str:
    """Read a text asset bundled with the package.

    Args:
        relative (str): Asset path relative to the package assets directory.

    Returns:
        str: Asset contents as text.

    """
    return _read(ASSETS_DIR / relative)


def css_bundle(extra: str | None = None) -> str:
    """Return the full CSS bundle for the report.

    Args:
        extra (str | None, optional): User-provided CSS to append.
            Defaults to None.

    Returns:
        str: Combined CSS bundle.

    """
    parts = [read_text("css/report.css")]
    if extra:
        parts.append("\n/* user-provided */\n")
        parts.append(extra)
    return "\n".join(parts)


def js_bundle(extra: str | None = None) -> str:
    """Return the full JS bundle for the report.

    Args:
        extra (str | None, optional): User-provided JS to append.
            Defaults to None.

    Returns:
        str: Combined JS bundle.

    """
    parts = [
        read_text("js/charts.js"),
        read_text("js/report.js"),
    ]
    if extra:
        parts.append("\n/* user-provided */\n")
        parts.append(extra)
    return "\n".join(parts)
