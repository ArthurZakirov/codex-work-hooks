"""Persist the worker's source-attributed handoff in its Codex session."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from work_hooks.ports.requirements import Requirement


class SessionCriteria:
    def __init__(self, directory: Path) -> None:
        self.path = directory / "work-item.json"

    def __call__(self, session_id: str) -> tuple[Requirement, ...]:
        if not self.path.exists():
            return ()
        return tuple(Requirement(**row) for row in json.loads(self.path.read_text())["records"])

    def record(self, reply: str) -> bool:
        handoff = re.fullmatch(r"Work item: ([^\n]+)\nSource: ([^\n]+)\nAcceptance criteria:\n(.+)",
                               reply.strip(), re.DOTALL)
        if not handoff:
            return False
        item, source, criteria = (part.strip() for part in handoff.groups())
        if not all((item, source, criteria)):
            return False
        previous = json.loads(self.path.read_text()) if self.path.exists() else {}
        records = previous.get("records", []) if previous.get("item") == item else []
        record = Requirement(source, datetime.now(timezone.utc).isoformat(), "source supplied in chat", criteria)
        records = [row for row in records if row["source_ref"] != source] + [asdict(record)]
        with NamedTemporaryFile(mode="w", dir=self.path.parent, delete=False) as stream:
            json.dump({"item": item, "records": records}, stream)
        Path(stream.name).replace(self.path)
        return True
