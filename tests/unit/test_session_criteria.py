from pathlib import Path

from work_hooks.adapters.criteria import SessionCriteria


def test_session_reload_refresh_clarification_and_switch(tmp_path: Path) -> None:
    def store(item: str, source: str, text: str) -> None:
        assert SessionCriteria(tmp_path).record(f"Work item: {item}\nSource: {source}\nAcceptance criteria:\n{text}")

    store("A", "brief", "Original")
    store("A", "comment", "Clarification")
    store("A", "brief", "Amended")
    assert {r.text for r in SessionCriteria(tmp_path)("chat")} == {"Amended", "Clarification"}

    store("B", "another brief", "Second task")
    assert [r.text for r in SessionCriteria(tmp_path)("chat")] == ["Second task"]


def test_unattributed_reply_stores_nothing(tmp_path: Path) -> None:
    source = SessionCriteria(tmp_path)
    assert not source.record("Acceptance criteria: add a blue elephant")
    assert source("chat") == ()
