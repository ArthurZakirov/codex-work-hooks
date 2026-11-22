"""The hook supplies scoped evidence. Adapters return a domain assessment."""
from dataclasses import dataclass
from enum import Enum


class Ownership(str, Enum):
    PERSONAL = "personal"
    PROFESSIONAL = "professional"


class AssessmentKind(str, Enum):
    EXPLANATION = "explanation"
    IMPLEMENTATION = "implementation"
    EXCEPTION = "exception"
    UNCLEAR = "unclear"
    ACCEPTANCE_CRITERIA_ONLY = "criteria_only"


@dataclass(frozen=True)
class Assessment:
    kind: AssessmentKind
    score: int
    reason: str
    replacement: bool


@dataclass(frozen=True)
class ClassificationInput:
    request: str
    pending_request: str
    work_item: str


@dataclass(frozen=True)
class Session:
    ownership: str = ""
    pending: str = ""
    approved: str = ""


@dataclass(frozen=True)
class Decision:
    session: Session
    message: str
    blocked: bool = False
    review: bool = False
