from typing import Protocol
from work_hooks.core.assessment import Assessment, ClassificationInput


class ScopeClassifier(Protocol):
    def __call__(self, evidence: ClassificationInput) -> Assessment: ...
