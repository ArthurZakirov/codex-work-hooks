from types import SimpleNamespace

import pytest

from work_hooks.adapters import jev_key
from work_hooks.adapters.process import HookCommandError


def test_exported_key_takes_precedence(monkeypatch):
    monkeypatch.setenv("JEV_API_KEY", "synthetic-shell-value")
    assert jev_key.resolve_key() == "synthetic-shell-value"


@pytest.mark.parametrize("exit_code", [0, 44])
def test_keychain_lookup_without_shell_export(monkeypatch, exit_code):
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.setattr(jev_key.sys, "platform", "darwin")
    result = SimpleNamespace(returncode=exit_code, stdout="synthetic-keychain-value\n")
    monkeypatch.setattr(jev_key.subprocess, "run", lambda *args, **kwargs: result)

    if exit_code == 0:
        assert jev_key.resolve_key() == "synthetic-keychain-value"
    else:
        with pytest.raises(HookCommandError, match="codex-work-hooks.jev"):
            jev_key.resolve_key()
