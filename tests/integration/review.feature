Feature: Independent review of a completed request
  Scenario: Code and Markdown reviewers return one report without scope credentials
    Given a completed request in a sample workspace
    When the review plugin receives a mixed patch and a stop event
    Then it returns a report with findings from each review perspective
    And a follow-up stop does not request another review
