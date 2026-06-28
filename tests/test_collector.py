"""Collector tests using simple stubs (no Behave required)."""

from __future__ import annotations

from types import SimpleNamespace

from behave_modern_report.collector import Collector
from behave_modern_report.models import Attachment


def _feature(name, tags=()):
    return SimpleNamespace(
        name=name, description=["A feature"], location=f"{name}.feature:1",
        tags=list(tags), status="passed", duration=0.0,
    )


def _scenario(name, tags=()):
    return SimpleNamespace(
        name=name, description=[], location=f"{name}.feature:3",
        tags=list(tags), status="passed", duration=0.0,
    )


def _step(keyword, name, status="passed", duration=0.01, error=None):
    return SimpleNamespace(
        keyword=keyword, name=name, status=status, duration=duration,
        location=f"{name}.py:1", text=None, table=None,
        error_message=error or "", exception=None, exc_traceback="",
    )


def test_collector_builds_tree():
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
    c = Collector()
    c.start_feature(_feature("F"))
    c.start_scenario(_scenario("S"))
    c.add_step(_step("Given", "x"))
    c.attach(Attachment(name="note.txt", mime_type="text/plain", text="hi"))
    c.log("hello world")

    step = c._current_scenario.steps[-1]  # noqa: SLF001
    assert step.attachments[0].text == "hi"
    assert step.logs == ["hello world"]
