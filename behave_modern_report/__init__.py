"""Behave Modern Report.

The modern, beautiful, single-file HTML report formatter for Behave.

Public API:
    ModernHTMLFormatter -- the Behave entry point.
    Renderer           -- standalone renderer (Behave-independent).
    Collector          -- builds an execution model from formatter events.
    models             -- dataclasses representing the execution tree.
"""

from __future__ import annotations

from .collector import Collector
from .formatter import ModernHTMLFormatter
from .renderer import Renderer

__all__ = ["ModernHTMLFormatter", "Renderer", "Collector", "__version__"]

__version__ = "0.1.0"
