"""TypeSafe System One adapter. Only ClassificationInput is serialized."""
from dataclasses import asdict
import json
from pathlib import Path
from work_hooks.adapters.process import run_command
from typing import Any

from work_hooks.core.models import Assessment, AssessmentKind, ClassificationInput, Ownership

KINDS = {
    AssessmentKind.EXPLANATION: "Only asks to understand existing code or behavior. No requested changes.",
    AssessmentKind.ACCEPTANCE_CRITERIA_ONLY: "Supplies acceptance criteria without requesting work.",
    AssessmentKind.EXCEPTION: "Colleague PR review or roughly five minutes of colleague help.",
    AssessmentKind.IMPLEMENTATION: "Team deliverable or explicitly simulated professional work, including mixed explanation and changes.",
    AssessmentKind.UNCLEAR: "Beneficiary or intent remains ambiguous.",
}

LEVELS = ["Unrelated", "Very weak link", "Separate work item", "Possible link",
          "Plausible but unproven", "Indirect support", "Necessity unclear",
          "Demonstrated prerequisite", "Direct requirement", "Exactly the acceptance criterion"]


def ownership(request: str, previous: str, pending_request: str) -> Ownership:
    rubric = Path(__file__).resolve().parents[2] / "resources/prompts/ownership.md"
    question = {"type": "choice", "instructions": rubric.read_text(),
                "criteria": {"personal": "Private work", "professional": "Work for others or uncertain"}}
    answers = _ask_jev({"request": request, "previous": previous, "pending_request": pending_request}, {"ownership": question})
    return Ownership(answers["ownership"]["choice"])


def classify(evidence: ClassificationInput) -> Assessment:
    questions: dict[str, Any] = {
        "context_only": {"type": "noul", "instructions": "Is the current message only supplying the work item acceptance criteria for reference, without asking to implement anything now?"},
        "explain_only": {"type": "noul", "instructions": "Look only at state.request. Is the user asking for an explanation of code or behavior without asking anyone to make changes? A question about Pydantic is a typical example."},
        "kind": {"type": "choice", "instructions": "Classify the current request, considering pending work only when relevant.",
                 "criteria": {kind.value: label for kind, label in KINDS.items()}},
        "prerequisite": {"type": "noul", "instructions": "Does the requester explain a concrete limitation of existing checks and propose a focused way to verify a specific externally authorized criterion? Generic preferences, optional infrastructure and new product requirements do not qualify."},
        "alignment": {"type": "score", "instructions": "How necessary is the entire requested change for the supplied work item from external evidence only; conflicting or insufficient evidence scores below 8?", "criteria": LEVELS},
        "replacement": {"type": "noul", "instructions": "Does this request replace, rather than clarify, the pending request?"},
    }
    answers = _ask_jev(asdict(evidence), questions)
    kind = AssessmentKind(answers["kind"]["choice"])
    if answers["explain_only"]["noul"] >= 0.5:
        kind = AssessmentKind.EXPLANATION
    score = 1 + round(answers["alignment"]["score"])
    if evidence.work_item and answers["prerequisite"]["noul"] >= 0.8:
        score = max(score, 8)
    if not 1 <= score <= len(LEVELS):
        raise ValueError("invalid Jev alignment score")
    if answers["context_only"]["noul"] >= 0.5:
        kind = AssessmentKind.ACCEPTANCE_CRITERIA_ONLY
    reason = LEVELS[score - 1] if kind is AssessmentKind.IMPLEMENTATION else KINDS[kind]
    return Assessment(kind, score, reason, answers["replacement"]["noul"] >= 0.5)


def _ask_jev(state: dict[str, str], questions: dict[str, Any]) -> dict[str, Any]:
    """curl expands the credential internally; it never appears in arguments or logs."""
    payload = {"model": "jev-latest", "state": state, "questions": questions}
    result = run_command("Jev classifier",
        ["curl", "--disable", "--silent", "--show-error", "--fail", "--max-time", "60",
         "--variable", "%JEV_API_KEY", "--expand-header", "Authorization: Bearer {{JEV_API_KEY}}",
         "--header", "Content-Type: application/json", "--data-binary", "@-",
         "https://api.typesafe.ai/v1/systemone"],
        input=json.dumps(payload), timeout=65)
    return json.loads(result.stdout)["answers"]
