"""TypeSafe System One adapter. Only ClassificationInput is serialized."""
from dataclasses import asdict
import json
import re
import subprocess
from typing import Any

from work_hooks.core.models import Assessment, AssessmentKind, ClassificationInput

KINDS = {
    AssessmentKind.EXPLANATION: "Only asks to understand existing code or behavior. No requested changes.",
    AssessmentKind.ACCEPTANCE_CRITERIA_ONLY: "Supplies acceptance criteria without requesting work.",
    AssessmentKind.EXCEPTION: "Colleague PR review or roughly five minutes of colleague help.",
    AssessmentKind.PERSONAL: "Private or hobby task.",
    AssessmentKind.PROFESSIONAL: "Team deliverable or explicitly simulated professional work, including mixed explanation and changes.",
    AssessmentKind.UNCLEAR: "Beneficiary or intent remains ambiguous.",
}

LEVELS = ["Unrelated", "Very weak link", "Separate work item", "Possible link",
          "Plausible but unproven", "Indirect support", "Necessity unclear",
          "Demonstrated prerequisite", "Direct requirement", "Exactly the acceptance criterion"]


def classify(evidence: ClassificationInput) -> Assessment:
    spans = [s.strip() for s in re.split(r"\n|(?<=[.!?])\s+", evidence.request) if s.strip()]
    questions: dict[str, Any] = {
        "context_only": {"type": "noul", "instructions": "Is the current message only supplying the work item acceptance criteria for reference, without asking to implement anything now?"},
        "explain_only": {"type": "noul", "instructions": "Look only at state.request. Is the user asking for an explanation of code or behavior without asking anyone to make changes? A question about Pydantic is a typical example."},
        "kind": {"type": "choice", "instructions": "Classify the current request, considering pending work only when relevant.",
                 "criteria": {kind.value: label for kind, label in KINDS.items()}},
        "alignment": {"type": "score", "instructions": "How necessary is the entire requested change for the supplied work item or explicitly pasted criteria?", "criteria": LEVELS},
        "replacement": {"type": "noul", "instructions": "Does this request replace, rather than clarify, the pending request?"},
    }
    for i, span in enumerate(spans):
        questions[f"criterion_{i}"] = {"type": "noul", "instructions":
            f"Does this passage supply a new acceptance criterion? Exclude implementation requests and questions. Passage: {span}"}

    answers = _ask_jev(asdict(evidence), questions)
    kind = AssessmentKind(answers["kind"]["choice"])
    if answers["explain_only"]["noul"] >= 0.5:
        kind = AssessmentKind.EXPLANATION
    score = 1 + round(answers["alignment"]["score"])
    if not 1 <= score <= len(LEVELS):
        raise ValueError("invalid Jev alignment score")
    criteria = [span for i, span in enumerate(spans) if answers[f"criterion_{i}"]["noul"] >= 0.5]
    if criteria and answers["context_only"]["noul"] >= 0.5:
        kind = AssessmentKind.ACCEPTANCE_CRITERIA_ONLY
    reason = LEVELS[score - 1] if kind is AssessmentKind.PROFESSIONAL else KINDS[kind]
    return Assessment(kind, score, reason, answers["replacement"]["noul"] >= 0.5, criteria)


def _ask_jev(state: dict[str, str], questions: dict[str, Any]) -> dict[str, Any]:
    """curl expands the credential internally; it never appears in arguments or logs."""
    payload = {"model": "jev-latest", "state": state, "questions": questions}
    result = subprocess.run(
        ["curl", "--disable", "--silent", "--fail", "--max-time", "60",
         "--variable", "%JEV_API_KEY", "--expand-header", "Authorization: Bearer {{JEV_API_KEY}}",
         "--header", "Content-Type: application/json", "--data-binary", "@-",
         "https://api.typesafe.ai/v1/systemone"],
        input=json.dumps(payload), capture_output=True, text=True, check=True)
    return json.loads(result.stdout)["answers"]
