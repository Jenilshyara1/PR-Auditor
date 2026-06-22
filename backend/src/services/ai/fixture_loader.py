from pathlib import Path

from src.schemas.state import ReviewState


def load_fixture_state(fixture_dir: Path) -> ReviewState:
    diff_text = (fixture_dir / "diff.patch").read_text()
    repo_root = fixture_dir / "repo"
    changed_files = [p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*") if p.is_file()]

    return ReviewState(
        pr_diff=diff_text,
        changed_files=changed_files,
        repo_language="python",
        repo_root=str(repo_root),
        plan=None,
        findings=[],
        final_report=None,
        specialists_run=[],
        specialists_failed=[],
    )
