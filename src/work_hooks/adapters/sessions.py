"""Per-chat state in Codex's writable plugin data directory."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from work_hooks.core.models import Session


def session_directory(session_id: str) -> Path:
    directory = Path(os.environ["PLUGIN_DATA"]) / sha256(session_id.encode()).hexdigest()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    return directory


def load(directory: Path) -> Session:
    path = directory / "session.json"
    return Session(**json.loads(path.read_text())) if path.exists() else Session()


def save(directory: Path, session: Session) -> None:
    with NamedTemporaryFile(mode="w", dir=directory, delete=False) as stream:
        json.dump(asdict(session), stream)
    Path(stream.name).replace(directory / "session.json")
