import os
from pathlib import Path
from pytest_bdd import given, when, then, scenarios
from work_hooks.adapters.classifiers import codex, jev
from work_hooks.adapters.demo_ticket import DemoTicket
from work_hooks.core.models import Session
from work_hooks.core.evaluate_submission import evaluate_submission

scenarios("scope.feature")
TICKET = Path(__file__).resolve().parents[1] / "fixtures/dispatch_api/OPS-17.md"


@given("the team has supplied no ticket or other verified requirements", target_fixture="chat")
def fresh_chat(tmp_path):
    return {"session": Session(ownership="professional"), "source": DemoTicket(TICKET, tmp_path)}


@given("a ticket with verified acceptance criteria is selected", target_fixture="chat")
def chat_with_ticket(tmp_path):
    chat = fresh_chat(tmp_path)
    if not chat["source"].select("Here is our Jira ticket: " + TICKET.read_text()):
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
    provider = {"jev": jev, "codex": codex}[os.getenv("WORK_HOOKS_CLASSIFIER", "jev")]
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
