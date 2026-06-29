"""Step implementations for the checkout feature."""

import time

from behave import given, then, when


@given('the cart contains {count:d} items')
@given('the cart contains 1 item')
def step_cart_items(context, count=1):
    context.cart = {"items": count, "total": count * 50}


@given('the total is {total:d}')
def step_total(context, total):
    context.cart["total"] = total


@when('the user pays with "{method}"')
def step_pay(context, method):
    time.sleep(0.05)
    context.payment_accepted = method == "credit card"
    context.payment_method = method


@then('the payment is accepted')
def step_payment_accepted(context):
    assert context.payment_accepted, "Payment was rejected"


@then('the payment is rejected')
def step_payment_rejected(context):
    assert not context.payment_accepted, "Payment was unexpectedly accepted"


@given('the order is confirmed')
def step_order_confirmed(context):
    context.order = {"status": "confirmed"}


@when('the user selects "{method}" shipping')
def step_select_shipping(context, method):
    time.sleep(0.03)
    context.shipping = method


@then('the shipping cost is {cost:d}')
def step_shipping_cost(context, cost):
    expected = {"express": 15, "standard": 5}[context.shipping]
    assert expected == cost, f"Expected shipping cost {cost}, got {expected}"


@then('the order is confirmed')
def step_check_confirmed(context):
    assert context.order["status"] == "confirmed"
