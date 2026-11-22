# Sourced before the trial isolates HOME.
require_brew() {
  if ! command -v brew >/dev/null; then
    for prefix in /opt/homebrew /usr/local; do
      if [[ -x "$prefix/bin/brew" ]]; then export PATH="$prefix/bin:$PATH"; break; fi
    done
  fi
  command -v brew >/dev/null || {
    echo "A required tool is missing. Install Homebrew or provide Python 3.10+ and a plugin-capable Codex CLI on PATH." >&2
    return 1
  }
}

prepare_tools() {
  if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    require_brew
    brew install python
    export PATH="$(brew --prefix python)/bin:$PATH"
  fi
  if ! codex plugin add --help >/dev/null 2>&1; then
    # Keep a compatible CLI private to the trial, including when an older CLI exists.
    if ! command -v npm >/dev/null; then require_brew; brew install node; fi
    local prefix="$HOME/Library/Caches/codex-work-hooks/cli"
    if ! "$prefix/node_modules/.bin/codex" plugin add --help >/dev/null 2>&1; then
      npm install --prefix "$prefix" @openai/codex@0.171.0
    fi
    export PATH="$prefix/node_modules/.bin:$prefix/bin:$PATH"
  fi
  codex plugin add --help >/dev/null
}

prepare_jev() {
  if [[ -z ${JEV_API_KEY:-} ]]; then
    [[ -t 0 ]] || { echo "Export JEV_API_KEY before starting a noninteractive trial." >&2; return 1; }
    read -r -s -p 'TypeSafe Jev API key (hidden): ' JEV_API_KEY
    echo >&2
    [[ -n "$JEV_API_KEY" ]] || { echo "A TypeSafe API key is required for Jev." >&2; return 1; }
    export JEV_API_KEY
  fi
}
