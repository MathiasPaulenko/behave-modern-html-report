"""Environment hooks for the example Behave project."""

import json
import os


def before_all(context):
    """Add custom BMR userdata and report options."""
    context.config.userdata.set("bmr.title", "Behave Project Example")
    context.config.userdata.set("bmr.company", "Open Source")
    context.config.userdata.set("bmr.theme", "auto")


def before_scenario(_context, scenario):
    """Skip or mark pending scenarios based on tags for the demo."""
    if "skip" in scenario.tags:
        scenario.skip("Scenario tagged with @skip")
    elif "pending" in scenario.tags:
        scenario.skip("Scenario tagged with @pending")


def after_step(context, step):
    """Attach a failure log when a step fails."""
    if step.status == "failed":
        context.attach(
            mime_type="text/plain",
            data=f"Step failed: {step.name}\nStatus: {step.status}\nDuration: {step.duration:.3f}s".encode(),
            name="failure-log.txt",
        )


def after_all(_context):
    """Write a summary JSON sidecar for debugging."""
    summary = {
        "features": len(_context.features),
        "status": str(_context.failed),
    }
    path = os.path.join(os.path.dirname(__file__), "summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
