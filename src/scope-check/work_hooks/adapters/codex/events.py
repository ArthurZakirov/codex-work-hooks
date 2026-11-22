from typing import Any
from work_hooks.core.evaluate_submission import evaluate_submission
from work_hooks.ports.requirements import Requirements
from work_hooks.ports.scope_classifier import ScopeClassifier
from work_hooks.adapters import sessions


def dispatch(event: dict[str, Any], classify: ScopeClassifier, requirements: Requirements) -> dict[str, Any]:
    directory = sessions.session_directory(event["session_id"])
    session = sessions.load(directory)
    decision = evaluate_submission(event["prompt"], session, classify, requirements, event["session_id"])
    sessions.save(directory, decision.session)
    if decision.blocked:
        return {"decision": "block", "reason": decision.message}
    if not decision.message:
        return {}
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                   "additionalContext": decision.message}}
