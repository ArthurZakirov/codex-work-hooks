"""Only source adapters may produce evidence; chat messages are never a source."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Requirement:
    source_ref: str
    revision: str
    author_id: str
    text: str


class Requirements(Protocol):
    def __call__(self, session_id: str) -> tuple[Requirement, ...]:
        """Return current externally authorized evidence for this session's work item."""
        ...


def unavailable(session_id: str) -> tuple[Requirement, ...]:
    return ()
