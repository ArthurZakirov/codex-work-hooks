"""Report actionable subprocess failures without echoing prompts or credentials."""
import subprocess


class HookCommandError(Exception):
    """Safe to display in Codex."""


def run_command(stage: str, command: list[str], *, input: str, timeout: int,
                env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, input=input, env=env, text=True,
                              capture_output=True, timeout=timeout, check=True)
    except FileNotFoundError:
        raise HookCommandError(f"{stage}: {command[0]} is missing from the hook's PATH.") from None
    except subprocess.TimeoutExpired:
        raise HookCommandError(f"{stage}: {command[0]} timed out after {timeout}s.") from None
    except subprocess.CalledProcessError as error:
        detail = _failure_hint(error.stderr or "", command[0], error.returncode)
        raise HookCommandError(f"{stage}: {command[0]} exited {error.returncode}. {detail}") from None


def _failure_hint(stderr: str, executable: str, code: int) -> str:
    message = stderr.lower()
    if executable == "curl":
        if "401" in message or "403" in message:
            return "TypeSafe denied access. Check the Jev credential in the launching shell."
        if "429" in message:
            return "TypeSafe rate limited the request."
        if "variable" in message or "unknown option" in message:
            return "Check that JEV_API_KEY is exported and curl supports --variable (8.3+)."
        if code in (6, 7, 28):
            return "The hook could not reach TypeSafe within the request deadline."
    if "401" in message or "not logged in" in message or "unauthorized" in message:
        return "Check Codex login in the isolated trial."
    if "model" in message and any(word in message for word in ("unsupported", "not supported", "not found", "not available")):
        return "The requested model is unavailable. Set WORK_HOOKS_MODEL to a model available on this account."
    if "unexpected argument" in message or "unrecognized option" in message:
        return "The installed CLI rejected an option. Check the installed CLI version."
    return "The subprocess returned an unrecognized error. Retry the isolated trial with open-chat --check."
