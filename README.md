# Codex Work Hooks

Install a prompt scope check and parallel review into an ordinary Codex CLI session. Requires Python 3.10+ and a signed-in Codex CLI with plugin hook support.

## Install

From this checkout, register its marketplace and install the plugin:

```sh
codex plugin marketplace add "$PWD"
codex plugin add work-hooks@work-hooks
```

Start Codex normally and review both hook definitions in `/hooks`. Paste acceptance criteria in chat. A fresh Codex classifier is the default. To use TypeSafe Jev instead, set `WORK_HOOKS_CLASSIFIER=jev` and supply `JEV_API_KEY` in the environment before starting Codex. Jev requires curl 8.3+ and sends the request, pending request and criteria to TypeSafe.

## How it works

The [submission policy](plugins/work-hooks/src/work_hooks/core/submission.py) evaluates the [classifier contract](plugins/work-hooks/src/work_hooks/ports/classifiers.py). The [composition root](plugins/work-hooks/src/work_hooks/bootstrap.py) selects the provider. Codex events, subprocesses and persistence live under [adapters](plugins/work-hooks/src/work_hooks/adapters).

An accepted work request schedules three read-only reviews at the next stop. Reviewers run against the current workspace and share its files. The combined report and per-chat state live under Codex’s plugin data directory. Explanation-only and criteria-only turns skip review.
