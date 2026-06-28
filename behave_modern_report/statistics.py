"""Aggregate statistics computation."""

from __future__ import annotations

from .models import (
    ALL_STATUSES,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_PENDING,
    STATUS_SKIPPED,
    STATUS_UNDEFINED,
    Execution,
    Feature,
    Scenario,
    Statistics,
)


def _derive_feature_status(feature: Feature) -> str:
    statuses = [s.status for s in feature.scenarios]
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
    return statuses[0] if statuses else "untested"


def _scenario_duration(scenario: Scenario) -> float:
    if scenario.duration:
        return scenario.duration
    return sum(step.duration or 0.0 for step in scenario.steps)


def compute(execution: Execution) -> Statistics:
    """Recompute statistics and propagate durations / statuses."""
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
    """Return the slowest scenarios across the whole execution."""
    all_scenarios = [s for f in execution.features for s in f.scenarios]
    return sorted(all_scenarios, key=lambda s: s.duration, reverse=True)[:limit]


def duration_buckets(execution: Execution) -> dict[str, int]:
    """Group scenarios into duration buckets for the histogram chart."""
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
