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

  Scenario: Continue delivery workflow while an implementation request is pending
    Given the team has supplied no ticket or other verified requirements
    When the user asks to implement a feature for the team
    Then implementation is blocked and the requester is asked for the originating ticket or colleague message
    When the user discusses and revises a PR announcement and requests the originating ticket
    Then each workflow request proceeds and the implementation remains pending
    When the user combines ticket lookup with an unrelated refactor
    Then implementation is blocked

  Scenario: Continue personal implementation after correcting project ownership
    Given the team has supplied no ticket or other verified requirements
    When the user asks to implement a feature for the team
    Then implementation is blocked
    When the user clarifies that the current project is personal
    Then the personal request may proceed
    When the user asks to proceed without restating the task
    Then the personal request may proceed
    When the user asks to implement a feature for the team
    Then implementation is blocked

  Scenario: Distinguish a developer's own workflow from an agent delivered to their team
    Given the team has supplied no ticket or other verified requirements
    When the user builds an agent to improve their own development workflow
    Then the personal request may proceed
    When the user builds an agent as a team deliverable
    Then implementation is blocked

  Scenario Outline: Resolve the same assent against the preceding assistant proposal
    Given the team has supplied no ticket or other verified requirements
    And the assistant has proposed <proposal>
    When the user says go
    Then <outcome>

    Examples:
      | proposal                            | outcome                          |
      | a private developer workflow change | the personal request may proceed |
      | a change to the team's service      | implementation is blocked        |

  Scenario: Assent to a proposal outside the selected ticket remains out of scope
    Given a ticket with verified acceptance criteria is selected
    And the assistant has proposed an unrelated team feature
    When the user says go
    Then implementation is blocked
