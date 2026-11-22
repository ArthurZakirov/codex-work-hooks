from typing import Protocol
from work_hooks.core.models import Assessment, ClassificationInput


class ScopeClassifier(Protocol):
    def __call__(self, evidence: ClassificationInput) -> Assessment: ...
