"""Collector tests using simple stubs (no Behave required)."""

from __future__ import annotations

from types import SimpleNamespace

from behave_modern_html_report.collector import Collector
from behave_modern_html_report.models import Attachment


def _feature(name, tags=()):
    """Return a minimal Behave-like feature stub."""
    return SimpleNamespace(
        name=name, description=["A feature"], location=f"{name}.feature:1",
        tags=list(tags), status="passed", duration=0.0,
    )


def _scenario(name, tags=()):
    """Return a minimal Behave-like scenario stub."""
    return SimpleNamespace(
        name=name, description=[], location=f"{name}.feature:3",
        tags=list(tags), status="passed", duration=0.0,
    )


def _rule(name):
    """Return a minimal Behave-like rule stub."""
    return SimpleNamespace(name=name, description=[], location=f"{name}.feature:2")


def _background(name="Setup", steps=()):
    """Return a minimal Behave-like background stub."""
    return SimpleNamespace(
        name=name, keyword="Background", location=f"{name}.feature:2",
        steps=list(steps),
    )


def _step(keyword, name, status="passed", duration=0.01, error=None):
    """Return a minimal Behave-like step stub."""
    return SimpleNamespace(
        keyword=keyword, name=name, status=status, duration=duration,
        location=f"{name}.py:1", text=None, table=None,
        error_message=error or "", exception=None, exc_traceback="",
    )


def test_collector_builds_tree():
    """The collector builds a feature/scenario/step tree and aggregates counts."""
    c = Collector(title="X")
    c.start_feature(_feature("F"))
    c.start_scenario(_scenario("S", tags=["smoke"]))
    c.add_step(_step("Given", "a thing"))
    c.add_step(_step("Then", "ok", status="passed", duration=0.5))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.51))
    c.end_feature(SimpleNamespace(status="passed", duration=0.51))

    execution = c.finalize()
    assert execution.title == "X"
    assert execution.statistics.total_features == 1
    assert execution.statistics.total_scenarios == 1
    assert execution.statistics.total_steps == 2
    assert execution.statistics.passed == 1


def test_collector_captures_error():
    """The collector captures step error details."""
    c = Collector()
    c.start_feature(_feature("F"))
    c.start_scenario(_scenario("S"))
    c.add_step(_step("When", "boom", status="failed", error="kaboom"))
    c.end_scenario(SimpleNamespace(status="failed", duration=0.0))
    c.end_feature(SimpleNamespace(status="failed", duration=0.0))
    execution = c.finalize()

    step = execution.features[0].scenarios[0].steps[0]
    assert step.error is not None
    assert "kaboom" in step.error.message


def test_collector_attach_and_log():
    """The collector records attachments and log lines on the current step."""
    c = Collector()
    c.start_feature(_feature("F"))
    c.start_scenario(_scenario("S"))
    c.add_step(_step("Given", "x"))
    c.attach(Attachment(name="note.txt", mime_type="text/plain", text="hi"))
    c.log("hello world")

    step = c._current_scenario.steps[-1]  # noqa: SLF001
    assert step.attachments[0].text == "hi"
    assert step.logs == ["hello world"]


def test_collector_tracks_rule_name():
    """The collector records the rule name for scenarios under a Gherkin v6 rule."""
    c = Collector()
    c.start_feature(_feature("F"))
    c.start_rule(_rule("R1"))
    c.start_scenario(_scenario("S1"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.start_scenario(_scenario("S2"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.end_rule()
    c.end_feature(SimpleNamespace(status="passed", duration=0.0))

    execution = c.finalize()
    feature = execution.features[0]
    assert feature.scenarios[0].rule_name == "R1"
    assert feature.scenarios[1].rule_name == "R1"


def test_collector_resets_rule_after_feature():
    """The current rule is cleared when a feature ends."""
    c = Collector()
    c.start_feature(_feature("F1"))
    c.start_rule(_rule("R1"))
    c.start_scenario(_scenario("S1"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.end_feature(SimpleNamespace(status="passed", duration=0.0))

    c.start_feature(_feature("F2"))
    c.start_scenario(_scenario("S2"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.end_feature(SimpleNamespace(status="passed", duration=0.0))

    execution = c.finalize()
    assert execution.features[0].scenarios[0].rule_name == "R1"
    assert execution.features[1].scenarios[0].rule_name == ""


def test_collector_normalizes_extended_statuses():
    """The collector normalizes Behave 1.3.x extended statuses to canonical names."""
    c = Collector()
    c.start_feature(_feature("F"))
    for status in ("error", "hook_error", "cleanup_error", "xfailed"):
        c.start_scenario(_scenario(f"S-{status}"))
        c.end_scenario(SimpleNamespace(status=status, duration=0.0))
    c.end_feature(SimpleNamespace(status="failed", duration=0.0))

    execution = c.finalize()
    statuses = [s.status for s in execution.features[0].scenarios]
    assert "error" in statuses
    assert "hook_error" in statuses
    assert "cleanup_error" in statuses
    assert "xfailed" in statuses
    assert execution.features[0].status == "failed"


def test_collector_captures_feature_background():
    """The collector records feature background and attaches it to each scenario."""
    c = Collector()
    c.start_feature(
        SimpleNamespace(
            name="F", description=["A feature"], location="F.feature:1",
            tags=[], status="passed", duration=0.0,
            background=_background("Reset db", steps=[_step("Given", "db reset")]),
        )
    )
    c.start_scenario(_scenario("S"))
    c.add_step(_step("When", "x"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.end_feature(SimpleNamespace(status="passed", duration=0.0))

    execution = c.finalize()
    assert execution.features[0].background is not None
    assert len(execution.features[0].background.steps) == 1
    assert execution.features[0].scenarios[0].background is execution.features[0].background


def test_collector_captures_environment():
    """The collector captures host and runtime environment details."""
    c = Collector()
    env = c.execution.environment
    assert env.python_version
    assert env.platform
    assert env.hostname
    assert env.cpu_count >= 0


def test_collector_captures_scenario_outline():
    """The collector detects scenario outlines and captures their examples table."""
    c = Collector()
    c.start_feature(_feature("F"))
    examples = SimpleNamespace(
        tables=[
            SimpleNamespace(
                headings=["username", "password"],
                rows=[
                    SimpleNamespace(cells=["alice", "secret1"]),
                    SimpleNamespace(cells=["bob", "secret2"]),
                ],
            ),
        ],
    )
    c.start_scenario(
        SimpleNamespace(
            name="Example 1", description=[], location="F.feature:4",
            tags=[], status="passed", duration=0.0,
            type="scenario_outline", outline_name="Login flow", examples=examples,
        )
    )
    c.add_step(_step("Given", "user logs in"))
    c.end_scenario(SimpleNamespace(status="passed", duration=0.0))
    c.end_feature(SimpleNamespace(status="passed", duration=0.0))

    execution = c.finalize()
    scenario = execution.features[0].scenarios[0]
    assert scenario.is_outline
    assert scenario.outline_name == "Login flow"
    assert scenario.examples.headings == ["username", "password"]
    assert scenario.examples.rows == [["alice", "secret1"], ["bob", "secret2"]]
