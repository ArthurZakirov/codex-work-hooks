"""Resolve the Jev credential in the hook process, including a macOS login keychain."""
import os
import subprocess
import sys

from work_hooks.adapters.process import HookCommandError

SERVICE = "codex-work-hooks.jev"


def resolve_key() -> str:
    exported = os.getenv("JEV_API_KEY")
    if exported:
        return exported

    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["/usr/bin/security", "find-generic-password", "-s", SERVICE, "-w"],
                capture_output=True, text=True, check=False, timeout=20,
            )
        except subprocess.TimeoutExpired:
            raise HookCommandError("Scope Check timed out waiting for macOS Keychain access. Unlock the login keychain and allow access to codex-work-hooks.jev.") from None
        if result.returncode == 0 and result.stdout.rstrip("\n"):
            return result.stdout.rstrip("\n")

    raise HookCommandError(
        "Scope Check could not access the Jev credential. On macOS add a login keychain "
        "password named codex-work-hooks.jev. Alternatively export JEV_API_KEY and start codex --no-daemon."
    )
