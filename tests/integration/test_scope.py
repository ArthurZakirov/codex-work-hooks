import json
import os
import subprocess
import sys
from pathlib import Path
from pytest_bdd import given, when, then, scenarios
from work_hooks.adapters import sessions
from work_hooks.adapters.classifiers import codex, jev
from work_hooks.adapters.criteria import SessionCriteria
from work_hooks.core.models import Session
from work_hooks.core.evaluate_submission import evaluate_submission

scenarios("scope.feature")
TICKET = Path(__file__).resolve().parents[1] / "fixtures/dispatch_api/OPS-17.md"


@given("the team has supplied no ticket or other verified requirements", target_fixture="chat")
def fresh_chat(tmp_path):
    return {"session": Session(ownership="professional"), "source": SessionCriteria(tmp_path)}


@given("a ticket with verified acceptance criteria is selected", target_fixture="chat")
def chat_with_ticket(tmp_path):
    chat = fresh_chat(tmp_path)
    if not chat["source"].record("Work item: OPS-17\nSource: team brief OPS-17\nAcceptance criteria:\n" + TICKET.read_text()):
        raise RuntimeError("Could not prepare the selected fixture ticket")
    return chat


@when("the user asks to implement a feature for the team")
def request_feature(chat):
    submit(chat, "Implement DELETE /manifests/{id} for the dispatch team.")


@when("the user requests the change specified by the ticket")
def request_ticket_scope(chat):
    submit(chat, "Implement the endpoint described in our ticket.")


@when("the user requests additional work without showing why a criterion requires it")
def request_extra_work(chat):
    submit(chat, "Provision a separate system-test environment and test the API over HTTP.")


@when("the user justifies the additional work with a personal preference")
def give_preference(chat):
    submit(chat, "Do it because I like having more tests.")


@when("the user explains why a focused change is necessary to verify a specific criterion")
def justify_necessity(chat):
    submit(chat, "Instead use a focused localhost HTTP test for OPS-17: the unit response mock drops bodies, so only a real HTTP response can verify the required empty 204 body. No new environment.")


@when("the user asks for help with their own development setup")
def request_personal_help(chat):
    submit(chat, "Investigate why my personal Codex coding standards skill never triggers on my laptop.")


def submit(chat, prompt):
    provider = {"jev": jev, "codex": codex}[os.getenv("WORK_HOOKS_CLASSIFIER", "codex")]
    decision = evaluate_submission(prompt, chat["session"], provider, chat["source"], "probe")
    chat.update(session=decision.session, decision=decision, prompt=prompt)


@then("implementation is blocked")
def blocked(chat):
    assert chat["session"].ownership == "professional"
    assert chat["decision"].blocked, chat["decision"]


@then("implementation may begin")
def approved(chat):
    assert chat["session"].ownership == "professional"
    assert not chat["decision"].blocked
    assert chat["prompt"] in chat["session"].approved


@then("the personal request may proceed")
def personal(chat):
    assert chat["session"].ownership == "personal"
    assert not chat["decision"].blocked
    assert chat["prompt"] in chat["session"].approved


@then("implementation is blocked and the requester is asked for the originating ticket or colleague message")
def missing_requirements(chat):
    decision = chat["decision"]
    assert chat["session"].ownership == "professional"
    assert decision.blocked and not decision.session.approved
    assert "No verified requirements" in decision.message
    assert "ticket or colleague message" in decision.message


@when("the user discusses and revises a PR announcement and requests the originating ticket")
def continue_workflow(chat):
    chat["original_pending"] = chat["session"].pending
    chat["workflow"] = []
    for prompt in (
        "What about Delta? You omitted it from the shared fields sentence but included it in the general template sentence. Why?",
        "Revise the Slack PR review announcement in draft.md to make that distinction clear.",
        "Fetch Jira OPS-17 to set up the work item.",
    ):
        submit(chat, prompt)
        chat["workflow"].append(chat["decision"])


@then("each workflow request proceeds and the implementation remains pending")
def workflow_allowed(chat):
    for decision in chat["workflow"]:
        assert not decision.blocked, decision
        assert decision.session.pending == chat["original_pending"]
        assert not decision.session.approved


@when("the user combines ticket lookup with an unrelated refactor")
def mixed_request(chat):
    submit(chat, "Fetch OPS-17 and refactor the entire dispatch service into a new architecture.")


@when("the user clarifies that the current project is personal")
def clarify_ownership(chat):
    submit(chat, "This is my personal project, not work.")


@when("the user asks to proceed without restating the task")
def continue_implementation(chat):
    submit(chat, "fo implement")


@when("the user builds an agent to improve their own development workflow")
def build_developer_tool(chat):
    submit(chat, "Build me a coding agent that organizes my debugging notes so I can work faster on my team's Java services.")


@when("the user builds an agent as a team deliverable")
def build_team_agent(chat):
    submit(chat, "Our platform team commissioned an agent that diagnoses vulnerabilities in company Java services. Implement that service for the team.")


@given("the assistant has proposed a private developer workflow change")
def offer_personal_tool(chat, tmp_path, monkeypatch):
    record_reply(chat, tmp_path, monkeypatch, "I can build a debugging-notes assistant for your own development workflow. Shall I implement it?")


@given("the assistant has proposed a change to the team's service")
def offer_team_change(chat, tmp_path, monkeypatch):
    record_reply(chat, tmp_path, monkeypatch, "I can add a deletion endpoint to the team's dispatch service. Shall I implement it?")


def record_reply(chat, tmp_path, monkeypatch, message):
    monkeypatch.setenv("PLUGIN_DATA", str(tmp_path))
    directory = sessions.session_directory("probe")
    sessions.save(directory, chat["session"])
    event = {"session_id": "probe", "hook_event_name": "Stop", "last_assistant_message": message}
    dispatcher = Path(__file__).resolve().parents[2] / "src/scope-check/hooks/dispatch.py"
    subprocess.run([sys.executable, dispatcher], input=json.dumps(event), text=True, check=True)
    chat["session"] = sessions.load(directory)


@when("the user says go")
def say_go(chat):
    submit(chat, "go")


@given("the assistant has proposed an unrelated team feature")
def offer_unrelated_feature(chat, tmp_path, monkeypatch):
    record_reply(chat, tmp_path, monkeypatch, "I can add weekly billing forecasts to our dispatch team's service. Shall I implement that?")
