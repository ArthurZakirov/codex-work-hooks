"""Opt-in, single-ticket simulator. Never resolves a user-supplied filesystem path."""
from pathlib import Path
from work_hooks.ports.requirements import Requirement


class DemoTicket:
    def __init__(self, ticket: Path, session_dir: Path):
        self.ticket = ticket.resolve()
        self.selection = session_dir / "demo-ticket"

    def select(self, prompt: str) -> bool:
        references = (self.ticket.read_text().strip(), str(self.ticket), self.ticket.name)
        if not any(reference in prompt for reference in references):
            return False
        self.selection.write_text(str(self.ticket))
        return True

    def __call__(self, session_id: str) -> tuple[Requirement, ...]:
        if not self.selection.exists() or self.selection.read_text() != str(self.ticket):
            return ()
        return (Requirement(self.ticket.stem, "fixture", "Dispatch Operations", self.ticket.read_text()),)
