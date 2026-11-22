Feature: Review handoff in stock Codex
  Scenario: An independently installed review plugin delivers findings to the worker
    Given a Codex workspace with only Parallel Review installed
    When the user makes a documentation edit
    Then the worker applies a review-guided edit and finishes after one review pass

  Scenario: Discussion in a workspace containing unrelated code
    Given a Codex workspace with only Parallel Review installed
    When the user asks a discussion question
    Then the turn completes without recording edits or producing a report
