"""Tests for execution statistics computation."""

from behave_modern_html_report import statistics as stats_mod


def test_compute_aggregates_counts_and_durations(sample_execution):
    """Compute aggregates feature/scenario/step counts and durations."""
    stats = stats_mod.compute(sample_execution)

    assert stats.total_features == 2
    assert stats.total_scenarios == 4
    assert stats.passed == 2
    assert stats.failed == 1
    assert stats.undefined == 1
    assert stats.skipped == 0
    assert stats.duration >= 0


def test_pass_rate(sample_execution):
    """pass_rate is a percentage between 0 and 100."""
    stats = stats_mod.compute(sample_execution)
    assert 0.0 <= stats.pass_rate <= 100.0


def test_slowest_scenarios(sample_execution):
    """slowest_scenarios returns scenarios ordered by duration descending."""
    stats_mod.compute(sample_execution)
    slow = stats_mod.slowest_scenarios(sample_execution, limit=2)
    assert len(slow) == 2
    assert slow[0].duration >= slow[1].duration


def test_duration_buckets_total_matches_scenarios(sample_execution):
    """duration_buckets groups every scenario into a duration range."""
    stats_mod.compute(sample_execution)
    b = stats_mod.duration_buckets(sample_execution)
    assert sum(b.values()) == 4


def test_by_tag_aggregates(sample_execution):
    """Tags are aggregated per scenario, including feature-level tags."""
    stats_mod.compute(sample_execution)
    assert "smoke" in sample_execution.statistics.by_tag
    assert "happy" in sample_execution.statistics.by_tag
    # smoke has both scenarios (one passed, one failed) -> count 2
    smoke = sample_execution.statistics.by_tag["smoke"]
    assert smoke["count"] == 2
    assert smoke["failed"] == 1
    assert smoke["passed"] == 1


def test_tag_ranking_sorts_failed_first(sample_execution):
    """tag_ranking sorts tags by failures, then count, then duration."""
    stats_mod.compute(sample_execution)
    ranking = stats_mod.tag_ranking(sample_execution)
    # smoke (feature tag) has 2 scenarios, 1 failed; payment has 1 failed scenario.
    # Both have failed=1, so smoke wins on count.
    assert ranking[0]["name"] == "smoke"
    assert ranking[1]["name"] == "payment"


def test_error_statuses_derive_feature_status(sample_execution):
    """error, hook_error and cleanup_error are treated as failed for the feature status."""
    sample_execution.features[0].scenarios[0].status = "error"
    stats = stats_mod.compute(sample_execution)
    assert sample_execution.features[0].status == "failed"
    assert stats.by_status["error"] >= 1


def test_tag_stats_count_all_statuses():
    """Tag counters include all Behave 1.3.x statuses, not just the original five."""
    from behave_modern_html_report.models import Execution, Feature, Scenario, Statistics

    execution = Execution(
        statistics=Statistics(),
        features=[
            Feature(
                name="F",
                tags=["regression"],
                scenarios=[
                    Scenario(name="S1", status="hook_error", tags=["regression"]),
                    Scenario(name="S2", status="cleanup_error", tags=["regression"]),
                    Scenario(name="S3", status="xpassed", tags=["regression"]),
                ],
            )
        ],
    )
    stats = stats_mod.compute(execution)
    tag_data = stats.by_tag["regression"]
    assert tag_data["hook_error"] == 1
    assert tag_data["cleanup_error"] == 1
    assert tag_data["xpassed"] == 1
