from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[2] / "src/parallel-review/hooks"


@pytest.fixture
def hook(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(HOOKS))
    monkeypatch.setenv("PLUGIN_DATA", str(tmp_path / "state"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    import dispatch
    calls = []

    def review(groups):
        calls.append(groups)
        return "report"

    monkeypatch.setattr(dispatch, "parallel_review", review)

    def send(kind, turn="first", **fields):
        return dispatch.handle(dict(hook_event_name=kind, session_id="worker", turn_id=turn, **fields))

    return send, calls


def patch(name, text, call, *, success=True):
    return dict(tool_name="apply_patch", tool_use_id=call,
                tool_input={"command": f"*** Begin Patch\n*** Add File: {name}\n+{text}\n*** End Patch"},
                tool_response=f"Exit code: {0 if success else 1}\n")


def test_reviews_only_accepted_edits_once_and_for_their_own_turn(hook):
    send, calls = hook
    send("PostToolUse", **patch("failed.py", "failed", "f", success=False))
    send("PostToolUse", **patch("image.png", "unsupported", "u"))
    assert send("Stop") == {} and not calls

    first = patch("a.py", "print(1)", "a")
    send("PostToolUse", **first)
    send("PostToolUse", **first)
    send("PostToolUse", **patch("b.py", "print(2)", "b"))
    assert send("Stop", turn="other") == {}
    assert send("Stop")["decision"] == "block"
    assert calls == [{"code": ["*** Add File: a.py\n+print(1)", "*** Add File: b.py\n+print(2)"]}]
    assert send("Stop", stop_hook_active=True) == {}

    send("PostToolUse", **patch("NOTES.md", "# Notes", "c"))
    assert send("Stop", stop_hook_active=True) == {}
    assert len(calls) == 1
    send("PostToolUse", turn="next", **patch("new.py", "x=1", "d"))
    assert send("Stop", turn="next")["decision"] == "block"
    assert len(calls) == 2


def test_mixed_patch_routes_by_destination_including_move(hook):
    send, calls = hook
    event = patch("unused", "", "mixed")
    event["tool_input"]["command"] = (
        "*** Begin Patch\n*** Update File: old.txt\n*** Move to: Guide.MD\n@@\n-old\n+new\n"
        "*** Delete File: unused.py\n*** End Patch")
    send("PostToolUse", **event)
    send("Stop")
    groups, = calls
    assert groups["code"] == ["*** Delete File: unused.py"]
    assert groups["markdown"] == ["*** Update File: old.txt\n*** Move to: Guide.MD\n@@\n-old\n+new"]


def test_model_inputs_are_limited_to_assigned_edits_and_guidance(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.syspath_prepend(str(HOOKS))
    import reviews
    guide = tmp_path / "guide.md"
    guide.write_text("MARKDOWN_GUIDANCE_CANARY")
    monkeypatch.setenv("WORK_HOOKS_MARKDOWN_GUIDE", str(guide))
    prompts = []

    def capture(command, *, input, cwd, **options):
        assert not list(Path(cwd).iterdir())
        assert "--ignore-user-config" in command
        prompts.append(input)
        return SimpleNamespace(returncode=0, stdout="No findings.")

    monkeypatch.setattr(reviews.subprocess, "run", capture)
    reviews.parallel_review({"code": ["PYTHON_CANARY"], "markdown": ["MARKDOWN_CANARY"]})

    assert len(prompts) == 4
    for prompt in prompts:
        assert ("PYTHON_CANARY" in prompt) != ("MARKDOWN_CANARY" in prompt)
        assert ("MARKDOWN_CANARY" in prompt) == ("MARKDOWN_GUIDANCE_CANARY" in prompt)


@pytest.mark.parametrize(("setting", "expected"), [(0, 0), (2, 2), (3, 3), ("unlimited", 5)])
def test_configured_budget_counts_batches_with_new_edits(hook, tmp_path, setting, expected):
    import json

    (tmp_path / "parallel-review.json").write_text(json.dumps({"max_review_passes": setting}))
    send, calls = hook
    for index in range(5):
        send("PostToolUse", **patch("a.py", f"x={index}", str(index)))
        response = send("Stop", stop_hook_active=index > 0)
        assert bool(response) == (index < expected)
        assert send("Stop", stop_hook_active=True) == {}
    assert len(calls) == expected


def test_failed_reviewer_does_not_repeatedly_spend_the_turn_budget(hook, monkeypatch):
    import dispatch

    send, _ = hook
    def unavailable(groups):
        raise RuntimeError("reviewer unavailable")

    monkeypatch.setattr(dispatch, "parallel_review", unavailable)
    send("PostToolUse", **patch("sample.py", "x=1", "first"))
    with pytest.raises(RuntimeError, match="reviewer unavailable"):
        send("Stop")
    send("PostToolUse", **patch("sample.py", "x=2", "retry"))
    assert send("Stop") == {}
