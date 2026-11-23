"""Assess a submission without depending on files, Codex events or a model provider."""
from dataclasses import replace
from work_hooks.core.models import AssessmentKind, ClassificationInput, Decision, Ownership, Session
from work_hooks.ports.requirements import Requirements
from work_hooks.ports.scope_classifier import ScopeClassifier


def evaluate_submission(request: str, session: Session, classify: ScopeClassifier,
                        requirements: Requirements, session_id: str) -> Decision:
    owner = classify.ownership(request, session.ownership, session.pending)
    if owner is Ownership.PERSONAL:
        return Decision(replace(session, ownership=owner.value, approved=request), "")

    session = replace(session, ownership=owner.value)
    records = requirements(session_id)
    criteria = "\n".join(f"{r.source_ref} ({r.author_id}, {r.revision}): {r.text}" for r in records)
    grade = classify.classify(ClassificationInput(request, session.pending, criteria))
    kind = grade.kind
    if kind is AssessmentKind.EXPLANATION:
        return Decision(session, "Explain using the conversation context. Do not implement changes.")
    if kind is AssessmentKind.ACCEPTANCE_CRITERIA_ONLY:
        return Decision(session, "", capture_criteria=True)
    if kind is AssessmentKind.EXCEPTION:
        return Decision(session, "Carry out the current workflow request. Leave pending implementation requests on hold.")
    if kind is AssessmentKind.UNCLEAR:
        return Decision(session, "Answer or clarify the current request using the conversation context. Ask before making implementation changes.")

    prior = "" if grade.replacement else session.pending
    full_request = "\n".join(filter(None, [prior, request]))
    blocked = not criteria or grade.score < 8
    message = (f"Scope {grade.score}/10 · {grade.reason}" if criteria
               else "No verified requirements are available for this work item. Identify the originating ticket or colleague message.")

    if blocked:
        return Decision(replace(session, pending=full_request), message, blocked=True)
    if prior:
        message += "\nPreviously blocked request now approved:\n" + prior
    message += "\nActive work item:\n" + criteria
    return Decision(replace(session, pending="", approved=full_request), message)
