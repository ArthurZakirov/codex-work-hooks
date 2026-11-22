"""Real installed hooks and a read-only worker. No implementation is requested."""
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

from pytest_bdd import given, when, then, scenarios

scenarios("codex_submission.feature")

ROOT = Path(__file__).resolve().parents[2]


@given("a fresh read-only Codex workspace with Work Hooks installed and no selected ticket", target_fixture="chat")
def installed_chat(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()
    auth = Path(os.environ["WORK_HOOKS_TEST_AUTH_HOME"]) / "auth.json"
    (home / "auth.json").symlink_to(auth)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    fixture = ROOT / "tests/fixtures/dispatch_api/service.py"
    service = workspace / "service.py"
    service.write_bytes(fixture.read_bytes())
    ticket = ROOT / "tests/fixtures/dispatch_api/OPS-17.md"
    env = dict(os.environ, CODEX_HOME=str(home), HOME=str(tmp_path),
               WORK_HOOKS_DEMO_TICKET=str(ticket))
    env.pop("WORK_HOOKS_CLASSIFIER", None)

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["codex", "--no-daemon", *args], env=env, cwd=workspace,
                              text=True, capture_output=True, timeout=100)

    run("plugin", "marketplace", "add", str(ROOT)).check_returncode()
    run("plugin", "add", "work-hooks@work-hooks").check_returncode()
    flags = ["exec", "--json", "--trust", "--dangerously-bypass-hook-trust",
             "--skip-git-repo-check", "-s", "read-only", "-m", "gpt-6-luna",
             "-c", 'model_reasoning_effort="low"']

    return SimpleNamespace(run=run, flags=flags, home=home, ticket=ticket, service=service, fixture=fixture)


@when("the user requests a feature for the team", target_fixture="first_turn")
def request_endpoint(chat):
    prompt = "Implement DELETE /manifests/{id} for our dispatch team."
    result = chat.run(*chat.flags, prompt)
    result.check_returncode()
    return prompt, [json.loads(line) for line in result.stdout.splitlines()]


@then("the request is pending and the worker has used no model tokens")
def check_block(chat, first_turn):
    prompt, events = first_turn
    usage = next(event["usage"] for event in events if event["type"] == "turn.completed")
    assert usage["input_tokens"] == usage["output_tokens"] == 0
    state, = chat.home.rglob("session.json")
    assert json.loads(state.read_text())["pending"] == prompt


@when("the user supplies the originating ticket in the same chat", target_fixture="ticket_turn")
def submit_ticket(chat, first_turn):
    _, events = first_turn
    thread = next(event["thread_id"] for event in events if event["type"] == "thread.started")

    accepted = chat.run(*chat.flags, "resume", thread, f"Here is our Jira ticket: {chat.ticket}. Acknowledge with TICKET_RECEIVED only.")
    accepted.check_returncode()
    return [json.loads(line) for line in accepted.stdout.splitlines()]


@then("the hook selects the ticket and the worker acknowledges it")
def check_acknowledgment(chat, ticket_turn):
    events = ticket_turn
    messages = [e["item"]["text"] for e in events if e.get("type") == "item.completed"
                and e.get("item", {}).get("type") == "agent_message"]
    assert any("TICKET_RECEIVED" in text for text in messages), messages
    assert list(chat.home.rglob("demo-ticket")), "Expected the real hook to select the ticket"


@then("the application code remains unchanged")
def check_service(chat):
    assert chat.service.read_bytes() == chat.fixture.read_bytes()
