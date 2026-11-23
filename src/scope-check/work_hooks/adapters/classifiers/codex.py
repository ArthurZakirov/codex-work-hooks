from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
from work_hooks.adapters.process import run_command

from work_hooks.core.models import Assessment, AssessmentKind, ClassificationInput, Ownership

RESOURCES = Path(__file__).resolve().parents[2] / "resources"
SCOPE_RUBRIC = RESOURCES / "prompts/scope.md"


def ownership(request: str, previous: str, pending_request: str) -> Ownership:
    rubric = (RESOURCES / "prompts/ownership.md").read_text()
    prompt = rubric + json.dumps({"request": request, "previous": previous, "pending_request": pending_request})
    output = _run_codex_classifier(prompt, RESOURCES / "ownership.json")
    return Ownership(json.loads(output)["ownership"])


def classify(evidence: ClassificationInput) -> Assessment:
    prompt = _build_assessment_prompt(evidence)
    return _parse_assessment(_run_codex_classifier(prompt, RESOURCES / "grade.json"))


def _build_assessment_prompt(submission: ClassificationInput) -> str:
    evidence = {
        "request": submission.request,
        "pending": submission.pending_request,
        "work_item": submission.work_item,
    }
    return SCOPE_RUBRIC.read_text() + "\nReturn only JSON, without fences.\n" + json.dumps(evidence)


def _run_codex_classifier(prompt: str, schema: Path) -> str:
    with TemporaryDirectory() as workspace:
        command = [
            "codex", "--no-daemon", "exec", "-C", workspace, "--disable", "hooks", "--ephemeral", "--skip-git-repo-check",
            "--ignore-user-config", "--ignore-rules", "--disable", "plugins", "--disable", "apps",
            "--disable", "shell_tool", "--disable", "unified_exec", "-c", "project_doc_max_bytes=0",
            "--output-schema", str(schema),
            "-s", "read-only", "-m", os.getenv("WORK_HOOKS_MODEL", "gpt-6-luna"), "-c", 'model_reasoning_effort="low"', "-",
        ]
        result = run_command(f"Codex classifier ({schema.stem})",
            command,
            input=prompt,
            env={k: v for k, v in os.environ.items() if k != "JEV_API_KEY"},
            timeout=75,
        )
    return result.stdout


def _parse_assessment(output: str) -> Assessment:
    payload = output.strip().removeprefix("```json").removesuffix("```").strip()
    fields = json.loads(payload)
    kind = AssessmentKind(fields["kind"])
    score = fields["score"]
    if type(score) is not int or not 1 <= score <= 10:
        raise ValueError("invalid necessity score")
    if not isinstance(fields["reason"], str) or type(fields["replacement"]) is not bool:
        raise ValueError("invalid assessment")

    return Assessment(kind, score, fields["reason"], fields["replacement"])
