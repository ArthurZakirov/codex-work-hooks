import json
import os
from pathlib import Path
import subprocess

from pytest_bdd import given, scenarios, then, when

scenarios("review.feature")
ROOT = Path(__file__).resolve().parents[2]


@given("a Codex workspace with only Parallel Review installed", target_fixture="chat")
def review_chat(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()
    auth = Path(os.environ["WORK_HOOKS_TEST_AUTH_HOME"]) / "auth.json"
    (home / "auth.json").symlink_to(auth)
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "service.py").write_bytes((ROOT / "tests/fixtures/dispatch_api/service.py").read_bytes())
    subprocess.run(["git", "init", "-q"], check=True, cwd=workspace)
    env = dict(os.environ, CODEX_HOME=str(home), HOME=str(tmp_path))
    env.pop("JEV_API_KEY", None)
    for args in (["marketplace", "add", str(ROOT)], ["add", "parallel-review@work-hooks"]):
        subprocess.run(["codex", "plugin", *args], env=env, cwd=workspace, check=True)
    return home, workspace, env


@when("the user makes a documentation edit", target_fixture="events")
def request_handoff(chat):
    prompt = ("Use the native apply_patch tool to add NOTES.md containing only # Notes. If a hook requests a report, read it and name "
              "the review section in your final message.")
    return _run_turn(chat, prompt)


@when("the user asks a discussion question", target_fixture="discussion")
def discuss(chat):
    return _run_turn(chat, "What is a file extension? Answer in one sentence without editing files.")


@then("the turn completes without recording edits or producing a report")
def verify_discussion(chat, discussion):
    home, _, _ = chat
    assert discussion[-1]["type"] == "turn.completed"
    assert not list(home.rglob("edits.db"))
    assert not list(home.rglob("review.md"))


def _run_turn(chat, prompt):
    _, workspace, env = chat
    output = subprocess.check_output(
        ["codex", "--no-daemon", "exec", "--json", "--trust", "--dangerously-bypass-hook-trust",
         "--skip-git-repo-check", "-s", "workspace-write", "-m", "gpt-6-luna",
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
    assert "markdown" in replies[-1], replies
    assert [s.splitlines()[0] for s in report.read_text().split("\n## ")[1:]] == ["Markdown"]
