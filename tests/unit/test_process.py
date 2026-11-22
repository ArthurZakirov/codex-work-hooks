import sys

import pytest

from work_hooks.adapters.process import HookCommandError, run_command


def test_error_names_stage_and_exit_status_without_echoing_child_output():
    command = [sys.executable, "-c", "import sys; sys.stderr.write('private prompt'); sys.exit(17)"]
    with pytest.raises(HookCommandError) as failure:
        run_command("Codex classifier (ownership)", command, input="", timeout=5)
    message = str(failure.value)
    assert "Codex classifier (ownership)" in message
    assert "exited 17" in message
    assert "private prompt" not in message
