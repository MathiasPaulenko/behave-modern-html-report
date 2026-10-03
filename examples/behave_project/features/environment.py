"""Environment hooks for the example Behave project."""

import json
import os

from behave_modern_html_report import attach_text, log


def before_all(context):
    """Store extra data available to steps via context.config.userdata.

    Note: ``bmr.*`` formatter options must be set in ``behave.ini`` — the
    formatter reads userdata when it is instantiated, before ``before_all``.
    """
    context.config.userdata["example.env"] = "demo"


def before_scenario(_context, scenario):
    """Skip or mark pending scenarios based on tags for the demo."""
    if "skip" in scenario.tags:
        scenario.skip("Scenario tagged with @skip")
    elif "pending" in scenario.tags:
        scenario.skip("Scenario tagged with @pending")


def after_step(context, step):
    """Attach a failure log when a step fails."""
    if step.status == "failed":
        attach_text(
            context,
            f"Step failed: {step.name}\nStatus: {step.status}\nDuration: {step.duration:.3f}s",
            name="failure-log.txt",
        )
        # Behave's native embedding path (formatter.embedding) also works.
        context.attach("text/plain", f"Failed step: {step.name}".encode())
        log(context, f"Step failed at {step.location}")


def after_all(context):
    """Write a summary JSON sidecar for debugging."""
    features = getattr(getattr(context, "_runner", None), "features", None) or []
    scenarios = [s for f in features for s in f.walk_scenarios()]
    summary = {
        "features": len(features),
        "scenarios": len(scenarios),
        "failed": sum(1 for s in scenarios if s.status == "failed"),
    }
    path = os.path.join(os.path.dirname(__file__), "..", "summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
