Feature: Work approval in an installed Codex chat
  Scenario: Hold implementation until the user supplies the team ticket
    Given a fresh read-only Codex workspace with only Scope Check installed and no selected ticket
    When the user requests a feature for the team
    Then the request is pending and the worker has used no model tokens
    When the user supplies the originating ticket in the same chat
    Then the hook selects the ticket and the worker acknowledges it
    When the user asks for the approved change on a later turn
    Then the scope gate approves the implementation request
    And the application code remains unchanged
