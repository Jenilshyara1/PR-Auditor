from pathlib import Path


def list_test_files(repo_root: Path, changed_file: str) -> list[str]:
    changed_path = Path(changed_file)
    stem = changed_path.stem
    candidates = {
        f"test_{stem}.py",
        f"{stem}_test.py",
    }

    matches: list[str] = []
    for test_file in repo_root.rglob("*.py"):
        if test_file.name in candidates:
            matches.append(test_file.relative_to(repo_root).as_posix())

    return matches


def run_coverage(repo_root: Path, path: str) -> dict[str, object]:
    # TODO: shell out to `pytest --cov` and parse real coverage data once the
    # fixture/test-runner story for arbitrary checked-out repos is built.
    return {"covered": False}
