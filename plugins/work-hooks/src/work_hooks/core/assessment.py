"""The hook supplies scoped evidence. Adapters return a domain assessment."""
from dataclasses import dataclass
from enum import Enum


class AssessmentKind(str, Enum):
    EXPLANATION = "explanation"
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    EXCEPTION = "exception"
    UNCLEAR = "unclear"
    ACCEPTANCE_CRITERIA_ONLY = "criteria_only"


@dataclass(frozen=True)
class Assessment:
    kind: AssessmentKind
    score: int
    reason: str
    replacement: bool
    criteria: list[str]


@dataclass(frozen=True)
class ClassificationInput:
    request: str
    pending_request: str
    work_item: str
