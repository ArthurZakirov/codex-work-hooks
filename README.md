# Scope Check for Codex

**Build what the team actually asked for.** Scope Check compares a proposed implementation with the acceptance criteria you collected in chat, so you can catch scope creep before the agent writes code.

## Install

With Python 3.10+ and a signed-in, plugin-capable Codex CLI, run:

```sh
git clone https://github.com/ArthurZakirov/codex-work-hooks.git
cd codex-work-hooks
./install
```

Start a fresh Codex chat and trust the installed hooks when prompted.

## Optional Jev classifier

Set `WORK_HOOKS_CLASSIFIER=jev` in the environment that launches Codex to use Jev.

**macOS, including daemon-backed Codex.** In **Keychain Access**, choose the **login** keychain and create a new password item. Set **Keychain Item Name** to `codex-work-hooks.jev`, set **Account Name** to your macOS username and enter the Jev API key in **Password**. Scope Check looks up that item when its process has no exported key. The login keychain must be unlocked and macOS may ask you to allow access. You can then start stock `codex` normally.

**Shell-based setup.** Supply `JEV_API_KEY` through your usual credential manager or shell environment, then run `codex --no-daemon` from that shell. The embedded server inherits that environment. A shared server already running can have an older environment. If both sources exist, the exported key takes precedence.

**Verification.** Before enabling Scope Check, the installer runs a live synthetic submission from the installation shell. It then checks that the installed plugin files match the tested source. To check the actual launch environment, open a fresh Codex session and ask “Explain what an acceptance criterion is.” If the hook reports a missing credential, confirm the keychain item name and access permissions or use the shell launch above. An HTTP 401 means the provider received the request and rejected the credential. The Jev adapter uses Python HTTPS. [Credential lookup](src/scope-check/work_hooks/adapters/jev_key.py)

## How scope checking works

**Set up a work item in chat.** Paste the criteria with their source, or ask Codex to read a ticket, message or file through a tool it already has. Codex replies with the work item, source and criteria. Scope Check stores this receipt for the current chat. An attributed paste relies on the user's attribution. A lookup relies on the worker reading the source.

**Use the criteria.** Later professional implementation requests are compared with the saved criteria. A new source for the same item adds a clarification. Selecting another item replaces the active evidence. Discussion, team communications and personal requests can proceed independently. [Submission policy](src/scope-check/work_hooks/core/evaluate_submission.py)

## Tests

Install dependencies with `python3 -m pip install -r tests/requirements.txt`. Run `python3 -m pytest` for unit tests or `python3 -m pytest tests/integration` for live integration tests. Installed-plugin tests use `WORK_HOOKS_TEST_AUTH_HOME="$HOME/.codex" python3 -m pytest tests/system` and require a file-backed Codex login.

Run `tests/fixtures/dispatch_api/open-chat` to try the isolated Scope Check demo.
