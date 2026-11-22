Feature: Scope decisions for professional and personal requests
  Scenario: Hold a team implementation request until its requirements are known
    Given the team has supplied no ticket or other verified requirements
    When the user asks to implement a feature for the team
    Then implementation is blocked and the requester is asked for the originating ticket or colleague message

  Scenario: Implement the selected ticket
    Given a ticket with verified acceptance criteria is selected
    When the user requests the change specified by the ticket
    Then implementation may begin

  Scenario: Approve additional work only after its necessity is established
    Given a ticket with verified acceptance criteria is selected
    When the user requests additional work without showing why a criterion requires it
    Then implementation is blocked
    When the user justifies the additional work with a personal preference
    Then implementation is blocked
    When the user explains why a focused change is necessary to verify a specific criterion
    Then implementation may begin

  Scenario Outline: Personal setup requests can proceed during professional work
    Given <requirements_context>
    When the user asks for help with their own development setup
    Then the personal request may proceed

    Examples:
      | requirements_context                                         |
      | a ticket with verified acceptance criteria is selected       |
      | the team has supplied no ticket or other verified requirements |
