import pytest

from src.schemas.findings import Finding
from src.services.ai.fixture_loader import load_fixture_state
from src.services.ai.graph import build_graph
from tests.conftest import FIXTURES_DIR, requires_openai_key


@requires_openai_key
@pytest.mark.asyncio
async def test_full_diff_activates_specialists_and_produces_report() -> None:
    graph = build_graph()
    state = load_fixture_state(FIXTURES_DIR / "sample_pr")

    result = await graph.ainvoke(state)

    assert result["specialists_run"], "expected at least one specialist to run"
    assert result["final_report"] is not None
    for finding in result["final_report"]:
        assert isinstance(finding, Finding)
        if finding.dismissed:
            assert finding.dismissed_reason


@requires_openai_key
@pytest.mark.asyncio
async def test_css_only_diff_skips_most_specialists() -> None:
    graph = build_graph()
    state = load_fixture_state(FIXTURES_DIR / "css_only_pr")

    result = await graph.ainvoke(state)

    assert "security" not in result["specialists_run"]
    assert result["final_report"] is not None
