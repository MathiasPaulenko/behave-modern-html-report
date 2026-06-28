from behave_modern_report import statistics as stats_mod


def test_compute_aggregates_counts_and_durations(sample_execution):
    stats = stats_mod.compute(sample_execution)

    assert stats.total_features == 2
    assert stats.total_scenarios == 4
    assert stats.passed == 2
    assert stats.failed == 1
    assert stats.undefined == 1
    assert stats.skipped == 0
    assert stats.duration >= 0


def test_pass_rate(sample_execution):
    stats = stats_mod.compute(sample_execution)
    assert 0.0 <= stats.pass_rate <= 100.0


def test_slowest_scenarios(sample_execution):
    stats_mod.compute(sample_execution)
    slow = stats_mod.slowest_scenarios(sample_execution, limit=2)
    assert len(slow) == 2
    assert slow[0].duration >= slow[1].duration


def test_duration_buckets_total_matches_scenarios(sample_execution):
    stats_mod.compute(sample_execution)
    b = stats_mod.duration_buckets(sample_execution)
    assert sum(b.values()) == 4
