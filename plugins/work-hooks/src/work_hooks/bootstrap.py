import json
import os
import sys
from work_hooks.adapters.classifiers import codex, jev
from work_hooks.adapters.codex.events import dispatch


def main() -> None:
    try:
        classify = {"codex": codex.classify, "jev": jev.classify}[os.getenv("WORK_HOOKS_CLASSIFIER", "codex")]
        response = dispatch(json.load(sys.stdin), classify)
    except Exception as error:
        response = {"decision": "block", "reason": f"Work hook failed ({type(error).__name__}). Check plugin configuration."}
    print(json.dumps(response))
