"""High-level attachment helpers for Behave environment.py hooks.

These functions are the recommended way to attach screenshots, files, text
or log messages to the current step. They automatically find the active
``ModernHTMLFormatter`` on the Behave context and delegate to it.

Usage in ``environment.py``::

    from behave_modern_html_report import attach_screenshot, log

    def after_step(context, step):
        if step.status == "failed":
            attach_screenshot(context, name="failure.png")
            log(f"URL at failure: {getattr(context, 'url', 'unknown')}")

The helpers are intentionally tolerant to import-time behaviour: the project can
still be installed/tested without Behave being present.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

from .models import Attachment
from .utils import guess_mime


def _find_formatter(context: Any) -> Any:
    """Locate the ModernHTMLFormatter instance on the Behave context.

    Args:
        context (Any): Behave context object passed to the hook.

    Returns:
        Any: The formatter instance, or None if it is not available
            (e.g. outside Behave).

    """
    if context is None:
        return None
    # Behave 1.2.x / 1.3.x keeps the runner and formatters here.
    runner = getattr(context, "_runner", None)
    if runner is None:
        return None
    formatters = getattr(runner, "formatters", None)
    if not formatters:
        return None
    # Duck-type search: we look for the formatter that has the attach() API.
    for fmt in formatters:
        if hasattr(fmt, "attach") and hasattr(fmt, "log"):
            return fmt
    return None


def attach_file(context: Any, path: str | Path, name: str | None = None) -> None:
    """Attach a file from disk to the current step.

    Args:
        context (Any): Behave context object passed to the hook.
        path (str | Path): Path to the file to attach.
        name (str | None, optional): Optional display name. If omitted, the file
            name is used.

    """
    formatter = _find_formatter(context)
    if formatter is None:
        return
    p = Path(path)
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    mime = guess_mime(p.name)
    formatter.attach(
        Attachment(name=name or p.name, mime_type=mime, data_base64=data)
    )


def attach_text(context: Any, text: str, name: str = "note.txt") -> None:
    """Attach a plain text snippet to the current step.

    Args:
        context (Any): Behave context object passed to the hook.
        text (str): Raw text to embed.
        name (str, optional): Display name for the attachment. Defaults to
            ``note.txt``.

    """
    formatter = _find_formatter(context)
    if formatter is None:
        return
    formatter.attach(
        Attachment(name=name, mime_type="text/plain", text=str(text))
    )


def attach_json(context: Any, data: Any, name: str = "data.json") -> None:
    """Attach a JSON-serializable object to the current step.

    Args:
        context (Any): Behave context object passed to the hook.
        data (Any): Any object that can be passed to ``json.dumps``.
        name (str, optional): Display name for the attachment. Defaults to
            ``data.json``.

    """
    import json

    formatter = _find_formatter(context)
    if formatter is None:
        return
    formatter.attach(
        Attachment(name=name, mime_type="application/json", text=json.dumps(data, indent=2, default=str))
    )


def attach_screenshot(context: Any, source: Any, name: str = "screenshot.png") -> None:
    """Attach a screenshot to the current step.

    The ``source`` argument can be:

    - ``bytes`` or ``bytearray`` -> used as raw PNG data.
    - A path-like string -> read from disk.
    - A Selenium WebDriver instance -> ``driver.get_screenshot_as_png()`` is called.
    - A Playwright Page instance -> ``page.screenshot()`` is called.
    - A PIL Image -> saved to a PNG buffer.

    Args:
        context (Any): Behave context object passed to the hook.
        source (Any): Screenshot source (see above).
        name (str, optional): Display name for the attachment. Defaults to
            ``screenshot.png``.

    """
    formatter = _find_formatter(context)
    if formatter is None:
        return

    data: bytes | None = None

    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
    elif isinstance(source, (str, Path)):
        data = Path(source).read_bytes()
    else:
        # Selenium WebDriver
        method = getattr(source, "get_screenshot_as_png", None)
        if callable(method):
            data = method()
        # Playwright Page
        if data is None:
            method = getattr(source, "screenshot", None)
            if callable(method):
                data = method()
        # PIL Image
        if data is None:
            save = getattr(source, "save", None)
            if callable(save):
                import io

                buf = io.BytesIO()
                save(buf, format="PNG")
                data = buf.getvalue()

    if data is None:
        return

    mime = "image/png"
    if name.lower().endswith(".jpg") or name.lower().endswith(".jpeg"):
        mime = "image/jpeg"
    elif name.lower().endswith(".webp"):
        mime = "image/webp"
    elif name.lower().endswith(".gif"):
        mime = "image/gif"
    else:
        mime = mimetypes.guess_type(name)[0] or "image/png"

    formatter.attach(
        Attachment(name=name, mime_type=mime, data_base64=base64.b64encode(data).decode("ascii"))
    )


def log(context: Any, message: str) -> None:
    """Append a text log line to the current step.

    Args:
        context (Any): Behave context object passed to the hook.
        message (str): Free-form text line to attach.

    """
    formatter = _find_formatter(context)
    if formatter is None:
        return
    formatter.log(str(message))
