from pathlib import Path
from typing import Any
from work_hooks.core.evaluate_submission import evaluate_submission
from work_hooks.ports.scope_classifier import ScopeClassifier
from work_hooks.adapters import sessions
from work_hooks.adapters.codex.reviews import parallel_review


def dispatch(event: dict[str, Any], classify: ScopeClassifier) -> dict[str, Any]:
    directory = sessions.session_directory(event["session_id"])
    ready = directory / "review-ready"
    session = sessions.load(directory)
    if event["hook_event_name"] == "UserPromptSubmit":
        decision = evaluate_submission(event["prompt"], session, classify)
        sessions.save(directory, decision.session)
        if decision.review:
            ready.touch()
        else:
            ready.unlink(missing_ok=True)
        if decision.blocked:
            return {"decision": "block", "reason": decision.message}
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                       "additionalContext": decision.message}}

    if event["hook_event_name"] == "Stop" and ready.exists() and not event["stop_hook_active"]:
        report = directory / "review.md"
        report.write_text(parallel_review(Path(event["cwd"]), session.approved))
        ready.unlink()
        return {"decision": "block", "reason": f"Read {report}. Verify findings and fix confirmed issues."}
    return {}
