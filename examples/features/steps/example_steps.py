"""Step implementations for the demo feature."""

from behave import given, then, when


@given("I have entered {value:d}")
def step_enter(context, value):
    """Store the entered value for the addition scenario."""
    context.values = getattr(context, "values", [])
    context.values.append(value)


@when("I press add")
def step_add(context):
    """Sum all entered values."""
    context.result = sum(context.values)


@then("the result should be {expected:d}")
def step_check(context, expected):
    """Assert the computed result matches the expected value."""
    assert context.result == expected, f"Expected {expected}, got {context.result}"
