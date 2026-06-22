import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_GREP_MATCHES = 200


class PathEscapesRepoError(ValueError):
    pass


def _resolve_within_repo(repo_root: Path, path: str) -> Path:
    candidate = (repo_root / path).resolve()
    repo_root_resolved = repo_root.resolve()
    if repo_root_resolved not in candidate.parents and candidate != repo_root_resolved:
        raise PathEscapesRepoError(f"path '{path}' escapes repo root '{repo_root}'")
    return candidate


def fetch_file(repo_root: Path, path: str, max_bytes: int = 50_000) -> str | None:
    try:
        resolved = _resolve_within_repo(repo_root, path)
    except PathEscapesRepoError:
        logger.warning("fetch_file rejected path escaping repo root: %s", path)
        return None

    if not resolved.is_file():
        return None

    if resolved.stat().st_size > max_bytes:
        return resolved.read_bytes()[:max_bytes].decode("utf-8", errors="replace")

    return resolved.read_text(encoding="utf-8", errors="replace")


def grep_pattern(repo_root: Path, regex: str, file_glob: str = "**/*") -> list[dict[str, object]]:
    pattern = re.compile(regex)
    matches: list[dict[str, object]] = []

    for file_path in sorted(repo_root.glob(file_glob)):
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                matches.append(
                    {
                        "file": file_path.relative_to(repo_root).as_posix(),
                        "line": line_number,
                        "match": line.strip(),
                    }
                )
                if len(matches) >= MAX_GREP_MATCHES:
                    return matches

    return matches
