import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

LINT_SUBPROCESS_TIMEOUT_SECONDS = 15


def run_linter(repo_root: Path, path: str) -> list[dict[str, object]]:
    try:
        result = subprocess.run(
            ["ruff", "check", "--output-format=json", path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=LINT_SUBPROCESS_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        logger.warning("ruff is not installed; skipping lint for %s", path)
        return []
    except subprocess.TimeoutExpired:
        logger.warning("ruff timed out after %ss on %s", LINT_SUBPROCESS_TIMEOUT_SECONDS, path)
        return []

    if not result.stdout.strip():
        return []

    try:
        raw_violations = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("ruff produced non-JSON output for %s", path)
        return []

    return [
        {
            "file": violation["filename"],
            "line": violation["location"]["row"],
            "code": violation["code"],
            "message": violation["message"],
        }
        for violation in raw_violations
    ]
