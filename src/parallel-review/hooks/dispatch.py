"""Remember the request and return one report per completed turn."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from reviews import parallel_review


def handle(event: dict) -> dict:
    session = sha256(event["session_id"].encode()).hexdigest()
    directory = Path(os.environ["PLUGIN_DATA"]) / session
    request = directory / "request.txt"

    if event["hook_event_name"] == "UserPromptSubmit":
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        request.write_text(event["prompt"])
        return {}

    if event.get("stop_hook_active") or not request.exists():
        return {}

    report = directory / "review.md"
    report.write_text(parallel_review(Path(event["cwd"]), request.read_text()))
    request.unlink()
    return {"decision": "block", "reason": f"Read {report}. Verify findings and fix confirmed issues."}


if __name__ == "__main__":
    try:
        print(json.dumps(handle(json.load(sys.stdin))))
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"decision": "block", "reason": f"Parallel review failed: {error}"}))
