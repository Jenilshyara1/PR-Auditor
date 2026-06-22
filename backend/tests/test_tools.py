from pathlib import Path

import pytest

from src.services.ai.tools.coverage import list_test_files, run_coverage
from src.services.ai.tools.lint import run_linter
from src.services.ai.tools.repo_access import PathEscapesRepoError, _resolve_within_repo, fetch_file, grep_pattern


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "API_KEY = 'sk-hardcoded-secret'\n"
        "def handler():\n"
        "    return API_KEY\n"
    )
    (tmp_path / "src" / "utils.py").write_text("def helper():\n    pass\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_utils.py").write_text("def test_helper():\n    pass\n")
    return tmp_path


def test_fetch_file_returns_contents(repo_root: Path) -> None:
    contents = fetch_file(repo_root, "src/app.py")
    assert contents is not None
    assert "API_KEY" in contents


def test_fetch_file_missing_returns_none(repo_root: Path) -> None:
    assert fetch_file(repo_root, "src/missing.py") is None


def test_fetch_file_rejects_path_traversal(repo_root: Path) -> None:
    assert fetch_file(repo_root, "../outside.py") is None


def test_resolve_within_repo_raises_on_escape(repo_root: Path) -> None:
    with pytest.raises(PathEscapesRepoError):
        _resolve_within_repo(repo_root, "../../etc/passwd")


def test_grep_pattern_finds_hardcoded_secret(repo_root: Path) -> None:
    matches = grep_pattern(repo_root, r"API_KEY\s*=")
    assert len(matches) == 1
    assert matches[0]["file"] == "src/app.py"
    assert matches[0]["line"] == 1


def test_grep_pattern_no_match_returns_empty(repo_root: Path) -> None:
    assert grep_pattern(repo_root, r"NOT_PRESENT_PATTERN") == []


def test_list_test_files_finds_matching_test(repo_root: Path) -> None:
    matches = list_test_files(repo_root, "src/utils.py")
    assert matches == ["tests/test_utils.py"]


def test_list_test_files_no_match_returns_empty(repo_root: Path) -> None:
    assert list_test_files(repo_root, "src/app.py") == []


def test_run_coverage_is_a_stub(repo_root: Path) -> None:
    assert run_coverage(repo_root, "src/app.py") == {"covered": False}


def test_run_linter_skips_gracefully_if_ruff_missing(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    def fake_run(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("ruff not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert run_linter(repo_root, "src/app.py") == []


def test_run_linter_real_ruff_against_fixture(repo_root: Path) -> None:
    violations = run_linter(repo_root, "src/app.py")
    assert isinstance(violations, list)
