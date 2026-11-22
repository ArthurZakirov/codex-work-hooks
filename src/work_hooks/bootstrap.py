from dataclasses import replace
from pathlib import Path
import json
import os
import sys
from work_hooks.adapters.classifiers import codex, jev
from work_hooks.ports.requirements import unavailable
from work_hooks.adapters.demo_ticket import DemoTicket
from work_hooks.adapters import sessions
from work_hooks.adapters.process import HookCommandError
from work_hooks.adapters.codex.events import dispatch


def main() -> None:
    try:
        classify = {"codex": codex, "jev": jev}[os.getenv("WORK_HOOKS_CLASSIFIER", "jev")]
        event = json.load(sys.stdin)
        requirements = unavailable
        fixture = os.getenv("WORK_HOOKS_DEMO_TICKET")
        if fixture:
            directory = sessions.session_directory(event["session_id"])
            requirements = DemoTicket(Path(fixture), directory)
            if event["hook_event_name"] == "UserPromptSubmit" and requirements.select(event["prompt"]):
                sessions.save(directory, replace(sessions.load(directory), ownership="professional"))
                (directory / "review-ready").unlink(missing_ok=True)
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                    "additionalContext": "Acknowledge the selected demo ticket and await the next request."}}))
                return
        response = dispatch(event, classify, requirements)
    except HookCommandError as error:
        response = {"decision": "block", "reason": str(error)}
    except Exception as error:
        response = {"decision": "block", "reason": f"Work hook failed ({type(error).__name__}). Check plugin configuration."}
    print(json.dumps(response))
