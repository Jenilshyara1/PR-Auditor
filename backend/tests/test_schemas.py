import operator

import pytest
from pydantic import ValidationError

from src.schemas.findings import AgentName, Finding, Severity
from src.schemas.planner import PlannerOutput, SpecialistScope


def _finding(agent: AgentName = AgentName.SECURITY, line: int = 1) -> Finding:
    return Finding(
        agent=agent,
        file="src/app.py",
        line=line,
        severity=Severity.WARNING,
        confidence=0.8,
        message="example finding",
    )


def test_finding_defaults_not_dismissed() -> None:
    finding = _finding()
    assert finding.dismissed is False
    assert finding.dismissed_reason is None


def test_finding_confidence_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        Finding(
            agent=AgentName.STYLE,
            file="src/app.py",
            line=1,
            severity=Severity.INFO,
            confidence=1.5,
            message="bad confidence",
        )


def test_planner_output_rejects_unknown_agent() -> None:
    with pytest.raises(ValidationError):
        PlannerOutput(activate=["not_a_real_agent"], scopes=[], reasoning="x")


def test_planner_output_empty_activate_falls_back_to_style() -> None:
    plan = PlannerOutput(activate=[], scopes=[], reasoning="nothing relevant found")
    assert plan.activate == [AgentName.STYLE]


def test_planner_output_scope_for_finds_matching_agent() -> None:
    scope = SpecialistScope(agent=AgentName.PERF, instructions="check the new loop")
    plan = PlannerOutput(
        activate=[AgentName.PERF],
        scopes=[scope],
        reasoning="only a perf-relevant change",
    )
    found = plan.scope_for(AgentName.PERF)
    assert found is not None
    assert found.instructions == "check the new loop"


def test_planner_output_scope_for_returns_none_when_missing() -> None:
    plan = PlannerOutput(activate=[AgentName.STYLE], scopes=[], reasoning="x")
    assert plan.scope_for(AgentName.SECURITY) is None


def test_findings_reducer_concatenates_parallel_writes() -> None:
    existing = [_finding(AgentName.SECURITY, line=1)]
    incoming = [_finding(AgentName.STYLE, line=2)]
    combined = operator.add(existing, incoming)
    assert len(combined) == 2
    assert {f.agent for f in combined} == {AgentName.SECURITY, AgentName.STYLE}


def test_specialists_failed_reducer_concatenates() -> None:
    combined = operator.add(["security"], ["style"])
    assert combined == ["security", "style"]
