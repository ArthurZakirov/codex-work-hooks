"""Assess a submission without depending on files, Codex events or a model provider."""
from dataclasses import dataclass, replace
from work_hooks.core.assessment import AssessmentKind, ClassificationInput
from work_hooks.ports.classifiers import ScopeClassifier


@dataclass(frozen=True)
class Session:
    criteria: str = ""
    pending: str = ""
    approved: str = ""


@dataclass(frozen=True)
class Decision:
    session: Session
    message: str
    blocked: bool = False
    review: bool = False


def evaluate(request: str, session: Session, classify: ScopeClassifier) -> Decision:
    grade = classify(ClassificationInput(request, session.pending, session.criteria))
    kind = grade.kind
    if kind is AssessmentKind.EXPLANATION:
        return Decision(session, "Explain using the conversation context. Do not implement changes.")

    if grade.criteria:
        if any(not line.strip() or line not in request for line in grade.criteria):
            raise ValueError("criteria must quote the submission")
        session = replace(session, criteria="\n".join(grade.criteria))
    if kind is AssessmentKind.ACCEPTANCE_CRITERIA_ONLY:
        if not grade.criteria:
            raise ValueError("missing pasted criteria")
        return Decision(session, "Acknowledge the saved acceptance criteria and await the request.")

    prior = "" if grade.replacement else session.pending
    full_request = "\n".join(filter(None, [prior, request]))
    blocked = kind is AssessmentKind.UNCLEAR
    message = grade.reason
    if kind is AssessmentKind.PROFESSIONAL:
        blocked = not session.criteria or grade.score < 8
        message = (f"Scope {grade.score}/10 · {grade.reason}" if session.criteria
                   else "Please paste the acceptance criteria into this chat.")

    if blocked:
        return Decision(replace(session, pending=full_request), message, blocked=True)
    if prior:
        message += "\nPreviously blocked request now approved:\n" + prior
    if kind is AssessmentKind.PROFESSIONAL:
        message += "\nActive work item:\n" + session.criteria
    return Decision(replace(session, pending="", approved=full_request), message, review=True)
