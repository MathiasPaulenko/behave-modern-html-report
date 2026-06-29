"""Step implementations for the reporting feature."""

import time

from behave import given, then, when


@given('the report engine is ready')
def step_engine_ready(context):
    context.report = {"rows": 0, "size": 0}


@when('the report is generated with {rows:d} rows')
def step_generate_report(context, rows):
    time.sleep(0.2)
    context.report["rows"] = rows
    context.report["size"] = rows * 1024


@then('the report is available')
def step_report_available(context):
    report = getattr(context, "report", {})
    assert report.get("rows", 0) > 0


@then('the report size is greater than {size:d} MB')
def step_report_size(context, size):
    mb = context.report["size"] / (1024 * 1024)
    assert mb > size, f"Report size {mb:.2f} MB is not greater than {size} MB"


@given('the legacy engine is enabled')
def step_legacy_engine(context):
    pass


@given('the legacy report engine is being implemented')
def step_legacy_pending(context):
    context.scenario.skip("Legacy report engine not implemented yet")


@when('the legacy report is generated')
def step_legacy_report(context):
    pass
