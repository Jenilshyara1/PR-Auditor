import asyncio

import pytest
from pydantic import ValidationError

from src.schemas.findings import AgentName, Finding, Severity
from src.schemas.planner import PlannerOutput, SpecialistScope
from src.services.ai.routing import ALL_SPECIALISTS
from src.services.ai.specialists.base import FindingsList


class _FakeBoundModel:
    def __init__(self, response: object) -> None:
        self._response = response

    async def ainvoke(self, prompt: str) -> object:
        return self._response


class _FakeChatModel:
    def __init__(self, planner_output: PlannerOutput, findings_output: FindingsList) -> None:
        self._planner_output = planner_output
        self._findings_output = findings_output

    def with_structured_output(self, schema: type) -> _FakeBoundModel:
        if schema is PlannerOutput:
            return _FakeBoundModel(self._planner_output)
        return _FakeBoundModel(self._findings_output)


def _activate_all_plan() -> PlannerOutput:
    agents = [AgentName.SECURITY, AgentName.STYLE, AgentName.TEST_COVERAGE, AgentName.PERF]
    return PlannerOutput(
        activate=agents,
        scopes=[SpecialistScope(agent=agent, instructions="review everything") for agent in agents],
        reasoning="exercise all specialists",
    )


def _one_finding_list() -> FindingsList:
    return FindingsList(
        findings=[
            Finding(
                agent=AgentName.SECURITY,
                file="src/app.py",
                line=1,
                severity=Severity.WARNING,
                confidence=0.6,
                message="placeholder finding",
            )
        ]
    )


def _base_state(repo_root: object) -> dict[str, object]:
    return {
        "pr_diff": "diff --git a/src/app.py\n+API_KEY = 'x'",
        "changed_files": ["src/app.py"],
        "repo_language": "python",
        "repo_root": str(repo_root),
        "plan": None,
        "findings": [],
        "final_report": None,
        "specialists_run": [],
        "specialists_failed": [],
    }


@pytest.mark.asyncio
async def test_parallel_specialist_writes_are_concatenated_not_overwritten(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    fake_chat_model = _FakeChatModel(planner_output=_activate_all_plan(), findings_output=_one_finding_list())
    monkeypatch.setattr("src.services.ai.graph.get_chat_model", lambda tier: fake_chat_model)
    from src.services.ai.graph import build_graph

    graph = build_graph()
    result = await graph.ainvoke(_base_state(tmp_path))

    assert sorted(result["specialists_run"]) == sorted(ALL_SPECIALISTS)
    assert result["specialists_failed"] == []
    assert result["final_report"] is not None


@pytest.mark.asyncio
async def test_specialist_timeout_does_not_block_critic_or_other_specialists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    fake_chat_model = _FakeChatModel(planner_output=_activate_all_plan(), findings_output=_one_finding_list())
    monkeypatch.setattr("src.services.ai.graph.get_chat_model", lambda tier: fake_chat_model)

    from src.services.ai import graph as graph_module

    monkeypatch.setitem(graph_module.NODE_TIMEOUT_SECONDS, "style", 0.05)

    async def _slow_style(state: object) -> list[Finding]:
        await asyncio.sleep(1)
        return []

    monkeypatch.setattr(graph_module, "_style", _slow_style)

    graph = graph_module.build_graph()
    result = await graph.ainvoke(_base_state(tmp_path))

    assert "style" in result["specialists_failed"]
    assert "style" not in result["specialists_run"]
    assert {"security", "test_coverage", "perf"} <= set(result["specialists_run"])
    assert result["final_report"] is not None


@pytest.mark.asyncio
async def test_specialist_invalid_output_is_retried_then_dropped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    fake_chat_model = _FakeChatModel(planner_output=_activate_all_plan(), findings_output=_one_finding_list())
    monkeypatch.setattr("src.services.ai.graph.get_chat_model", lambda tier: fake_chat_model)

    from src.services.ai import graph as graph_module

    call_count = 0

    async def _always_invalid_security(state: object) -> list[Finding]:
        nonlocal call_count
        call_count += 1
        raise ValidationError.from_exception_data("FindingsList", [])

    monkeypatch.setattr(graph_module, "_security", _always_invalid_security)

    graph = graph_module.build_graph()
    result = await graph.ainvoke(_base_state(tmp_path))

    assert call_count == 2  # one initial attempt + one retry, per SPECIALIST_RETRY_COUNT
    assert "security" in result["specialists_failed"]
    assert "security" not in result["specialists_run"]
    assert {"style", "test_coverage", "perf"} <= set(result["specialists_run"])
    assert result["final_report"] is not None
