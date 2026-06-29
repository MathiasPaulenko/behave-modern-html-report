Feature: Checkout
  As a customer
  I want to complete a purchase
  So that I receive my order

  Background: Common order
    Given the cart contains 1 item
    And the total is 100

  @checkout @payment
  Scenario: Pay with credit card
    When the user pays with "credit card"
    Then the payment is accepted

  @checkout @payment
  Scenario: Pay with invalid card
    Given the total is 50
    When the user pays with "expired card"
    Then the payment is rejected

  @checkout @shipping
  Scenario: Choose express shipping
    Given the order is confirmed
    When the user selects "express" shipping
    Then the shipping cost is 15

  @checkout @shipping
  Scenario: Choose standard shipping
    Given the order is confirmed
    When the user selects "standard" shipping
    Then the shipping cost is 5
