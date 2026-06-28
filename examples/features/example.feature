Feature: Calculator
  As a user
  I want to add numbers
  So that I can do math

  @smoke
  Scenario: Add two positive numbers
    Given I have entered 50
    And I have entered 70
    When I press add
    Then the result should be 120

  @regression
  Scenario: Add a negative number
    Given I have entered 50
    And I have entered -20
    When I press add
    Then the result should be 30
