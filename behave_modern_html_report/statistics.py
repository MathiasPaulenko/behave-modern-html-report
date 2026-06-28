"""Aggregate statistics computation."""

from __future__ import annotations

from typing import Any

from .models import (
    ALL_STATUSES,
    STATUS_CLEANUP_ERROR,
    STATUS_ERROR,
    STATUS_FAILED,
    STATUS_HOOK_ERROR,
    STATUS_PASSED,
    STATUS_PENDING,
    STATUS_SKIPPED,
    STATUS_UNDEFINED,
    STATUS_UNTESTED,
    STATUS_XFAILED,
    Execution,
    Feature,
    Scenario,
    Statistics,
)

_FAILED_STATUSES = (
    STATUS_FAILED,
    STATUS_ERROR,
    STATUS_HOOK_ERROR,
    STATUS_CLEANUP_ERROR,
    STATUS_XFAILED,
)


def _derive_feature_status(feature: Feature) -> str:
    """Derive a feature's overall status from its scenario statuses.

    Args:
        feature (Feature): Feature to evaluate.

    Returns:
        str: Canonical status derived from the feature's scenarios.

    """
    statuses = [s.status for s in feature.scenarios]
    if any(s in _FAILED_STATUSES for s in statuses):
        return STATUS_FAILED
    if statuses and all(s == STATUS_PASSED for s in statuses):
        return STATUS_PASSED
    if any(s == STATUS_UNDEFINED for s in statuses):
        return STATUS_UNDEFINED
    if any(s == STATUS_PENDING for s in statuses):
        return STATUS_PENDING
    if statuses and all(s == STATUS_SKIPPED for s in statuses):
        return STATUS_SKIPPED
    return statuses[0] if statuses else STATUS_UNTESTED


def _tag_stats() -> dict[str, Any]:
    """Return a fresh counters dict for a single tag."""
    stats = {"count": 0, "duration": 0.0}
    stats.update(dict.fromkeys(ALL_STATUSES, 0))
    return stats


def _failed_count(data: dict[str, Any]) -> int:
    """Return the total number of failure-like statuses in a counter dict."""
    return sum(data.get(status, 0) for status in _FAILED_STATUSES)


def _scenario_duration(scenario: Scenario) -> float:
    """Return the total duration of a scenario.

    Uses the scenario's own duration when available, otherwise sums its steps.

    Args:
        scenario (Scenario): Scenario to measure.

    Returns:
        float: Total duration in seconds.

    """
    if scenario.duration:
        return scenario.duration
    return sum(step.duration or 0.0 for step in scenario.steps)


def compute(execution: Execution) -> Statistics:
    """Recompute statistics and propagate durations / statuses.

    Args:
        execution (Execution): Execution tree to analyse.

    Returns:
        Statistics: Updated statistics object, also assigned to the execution.

    """
    stats = Statistics(by_status=dict.fromkeys(ALL_STATUSES, 0))

    for feature in execution.features:
        stats.total_features += 1
        feature_duration = 0.0

        for scenario in feature.scenarios:
            stats.total_scenarios += 1
            scenario.duration = _scenario_duration(scenario)
            feature_duration += scenario.duration
            stats.by_status[scenario.status] = stats.by_status.get(scenario.status, 0) + 1
            stats.total_steps += len(scenario.steps)

            for tag in set(scenario.tags) | set(feature.tags):
                tag_data = stats.by_tag.setdefault(tag, _tag_stats())
                tag_data["count"] += 1
                tag_data["duration"] += scenario.duration
                if scenario.status in tag_data:
                    tag_data[scenario.status] += 1

        feature.duration = feature_duration
        feature.status = _derive_feature_status(feature)
        stats.duration += feature_duration

    if execution.statistics.start_time:
        stats.start_time = execution.statistics.start_time
    if execution.statistics.end_time:
        stats.end_time = execution.statistics.end_time
    if stats.start_time and stats.end_time:
        stats.duration = max(
            stats.duration, (stats.end_time - stats.start_time).total_seconds()
        )

    execution.statistics = stats
    return stats


def slowest_scenarios(execution: Execution, limit: int = 10) -> list[Scenario]:
    """Return the slowest scenarios across the whole execution.

    Args:
        execution (Execution): Execution tree to analyse.
        limit (int, optional): Maximum number of scenarios to return.
            Defaults to 10.

    Returns:
        list[Scenario]: Scenarios ordered by duration descending.

    """
    all_scenarios = [s for f in execution.features for s in f.scenarios]
    return sorted(all_scenarios, key=lambda s: s.duration, reverse=True)[:limit]


def tag_ranking(execution: Execution) -> list[dict[str, Any]]:
    """Return tags sorted by failures, then count, then duration.

    Args:
        execution (Execution): Execution tree to analyse.

    Returns:
        list[dict[str, Any]]: Tag rows with counts, statuses and pass rate.

    """
    stats = execution.statistics.by_tag
    rows = []
    for name, data in stats.items():
        count = data["count"]
        passed = data["passed"]
        failed = _failed_count(data)
        duration = data["duration"]
        pass_rate = (passed / count * 100.0) if count else 0.0
        rows.append(
            {
                "name": name,
                "count": count,
                "passed": passed,
                "failed": failed,
                "skipped": data["skipped"],
                "undefined": data["undefined"],
                "pending": data["pending"],
                "error": data["error"],
                "duration": duration,
                "pass_rate": pass_rate,
            }
        )
    return sorted(rows, key=lambda r: (-r["failed"], -r["count"], r["duration"]), reverse=False)


def duration_buckets(execution: Execution) -> dict[str, int]:
    """Group scenarios into duration buckets for the histogram chart.

    Args:
        execution (Execution): Execution tree to analyse.

    Returns:
        dict[str, int]: Mapping of bucket labels to scenario counts.

    """
    buckets = {
        "<100ms": 0,
        "100ms-500ms": 0,
        "500ms-1s": 0,
        "1s-5s": 0,
        "5s-30s": 0,
        ">30s": 0,
    }
    for feature in execution.features:
        for scenario in feature.scenarios:
            d = scenario.duration
            if d < 0.1:
                buckets["<100ms"] += 1
            elif d < 0.5:
                buckets["100ms-500ms"] += 1
            elif d < 1.0:
                buckets["500ms-1s"] += 1
            elif d < 5.0:
                buckets["1s-5s"] += 1
            elif d < 30.0:
                buckets["5s-30s"] += 1
            else:
                buckets[">30s"] += 1
    return buckets
