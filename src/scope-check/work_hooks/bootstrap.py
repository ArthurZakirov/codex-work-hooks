from dataclasses import replace
from pathlib import Path
import json
import os
import sys
from work_hooks.adapters.classifiers import codex, jev
from work_hooks.adapters.criteria import SessionCriteria
from work_hooks.adapters.demo_ticket import DemoTicket
from work_hooks.adapters import sessions
from work_hooks.adapters.process import HookCommandError
from work_hooks.adapters.codex.events import dispatch


def main() -> None:
    try:
        classify = {"codex": codex, "jev": jev}[os.getenv("WORK_HOOKS_CLASSIFIER", "codex")]
        event = json.load(sys.stdin)
        directory = sessions.session_directory(event["session_id"])
        requirements = SessionCriteria(directory)
        if event["hook_event_name"] == "Stop":
            reply = event.get("last_assistant_message") or ""
            sessions.save(directory, replace(sessions.load(directory), previous_assistant_reply=reply))
            awaiting = directory / "awaiting-criteria"
            if awaiting.exists():
                saved = requirements.record(reply)
                unavailable = reply.lstrip().startswith("Source unavailable:")
                if not saved and not unavailable and not event.get("stop_hook_active"):
                    print(json.dumps({"decision": "block", "reason":
                        "Criteria were not saved. Return the requested plain-text work-item receipt, "
                        "or begin with 'Source unavailable:' and explain what is missing."}))
                    return
                awaiting.unlink(missing_ok=True)
            print("{}")
            return
        fixture = os.getenv("WORK_HOOKS_DEMO_TICKET")
        if fixture:
            directory = sessions.session_directory(event["session_id"])
            requirements = DemoTicket(Path(fixture), directory)
            if event["hook_event_name"] == "UserPromptSubmit" and requirements.select(event["prompt"]):
                sessions.save(directory, replace(sessions.load(directory), ownership="professional"))
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                    "additionalContext": "Acknowledge the selected demo ticket and await the next request."}}))
                return
        response = dispatch(event, classify, requirements)
    except HookCommandError as error:
        response = {"decision": "block", "reason": str(error)}
    except Exception as error:
        response = {"decision": "block", "reason": f"Work hook failed ({type(error).__name__}). Check plugin configuration."}
    print(json.dumps(response))
