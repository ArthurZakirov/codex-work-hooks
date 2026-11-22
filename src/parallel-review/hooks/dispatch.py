"""Collect successful patches by turn; hand off one report per batch of new edits."""
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

from patches import review_inputs
from reviews import parallel_review


def handle(event: dict) -> dict:
    directory = _turn_directory(event)
    if event["hook_event_name"] == "PostToolUse":
        groups = review_inputs(event)
        if groups:
            _record_edit(directory, event["tool_use_id"], groups)
    elif event["hook_event_name"] == "Stop" and (directory / "edits.db").is_file():
        return _review_pending(directory)
    return {}


def _turn_directory(event: dict) -> Path:
    identity = json.dumps([event["session_id"], event["turn_id"]]).encode()
    return Path(os.environ["PLUGIN_DATA"]) / sha256(identity).hexdigest()


def _record_edit(directory: Path, call_id: str, groups: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sqlite3.connect(directory / "edits.db", timeout=260) as db:
        db.execute("CREATE TABLE IF NOT EXISTS edits (call_id TEXT UNIQUE, groups TEXT, reviewed INTEGER DEFAULT 0)")
        db.execute("INSERT OR IGNORE INTO edits(call_id, groups) VALUES (?, ?)", (call_id, json.dumps(groups)))


def _review_pending(directory: Path) -> dict:
    limit = _max_review_passes()
    pass_number, groups = _claim_review_pass(directory, limit)
    if not groups:
        return {}

    filename = "review.md" if pass_number == 1 else f"review-{pass_number}.md"
    report = directory / filename
    report.write_text(parallel_review(groups))
    budget = f"{pass_number}/{limit}" if limit is not None else str(pass_number)
    return {"decision": "block", "reason": f"Review pass {budget}. Read {report}. Verify findings against the recorded edits and fix confirmed issues."}


def _max_review_passes() -> int | None:
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    settings = home / "parallel-review.json"
    if not settings.exists():
        return 1

    try:
        value = json.loads(settings.read_text()).get("max_review_passes", 1)
    except (ValueError, AttributeError):
        raise ValueError(f"Expected a JSON object in {settings}.") from None
    if value == "unlimited":
        return None
    if type(value) is int and value >= 0:
        return value
    raise ValueError(f'In {settings}, set max_review_passes to a nonnegative integer or "unlimited".')


def _claim_review_pass(directory: Path, limit: int | None) -> tuple[int, dict[str, list[str]]]:
    """Assign pending edits a pass number before spending tokens, including on retries."""
    with sqlite3.connect(directory / "edits.db", timeout=260) as db:
        db.execute("BEGIN IMMEDIATE")
        previous, = db.execute("SELECT COALESCE(MAX(reviewed), 0) FROM edits").fetchone()
        if limit is not None and previous >= limit:
            return 0, {}

        pending = db.execute("SELECT groups FROM edits WHERE reviewed = 0 ORDER BY rowid")
        groups: dict[str, list[str]] = {}
        for (encoded,) in pending:
            for category, sections in json.loads(encoded).items():
                groups.setdefault(category, []).extend(sections)

        number = previous + 1
        db.execute("UPDATE edits SET reviewed = ? WHERE reviewed = 0", (number,))
        return number, groups


if __name__ == "__main__":
    try:
        print(json.dumps(handle(json.load(sys.stdin))))
    except (RuntimeError, ValueError, OSError, sqlite3.Error, subprocess.TimeoutExpired) as error:
        print(json.dumps({"decision": "block", "reason": f"Parallel review failed: {error}"}))
