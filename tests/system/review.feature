Feature: Review handoff in stock Codex
  Scenario: An independently installed review plugin delivers findings to the worker
    Given a read-only Codex workspace with only Parallel Review installed
    When the user asks for a handoff
    Then the worker receives the review report and completes the turn
