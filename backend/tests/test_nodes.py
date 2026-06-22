from pathlib import Path

import pytest

from src.schemas.findings import AgentName, Finding, Severity
from src.schemas.planner import SpecialistScope
from src.services.ai.critic import build_critic_prompt, critic_node
from src.services.ai.specialists.base import FindingsList
from src.services.ai.specialists.perf import perf_specialist
from src.services.ai.specialists.security import security_specialist
from src.services.ai.specialists.style import style_specialist
from src.services.ai.specialists.test_coverage import coverage_specialist


class FakeStructuredModel:
    def __init__(self, output: object) -> None:
        self._output = output
        self.last_prompt: str | None = None

    async def ainvoke(self, prompt: str) -> object:
        self.last_prompt = prompt
        return self._output


def _finding(agent: AgentName, message: str) -> Finding:
    return Finding(
        agent=agent,
        file="src/app.py",
        line=1,
        severity=Severity.WARNING,
        confidence=0.7,
        message=message,
    )


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "API_KEY = 'sk-hardcoded'\ndef handler():\n    return API_KEY\n"
    )
    return tmp_path


@pytest.fixture
def scope() -> SpecialistScope:
    return SpecialistScope(
        agent=AgentName.SECURITY,
        instructions="check for hardcoded credentials",
        relevant_files=["src/app.py"],
    )


@pytest.mark.asyncio
async def test_style_specialist_tags_findings_with_agent(repo_root: Path, scope: SpecialistScope) -> None:
    model = FakeStructuredModel(FindingsList(findings=[_finding(AgentName.SECURITY, "wrong agent on purpose")]))
    findings = await style_specialist("diff text", scope, model, repo_root)
    assert all(f.agent == AgentName.STYLE for f in findings)


@pytest.mark.asyncio
async def test_style_specialist_includes_lint_violations_in_prompt(repo_root: Path, scope: SpecialistScope) -> None:
    model = FakeStructuredModel(FindingsList(findings=[]))
    await style_specialist("diff text", scope, model, repo_root)
    assert model.last_prompt is not None
    assert "diff text" in model.last_prompt


@pytest.mark.asyncio
async def test_perf_specialist_has_no_tool_dependency(scope: SpecialistScope) -> None:
    model = FakeStructuredModel(FindingsList(findings=[_finding(AgentName.STYLE, "N+1 in loop")]))
    findings = await perf_specialist("diff text", scope, model)
    assert all(f.agent == AgentName.PERF for f in findings)


@pytest.mark.asyncio
async def test_security_specialist_includes_grep_and_file_contents(
    repo_root: Path, scope: SpecialistScope
) -> None:
    model = FakeStructuredModel(FindingsList(findings=[]))
    await security_specialist("diff text", scope, model, repo_root)
    assert model.last_prompt is not None
    assert "API_KEY" in model.last_prompt


@pytest.mark.asyncio
async def test_test_coverage_specialist_includes_coverage_signal(
    repo_root: Path, scope: SpecialistScope
) -> None:
    model = FakeStructuredModel(FindingsList(findings=[]))
    await coverage_specialist("diff text", scope, model, repo_root)
    assert model.last_prompt is not None
    assert "covered" in model.last_prompt


@pytest.mark.asyncio
async def test_critic_node_returns_empty_report_with_no_findings() -> None:
    state = {
        "pr_diff": "x",
        "changed_files": [],
        "repo_language": "python",
        "repo_root": ".",
        "plan": None,
        "findings": [],
        "final_report": None,
        "specialists_run": [],
        "specialists_failed": [],
    }
    result = await critic_node(state, FakeStructuredModel(FindingsList(findings=[])))
    assert result == {"final_report": []}


@pytest.mark.asyncio
async def test_critic_node_passes_findings_and_failed_specialists_to_prompt() -> None:
    state = {
        "pr_diff": "x",
        "changed_files": [],
        "repo_language": "python",
        "repo_root": ".",
        "plan": None,
        "findings": [_finding(AgentName.SECURITY, "secret found")],
        "final_report": None,
        "specialists_run": ["security"],
        "specialists_failed": ["perf"],
    }
    reconciled = [_finding(AgentName.SECURITY, "secret found")]
    model = FakeStructuredModel(FindingsList(findings=reconciled))

    result = await critic_node(state, model)

    assert result == {"final_report": reconciled}
    assert model.last_prompt is not None
    assert "perf" in model.last_prompt
    assert "secret found" in model.last_prompt


def test_build_critic_prompt_lists_none_when_no_failures() -> None:
    state = {
        "pr_diff": "x",
        "changed_files": [],
        "repo_language": "python",
        "repo_root": ".",
        "plan": None,
        "findings": [],
        "final_report": None,
        "specialists_run": [],
        "specialists_failed": [],
    }
    assert "none" in build_critic_prompt(state)
