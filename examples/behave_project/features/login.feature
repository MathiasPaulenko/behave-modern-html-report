Feature: User login
  As a registered user
  I want to log in with my credentials
  So that I can access the dashboard

  Background: Reset test account
    Given the database is reset
    And a registered user exists

  @smoke @login
  Scenario Outline: Login with valid credentials
    Given the username is "<username>"
    And the password is "<password>"
    When the user logs in
    Then the dashboard is shown

    Examples:
      | username | password |
      | alice    | secret1  |
      | bob      | secret2  |

  @login @negative
  Scenario: Login with invalid credentials
    Given the username is "eve"
    And the password is "wrong"
    When the user logs in
    Then an error is shown

  @login @pending
  Scenario: Login with locked account
    Given the username is "locked"
    And the password is "secret"
    When the user logs in
    Then the account locked message is shown

  @login
  Scenario: Undefined social login step
    Given the user chooses Google login
    When the user logs in
    Then the dashboard is shown
