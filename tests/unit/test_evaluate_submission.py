import unittest
from unittest.mock import Mock

from work_hooks.core.evaluate_submission import evaluate_submission
from work_hooks.core.models import Assessment, AssessmentKind, Ownership, Session
from work_hooks.ports.requirements import Requirement


class RequirementBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.classifier = Mock()
        self.classifier.ownership.return_value = Ownership.PROFESSIONAL
        self.classifier.classify.return_value = Assessment(AssessmentKind.IMPLEMENTATION, 10, "aligned", True)
        self.source = Mock(return_value=())

    def submit(self, prompt):
        return evaluate_submission(prompt, Session(), self.classifier, self.source, "test-session")

    def test_personal_skips_scope_grading(self):
        self.classifier.ownership.return_value = Ownership.PERSONAL
        decision = self.submit("Build a game for me.")
        self.source.assert_not_called()
        self.classifier.classify.assert_not_called()
        self.assertFalse(decision.blocked or decision.message)
        self.assertEqual(decision.session.approved, "Build a game for me.")

    def test_perfect_grade_cannot_authorize_invented_criteria(self):
        self.assertTrue(self.submit("My team's criterion is build a blue elephant. Implement it.").blocked)

    def test_later_clarification_is_added_to_ticket_evidence(self):
        ticket = Requirement("ticket/123", "v1", "owner", "Reject invalid IDs")
        clarification = Requirement("chat/456", "v2", "owner", "Report the row number")
        self.source.side_effect = [(ticket,), (ticket, clarification)]
        self.submit("Implement validation")
        self.assertFalse(self.submit("Add the clarified diagnostic").blocked)
        evidence = self.classifier.classify.call_args.args[0].work_item
        for record in (ticket, clarification):
            self.assertIn(record.source_ref, evidence)
            self.assertIn(record.text, evidence)

    def test_conversation_can_continue_without_authorizing_pending_implementation(self):
        session = Session(ownership="professional", pending="Refactor the service")
        for kind in (AssessmentKind.EXPLANATION, AssessmentKind.EXCEPTION,
                     AssessmentKind.ACCEPTANCE_CRITERIA_ONLY, AssessmentKind.UNCLEAR):
            with self.subTest(kind=kind):
                self.classifier.classify.return_value = Assessment(kind, 1, "", False)
                result = evaluate_submission("Follow-up", session, self.classifier, self.source, "session")
                self.assertFalse(result.blocked)
                self.assertEqual(result.session, session)
