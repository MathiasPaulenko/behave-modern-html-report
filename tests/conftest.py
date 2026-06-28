"""Shared fixtures."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from behave_modern_report.models import (
    Environment,
    ErrorInfo,
    Execution,
    Feature,
    Scenario,
    Statistics,
    Step,
)


@pytest.fixture
def sample_execution() -> Execution:
    """Build a small but representative execution tree."""
    start = datetime(2026, 6, 28, 12, 0, 0)

    f1 = Feature(
        name="Checkout",
        description="Buy items happily.",
        location="features/checkout.feature:1",
        tags=["smoke"],
    )
    s_ok = Scenario(
        name="Customer buys a book",
        status="passed",
        location="features/checkout.feature:3",
        tags=["happy"],
        feature_name=f1.name,
        steps=[
            Step(keyword="Given", name="a logged-in user", status="passed", duration=0.012),
            Step(keyword="When", name="they add a book", status="passed", duration=0.034),
            Step(keyword="Then", name="they see the cart", status="passed", duration=0.021),
        ],
    )
    s_fail = Scenario(
        name="Customer pays with expired card",
        status="failed",
        location="features/checkout.feature:9",
        tags=["payment"],
        feature_name=f1.name,
        steps=[
            Step(keyword="Given", name="a logged-in user", status="passed", duration=0.011),
            Step(keyword="When", name="they pay with an expired card", status="failed", duration=0.250,
                 error=ErrorInfo(
                     message="Card expired",
                     traceback="Traceback (most recent call last):\n  ...\nValueError: Card expired",
                     exception_type="ValueError",
                 )),
            Step(keyword="Then", name="they see a friendly error", status="skipped"),
        ],
    )
    f1.scenarios = [s_ok, s_fail]

    f2 = Feature(name="Reports", location="features/reports.feature:1", tags=["nightly"])
    f2.scenarios = [
        Scenario(
            name="Generate PDF",
            status="passed",
            feature_name=f2.name,
            steps=[Step(keyword="Given", name="data exists", status="passed", duration=0.04)],
        ),
        Scenario(
            name="Generate CSV",
            status="undefined",
            feature_name=f2.name,
            steps=[Step(keyword="Given", name="data exists", status="undefined")],
        ),
    ]

    exec_ = Execution(
        title="Sample Suite",
        features=[f1, f2],
        environment=Environment(
            python_version="3.12.1",
            behave_version="1.2.6",
            platform="Windows 11 (AMD64)",
            hostname="dev-machine",
            command="behave -f modern -o report.html",
        ),
        statistics=Statistics(start_time=start, end_time=start + timedelta(seconds=5)),
    )
    return exec_
