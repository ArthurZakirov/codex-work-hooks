import json
import os
from pathlib import Path
import subprocess

from pytest_bdd import given, scenarios, then, when

scenarios("review.feature")
ROOT = Path(__file__).resolve().parents[2]


@given("a read-only Codex workspace with only Parallel Review installed", target_fixture="chat")
def review_chat(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()
    auth = Path(os.environ["WORK_HOOKS_TEST_AUTH_HOME"]) / "auth.json"
    (home / "auth.json").symlink_to(auth)
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "service.py").write_bytes((ROOT / "tests/fixtures/dispatch_api/service.py").read_bytes())
    env = dict(os.environ, CODEX_HOME=str(home), HOME=str(tmp_path))
    env.pop("JEV_API_KEY", None)
    for args in (["marketplace", "add", str(ROOT)], ["add", "parallel-review@work-hooks"]):
        subprocess.run(["codex", "plugin", *args], env=env, cwd=workspace, check=True)
    return home, workspace, env


@when("the user asks for a handoff", target_fixture="events")
def request_handoff(chat):
    _, workspace, env = chat
    prompt = ("Say READY. If a hook asks you to read a report, read it, then reply with "
              "the names of its three sections. Make no edits.")
    output = subprocess.check_output(
        ["codex", "--no-daemon", "exec", "--json", "--trust", "--dangerously-bypass-hook-trust",
         "--skip-git-repo-check", "-s", "read-only", "-m", "gpt-6-luna",
         "-c", 'model_reasoning_effort="low"', prompt],
        env=env, cwd=workspace, text=True, timeout=320,
    )
    return [json.loads(line) for line in output.splitlines()]


@then("the worker receives the review report and completes the turn")
def verify_handoff(chat, events):
    home, _, _ = chat
    report, = home.rglob("review.md")
    assert report.stat().st_size > 0
    assert events[-1]["type"] == "turn.completed"
    replies = [event["item"]["text"].lower() for event in events if event["type"] == "item.completed"
               and event["item"]["type"] == "agent_message"]
    assert all(role in replies[-1] for role in ("experience", "standards", "correctness")), replies
