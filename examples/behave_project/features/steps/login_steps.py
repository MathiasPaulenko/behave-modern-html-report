"""Step implementations for the login feature."""

from behave import given, then, when


@given('the database is reset')
def step_reset_db(context):
    """Simulate resetting the test database."""
    context.database = {"users": {"alice": "secret1", "bob": "secret2", "locked": "secret"}}


@given('a registered user exists')
def step_user_exists(context):
    """Ensure the test user database is populated."""
    assert context.database is not None


@given('the username is "{username}"')
def step_set_username(context, username):
    """Store the username."""
    context.username = username


@given('the password is "{password}"')
def step_set_password(context, password):
    """Store the password."""
    context.password = password


@when('the user logs in')
def step_login(context):
    """Attempt login with stored credentials."""
    expected = context.database["users"].get(context.username)
    context.logged_in = expected is not None and expected == context.password


@then('the dashboard is shown')
def step_dashboard(context):
    """Assert the user reached the dashboard."""
    assert context.logged_in, "User is not logged in"


@then('an error is shown')
def step_error(context):
    """Assert login failed."""
    assert not context.logged_in, "User unexpectedly logged in"


@then('the account locked message is shown')
def step_locked(context):
    """Pending scenario: mark as pending for the report."""
    context.scenario.skip("Account locking logic is not implemented yet")
