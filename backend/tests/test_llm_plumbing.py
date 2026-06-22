import pytest
from langchain_openai import ChatOpenAI

from src.schemas.findings import AgentName
from src.schemas.planner import PlannerOutput
from src.services.ai.config import MODEL_TIERS, NODE_TIER
from src.services.ai.llm_clients import get_chat_model
from src.services.ai.planner import build_planner_prompt, planner_node


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-used-no-network-call")


def test_get_chat_model_resolves_correct_model_per_tier() -> None:
    model = get_chat_model("small")
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == MODEL_TIERS["small"]


def test_node_tier_covers_every_node() -> None:
    expected_nodes = {"planner", "style", "test_coverage", "perf", "security", "critic"}
    assert set(NODE_TIER) == expected_nodes


class FakeStructuredModel:
    def __init__(self, output: object) -> None:
        self._output = output
        self.last_prompt: str | None = None

    async def ainvoke(self, prompt: str) -> object:
        self.last_prompt = prompt
        return self._output


@pytest.mark.asyncio
async def test_planner_node_returns_plan_from_model() -> None:
    expected_plan = PlannerOutput(
        activate=[AgentName.SECURITY],
        scopes=[],
        reasoning="diff touches auth code",
    )
    fake_model = FakeStructuredModel(expected_plan)
    state = {
        "pr_diff": "diff --git a/auth.py\n+API_KEY = 'x'",
        "changed_files": ["auth.py"],
        "repo_language": "python",
        "plan": None,
        "findings": [],
        "final_report": None,
        "specialists_run": [],
        "specialists_failed": [],
    }

    result = await planner_node(state, fake_model)

    assert result == {"plan": expected_plan}
    assert fake_model.last_prompt is not None
    assert "auth.py" in fake_model.last_prompt


def test_build_planner_prompt_includes_diff_and_files() -> None:
    state = {
        "pr_diff": "some diff",
        "changed_files": ["a.py", "b.py"],
        "repo_language": "python",
        "plan": None,
        "findings": [],
        "final_report": None,
        "specialists_run": [],
        "specialists_failed": [],
    }
    prompt = build_planner_prompt(state)
    assert "some diff" in prompt
    assert "a.py, b.py" in prompt
    assert "python" in prompt
