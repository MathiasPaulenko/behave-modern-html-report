Feature: Reporting
  As a QA engineer
  I want test artifacts to be captured
  So that failures are easier to diagnose

  @reporting @slow
  Scenario: Generate a large report
    Given the report engine is ready
    When the report is generated with 1000 rows
    Then the report is available
    And the report size is greater than 0 MB

  @reporting @pending
  Scenario: Pending legacy report
    Given the legacy report engine is being implemented
    When the legacy report is generated
    Then the report is available
