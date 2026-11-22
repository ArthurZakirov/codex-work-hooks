from typing import Protocol
from work_hooks.core.models import Assessment, ClassificationInput, Ownership


class ScopeClassifier(Protocol):
    def ownership(self, request: str, previous: str, pending_request: str) -> Ownership: ...
    def classify(self, evidence: ClassificationInput) -> Assessment: ...
