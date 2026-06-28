"""Generate a demo report without running Behave.

Useful for development and for the project's screenshots.

Usage::

    python examples/generate_demo.py
    # -> opens examples/demo-report.html in your default browser

"""

from __future__ import annotations

import contextlib
import random
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from behave_modern_html_report import Renderer
from behave_modern_html_report.models import (
    Environment,
    ErrorInfo,
    Execution,
    Feature,
    Scenario,
    Statistics,
    Step,
)
from behave_modern_html_report.renderer import RenderOptions

STATUSES = ["passed"] * 14 + ["failed"] * 2 + ["skipped"] * 2 + ["undefined"]


def _random_step(i: int, force: str | None = None) -> Step:
    """Create a single synthetic step with a random status and duration."""
    status = force or random.choice(STATUSES)
    step = Step(
        keyword=random.choice(["Given", "When", "Then", "And"]),
        name=random.choice([
            "the user opens the dashboard",
            "they click the {} button".format(random.choice(["login", "submit", "buy"])),
            "the API returns 200",
            "the response payload matches the schema",
            f"the cart contains {random.randint(1, 9)} items",
        ]),
        status=status,
        duration=round(random.uniform(0.005, 1.2), 3),
        location=f"features/steps/example.py:{10 + i}",
    )
    if status == "failed":
        step.error = ErrorInfo(
            exception_type="AssertionError",
            message="Expected 200 but got 500",
            traceback=(
                "Traceback (most recent call last):\n"
                '  File "features/steps/example.py", line 42, in step_impl\n'
                "    assert response.status_code == 200\n"
                "AssertionError: Expected 200 but got 500"
            ),
        )
    return step


def _random_scenario(idx: int, feature_name: str) -> Scenario:
    """Create a synthetic scenario with random steps and tags."""
    n_steps = random.randint(3, 6)
    failing = random.random() < 0.12
    steps = [_random_step(i, "failed" if failing and i == n_steps - 2 else None) for i in range(n_steps)]
    status = (
        "failed" if any(s.status == "failed" for s in steps)
        else "undefined" if any(s.status == "undefined" for s in steps)
        else "passed"
    )
    return Scenario(
        name=f"Scenario {idx}: {random.choice(['login flow', 'checkout', 'reporting', 'API contract', 'permissions'])}",
        status=status,
        description="",
        location=f"features/{feature_name}.feature:{idx * 4}",
        tags=random.sample(["smoke", "regression", "ui", "api", "nightly", "wip"], k=random.randint(0, 3)),
        steps=steps,
        feature_name=feature_name,
    )


def build_demo_execution() -> Execution:
    """Build a deterministic demo execution tree for screenshots and previews."""
    random.seed(42)
    start = datetime.now() - timedelta(seconds=42)
    features = []
    for fname in ["Checkout", "Authentication", "Reporting", "Settings"]:
        feat = Feature(
            name=fname,
            description=f"Behavior of the {fname.lower()} subsystem.",
            location=f"features/{fname.lower()}.feature:1",
            tags=[fname.lower()],
        )
        feat.scenarios = [_random_scenario(i + 1, fname) for i in range(random.randint(4, 8))]
        features.append(feat)

    return Execution(
        title="Behave Modern Report — Demo",
        features=features,
        environment=Environment(
            python_version="3.12.1",
            behave_version="1.2.6",
            platform="Demo OS 1.0 (x86_64)",
            hostname="demo-host",
            command="behave -f modern -o demo-report.html",
            extra={"CI": "false", "Branch": "main"},
        ),
        statistics=Statistics(start_time=start, end_time=datetime.now()),
    )


def main() -> None:
    """Generate the demo report and open it in the default browser."""
    execution = build_demo_execution()
    renderer = Renderer(RenderOptions(
        title="Behave Modern Report — Demo",
        company="Open Source",
        theme="auto",
    ))
    out = Path(__file__).resolve().parent / "demo-report.html"
    renderer.render_to_file(execution, out)
    print(f"Wrote {out}")
    with contextlib.suppress(Exception):
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
