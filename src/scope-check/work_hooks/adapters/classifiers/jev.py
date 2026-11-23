"""TypeSafe System One adapter. Only ClassificationInput is serialized."""
from dataclasses import asdict
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, HTTPRedirectHandler, Request
from work_hooks.adapters.jev_key import resolve_key
import ssl
import socket
from work_hooks.adapters.process import HookCommandError
from typing import Any

from work_hooks.core.models import Assessment, AssessmentKind, ClassificationInput, Ownership

KINDS = {
    AssessmentKind.EXPLANATION: "Only asks to understand a draft, discrepancy, decision, code or behavior. No requested changes.",
    AssessmentKind.ACCEPTANCE_CRITERIA_ONLY: "Fetches, selects, supplies or updates a work item or its acceptance criteria without requesting implementation.",
    AssessmentKind.EXCEPTION: "Delivery workflow: gather general context, draft or revise a PR/team announcement, review a colleague PR, or briefly assist a colleague.",
    AssessmentKind.IMPLEMENTATION: "Product or engineering changes including new features, refactors, tests, infrastructure, and mixed workflow plus implementation.",
    AssessmentKind.UNCLEAR: "Beneficiary or intent remains ambiguous.",
}

LEVELS = ["Unrelated", "Very weak link", "Separate work item", "Possible link",
          "Plausible but unproven", "Indirect support", "Necessity unclear",
          "Demonstrated prerequisite", "Direct requirement", "Exactly the acceptance criterion"]


def ownership(request: str, previous: str, pending_request: str, previous_assistant_reply: str) -> Ownership:
    rubric = Path(__file__).resolve().parents[2] / "resources/prompts/ownership.md"
    question = {"type": "choice", "instructions": rubric.read_text(),
                "criteria": {"personal": "Private work", "professional": "Work for others or uncertain"}}
    answers = _ask_jev({"request": request, "previous": previous, "pending_request": pending_request,
                         "previous_assistant_reply": previous_assistant_reply}, {"ownership": question})
    return Ownership(answers["ownership"]["choice"])


def classify(evidence: ClassificationInput) -> Assessment:
    questions: dict[str, Any] = {
        "context_only": {"type": "noul", "instructions": "Is the current message only supplying the work item acceptance criteria for reference, without asking to implement anything now?"},
        "explain_only": {"type": "noul", "instructions": "Look only at state.request. Is the user asking for an explanation of a draft, inconsistency, code or behavior without asking anyone to make changes? A question about Pydantic is a typical example."},
        "kind": {"type": "choice", "instructions": "Resolve assent such as go to the proposal in previous_assistant_reply and classify that action. Use pending work only when relevant.",
                 "criteria": {kind.value: label for kind, label in KINDS.items()}},
        "prerequisite": {"type": "noul", "instructions": "Does the requester explain a concrete limitation of existing checks and propose a focused way to verify a specific externally authorized criterion? Generic preferences, optional infrastructure and new product requirements do not qualify."},
        "alignment": {"type": "score", "instructions": "For assent, resolve the change from previous_assistant_reply. How necessary is the entire requested change for the supplied work item from external evidence only; conflicting or insufficient evidence scores below 8?", "criteria": LEVELS},
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


class _NoRedirect(HTTPRedirectHandler):
    """Keep the authorization header on the configured TypeSafe endpoint."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _ask_jev(state: dict[str, str], questions: dict[str, Any]) -> dict[str, Any]:
    """Send a typed decision to TypeSafe over HTTPS; no local model is needed."""
    key = resolve_key()
    payload = {"model": "jev-latest", "state": state, "questions": questions}
    request = Request("https://api.typesafe.ai/v1/systemone",
                      data=json.dumps(payload).encode(),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with build_opener(_NoRedirect()).open(request, timeout=60) as response:
            return json.load(response)["answers"]
    except HTTPError as error:
        hint = {401: "Check the TypeSafe credential.", 403: "Check account access.",
                429: "Check rate limits and quota."}.get(error.code, "Check TypeSafe availability.")
        raise HookCommandError(f"Jev classifier: TypeSafe returned HTTP {error.code}. {hint}") from None
    except (URLError, OSError) as error:
        cause = error.reason if isinstance(error, URLError) else error
        if isinstance(cause, ssl.SSLCertVerificationError):
            hint = "TLS certificate verification failed. Check the CA bundle used by the hook's Python."
        elif isinstance(cause, socket.gaierror):
            hint = "DNS lookup failed. Check DNS and proxy access from the Codex process."
        else:
            hint = f"Transport error {type(cause).__name__} (errno {getattr(cause, 'errno', None)})."
        raise HookCommandError(f"Jev classifier: HTTPS connection to api.typesafe.ai failed. {hint}") from None
