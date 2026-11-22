from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import subprocess

PROMPTS = Path(__file__).resolve().parents[1] / "prompts"
ROLES = ("experience", "standards", "correctness")


def parallel_review(workspace: Path, request: str) -> str:
    def review(role: str) -> str:
        instructions = (PROMPTS / f"{role}.md").read_text()
        result = subprocess.run(
            ["codex", "--no-daemon", "exec", "-m", os.getenv("WORK_HOOKS_MODEL", "gpt-6-luna"), "-c", 'model_reasoning_effort="low"', "--disable", "hooks", "--ephemeral",
             "--skip-git-repo-check", "-s", "read-only", "-C", str(workspace), "-"],
            input=f"Original work request:\n{request}\n\nReview instructions:\n{instructions}",
            timeout=240, text=True, capture_output=True,
            env={k: v for k, v in os.environ.items() if k != "JEV_API_KEY"})
        if result.returncode:
            raise RuntimeError(f"{role} reviewer exited {result.returncode}. Check Codex login and WORK_HOOKS_MODEL.")
        return f"## {role.capitalize()}\n\n{result.stdout.strip()}\n"

    with ThreadPoolExecutor(max_workers=len(ROLES)) as pool:
        return "# Parallel review\n\n" + "\n".join(pool.map(review, ROLES))
