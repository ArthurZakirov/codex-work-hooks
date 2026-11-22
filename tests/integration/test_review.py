"""Run the review hook with real local Codex reviewers and no scope plugin."""
import json
import os
from pathlib import Path
import subprocess
import sys

from pytest_bdd import given, scenarios, then, when

scenarios("review.feature")
ROOT = Path(__file__).resolve().parents[2]


@given("a completed request in a sample workspace", target_fixture="workspace")
def sample_workspace(tmp_path):
    (tmp_path / "service.py").write_bytes((ROOT / "tests/fixtures/dispatch_api/service.py").read_bytes())
    return tmp_path


def send(workspace, event, **fields):
    env = dict(os.environ, PLUGIN_DATA=str(workspace.parent / "review-state"))
    env.pop("JEV_API_KEY", None)
    payload = dict(hook_event_name=event, session_id="review-test", cwd=str(workspace), **fields)
    result = subprocess.check_output(
        [sys.executable, ROOT / "src/parallel-review/hooks/dispatch.py"],
        input=json.dumps(payload), text=True, env=env, cwd=workspace, timeout=280,
    )
    return json.loads(result)


@when("the review plugin receives the submission and stop events", target_fixture="handoff")
def review(workspace):
    send(workspace, "UserPromptSubmit", prompt="Review the existing service.py. Keep feedback brief.")
    return send(workspace, "Stop", stop_hook_active=False)


@then("it returns a report with findings from each review perspective")
def verify_report(workspace, handoff):
    report, = (workspace.parent / "review-state").rglob("review.md")
    assert handoff["decision"] == "block" and str(report) in handoff["reason"]
    sections = report.read_text().split("\n## ")[1:]
    assert [s.splitlines()[0] for s in sections] == ["Experience", "Standards", "Correctness"]
    assert all(s.partition("\n")[2].strip() for s in sections)


@then("a follow-up stop does not request another review")
def verify_followup(workspace):
    assert send(workspace, "Stop", stop_hook_active=True) == {}
