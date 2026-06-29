"""Step implementations for the reporting feature."""

import time

from behave import given, then, when


@given('the report engine is ready')
def step_engine_ready(context):
    """Set up the report engine."""
    context.report = {"rows": 0, "size": 0}


@when('the report is generated with {rows:d} rows')
def step_generate_report(context, rows):
    """Simulate report generation."""
    time.sleep(0.2)
    context.report["rows"] = rows
    context.report["size"] = rows * 1024


@then('the report is available')
def step_report_available(context):
    """Assert the report exists."""
    report = getattr(context, "report", {})
    assert report.get("rows", 0) > 0


@then('the report size is greater than {size:d} MB')
def step_report_size(context, size):
    """Assert report size in MB."""
    mb = context.report["size"] / (1024 * 1024)
    assert mb > size, f"Report size {mb:.2f} MB is not greater than {size} MB"


@given('the legacy engine is enabled')
def step_legacy_engine(context):
    """Legacy engine setup (this scenario is skipped)."""
    pass


@given('the legacy report engine is being implemented')
def step_legacy_pending(context):
    """Pending step that marks the scenario as pending."""
    context.scenario.skip("Legacy report engine not implemented yet")


@when('the legacy report is generated')
def step_legacy_report(context):
    """Legacy report generation (this scenario is skipped)."""
    pass
