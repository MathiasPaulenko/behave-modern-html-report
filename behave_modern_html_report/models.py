"""Domain models for an execution.

Pure dataclasses. No Behave imports here so the model layer is fully reusable
and can be unit-tested in isolation.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

#: Canonical status names used across the model and the UI.
STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_UNTESTED = "untested"
STATUS_UNDEFINED = "undefined"
STATUS_PENDING = "pending"
STATUS_ERROR = "error"
STATUS_HOOK_ERROR = "hook_error"
STATUS_CLEANUP_ERROR = "cleanup_error"
STATUS_XFAILED = "xfailed"
STATUS_XPASSED = "xpassed"
STATUS_PENDING_WARN = "pending_warn"

ALL_STATUSES = (
    STATUS_PASSED,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STATUS_UNDEFINED,
    STATUS_PENDING,
    STATUS_PENDING_WARN,
    STATUS_UNTESTED,
    STATUS_ERROR,
    STATUS_HOOK_ERROR,
    STATUS_CLEANUP_ERROR,
    STATUS_XFAILED,
    STATUS_XPASSED,
)


def normalize_status(value: Any) -> str:
    """Normalize a Behave status (enum or string) to a canonical lowercase string.

    Args:
        value (Any): Raw status value from Behave.

    Returns:
        str: Canonical lowercase status, or ``untested`` when unknown.

    """
    if value is None:
        return STATUS_UNTESTED
    name = getattr(value, "name", None) or str(value)
    name = name.lower().strip()
    if name in ALL_STATUSES:
        return name
    return STATUS_UNTESTED


# ---------------------------------------------------------------------------
# Leaf models
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Attachment:
    """A file or blob attached to a step or scenario."""

    name: str
    mime_type: str = "application/octet-stream"
    data_base64: str = ""
    text: str | None = None

    @property
    def is_image(self) -> bool:
        """Return True if the attachment is an image."""
        return self.mime_type.startswith("image/")

    @property
    def is_text(self) -> bool:
        """Return True if the attachment is a text-based type."""
        return self.mime_type.startswith("text/") or self.mime_type in {
            "application/json",
            "application/xml",
        }


@dataclass(slots=True)
class ErrorInfo:
    """Captured error information for a failing step."""

    message: str = ""
    traceback: str = ""
    exception_type: str = ""


@dataclass(slots=True)
class DataTable:
    """A Gherkin data table."""

    headings: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Step:
    """A single Gherkin step."""

    keyword: str
    name: str
    status: str = STATUS_UNTESTED
    duration: float = 0.0
    location: str = ""
    text: str | None = None
    table: DataTable | None = None
    error: ErrorInfo | None = None
    attachments: list[Attachment] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Scenario:
    """A scenario or scenario outline example."""

    name: str
    status: str = STATUS_UNTESTED
    duration: float = 0.0
    description: str = ""
    location: str = ""
    tags: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    feature_name: str = ""
    rule_name: str = ""

    @property
    def step_count(self) -> int:
        """Return the number of steps in the scenario."""
        return len(self.steps)


@dataclass(slots=True)
class Feature:
    """A Gherkin feature."""

    name: str
    status: str = STATUS_UNTESTED
    duration: float = 0.0
    description: str = ""
    location: str = ""
    tags: list[str] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)

    @property
    def scenario_count(self) -> int:
        """Return the number of scenarios in the feature."""
        return len(self.scenarios)


# ---------------------------------------------------------------------------
# Environment & statistics
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Environment:
    """Information about the host running the suite."""

    python_version: str = ""
    behave_version: str = ""
    platform: str = ""
    hostname: str = ""
    cwd: str = ""
    command: str = ""
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class Statistics:
    """Aggregate counters and timings."""

    total_features: int = 0
    total_scenarios: int = 0
    total_steps: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    by_tag: dict[str, dict[str, Any]] = field(default_factory=dict)
    duration: float = 0.0
    start_time: datetime | None = None
    end_time: datetime | None = None
    error_count: int = 0
    rule_count: int = 0
    rule_failed_count: int = 0
    total_attachments: int = 0
    total_logs: int = 0
    slowest_step_duration: float = 0.0
    avg_scenario_duration: float = 0.0
    common_exception_type: str = ""

    @property
    def passed(self) -> int:
        """Number of passed scenarios."""
        return self.by_status.get(STATUS_PASSED, 0)

    @property
    def failed(self) -> int:
        """Number of failed scenarios."""
        return self.by_status.get(STATUS_FAILED, 0)

    @property
    def skipped(self) -> int:
        """Number of skipped scenarios."""
        return self.by_status.get(STATUS_SKIPPED, 0)

    @property
    def undefined(self) -> int:
        """Number of undefined scenarios."""
        return self.by_status.get(STATUS_UNDEFINED, 0)

    @property
    def pending(self) -> int:
        """Number of pending scenarios."""
        return self.by_status.get(STATUS_PENDING, 0)

    @property
    def pass_rate(self) -> float:
        """Pass rate as a percentage of total scenarios."""
        total = self.total_scenarios
        return (self.passed / total * 100.0) if total else 0.0


@dataclass(slots=True)
class Execution:
    """Root of the execution tree."""

    title: str = "Behave Modern Report"
    features: list[Feature] = field(default_factory=list)
    environment: Environment = field(default_factory=Environment)
    statistics: Statistics = field(default_factory=Statistics)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def overall_status(self) -> str:
        """Derive the overall execution status from feature statuses."""
        statuses = [f.status for f in self.features]
        if any(s == STATUS_FAILED for s in statuses):
            return STATUS_FAILED
        if statuses and all(s == STATUS_PASSED for s in statuses):
            return STATUS_PASSED
        if any(s == STATUS_UNDEFINED for s in statuses):
            return STATUS_UNDEFINED
        if any(s == STATUS_PENDING for s in statuses):
            return STATUS_PENDING
        if statuses and all(s == STATUS_SKIPPED for s in statuses):
            return STATUS_SKIPPED
        return STATUS_UNTESTED


def as_dict(obj: Any) -> Any:
    """Recursively convert dataclass instances to plain dicts (for JSON).

    Args:
        obj (Any): Dataclass instance, list, dict or primitive value.

    Returns:
        Any: JSON-serializable representation of the input.

    """
    if dataclasses.is_dataclass(obj):
        return {f.name: as_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, list):
        return [as_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: as_dict(v) for k, v in obj.items()}
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
