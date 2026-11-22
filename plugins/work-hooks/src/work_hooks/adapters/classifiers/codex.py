from pathlib import Path
import json
import os
import subprocess

from work_hooks.core.assessment import Assessment, AssessmentKind, ClassificationInput

RESOURCES = Path(__file__).resolve().parents[2] / "resources"
SCOPE_RUBRIC = RESOURCES / "prompts/scope.md"


def classify(evidence: ClassificationInput) -> Assessment:
    prompt = _build_assessment_prompt(evidence)
    return _parse_assessment(_run_codex_classifier(prompt))


def _build_assessment_prompt(submission: ClassificationInput) -> str:
    evidence = {
        "request": submission.request,
        "pending": submission.pending_request,
        "work_item": submission.work_item,
    }
    return SCOPE_RUBRIC.read_text() + "\nReturn only JSON, without fences.\n" + json.dumps(evidence)


def _run_codex_classifier(prompt: str) -> str:
    command = [
        "codex", "--no-daemon", "exec", "--disable", "hooks", "--ephemeral", "--skip-git-repo-check",
        "--output-schema", str(RESOURCES / "grade.json"),
        "-s", "read-only", "-m", "gpt-6.2-sol", "-c", 'model_reasoning_effort="low"', "-",
    ]
    result = subprocess.run(
        command,
        input=prompt,
        env={k: v for k, v in os.environ.items() if k != "JEV_API_KEY"},
        text=True, capture_output=True, timeout=75, check=True,
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

    return Assessment(kind, score, fields["reason"], fields["replacement"], fields["criteria"])
