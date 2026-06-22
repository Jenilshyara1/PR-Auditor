from pathlib import Path

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.schemas.findings import AgentName, Finding
from src.schemas.planner import PlannerOutput, SpecialistScope
from src.schemas.state import ReviewState
from src.services.ai.config import (
    NODE_TIER,
    NODE_TIMEOUT_SECONDS,
    SPECIALIST_RETRY_COUNT,
    get_langfuse_callbacks,
)
from src.services.ai.critic import critic_node as run_critic
from src.services.ai.llm_clients import get_chat_model
from src.services.ai.node_wrapper import specialist_node
from src.services.ai.planner import planner_node as run_planner
from src.services.ai.routing import ALL_SPECIALISTS, route_to_specialists
from src.services.ai.specialists.base import FindingsList
from src.services.ai.specialists.perf import perf_specialist
from src.services.ai.specialists.security import security_specialist
from src.services.ai.specialists.style import style_specialist
from src.services.ai.specialists.test_coverage import coverage_specialist

DEFAULT_SCOPE_INSTRUCTIONS = "No specific scope provided by the planner; review the full diff."


def _scope_for(plan: PlannerOutput | None, agent: AgentName) -> SpecialistScope:
    scope = plan.scope_for(agent) if plan is not None else None
    if scope is not None:
        return scope
    return SpecialistScope(agent=agent, instructions=DEFAULT_SCOPE_INSTRUCTIONS)


async def _planner(state: ReviewState) -> dict[str, object]:
    model = get_chat_model(NODE_TIER["planner"]).with_structured_output(PlannerOutput)
    return await run_planner(state, model)


async def _style(state: ReviewState) -> list[Finding]:
    model = get_chat_model(NODE_TIER["style"]).with_structured_output(FindingsList)
    scope = _scope_for(state.get("plan"), AgentName.STYLE)
    return await style_specialist(state["pr_diff"], scope, model, Path(state["repo_root"]))


async def _perf(state: ReviewState) -> list[Finding]:
    model = get_chat_model(NODE_TIER["perf"]).with_structured_output(FindingsList)
    scope = _scope_for(state.get("plan"), AgentName.PERF)
    return await perf_specialist(state["pr_diff"], scope, model)


async def _security(state: ReviewState) -> list[Finding]:
    model = get_chat_model(NODE_TIER["security"]).with_structured_output(FindingsList)
    scope = _scope_for(state.get("plan"), AgentName.SECURITY)
    return await security_specialist(state["pr_diff"], scope, model, Path(state["repo_root"]))


async def _test_coverage(state: ReviewState) -> list[Finding]:
    model = get_chat_model(NODE_TIER["test_coverage"]).with_structured_output(FindingsList)
    scope = _scope_for(state.get("plan"), AgentName.TEST_COVERAGE)
    return await coverage_specialist(state["pr_diff"], scope, model, Path(state["repo_root"]))


async def _critic(state: ReviewState) -> dict[str, object]:
    model = get_chat_model(NODE_TIER["critic"]).with_structured_output(FindingsList)
    return await run_critic(state, model)


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(ReviewState)

    graph.add_node("planner", _planner)
    graph.add_node(
        "security",
        specialist_node("security", NODE_TIMEOUT_SECONDS["security"], SPECIALIST_RETRY_COUNT)(_security),
    )
    graph.add_node(
        "style",
        specialist_node("style", NODE_TIMEOUT_SECONDS["style"], SPECIALIST_RETRY_COUNT)(_style),
    )
    graph.add_node(
        "test_coverage",
        specialist_node(
            "test_coverage", NODE_TIMEOUT_SECONDS["test_coverage"], SPECIALIST_RETRY_COUNT
        )(_test_coverage),
    )
    graph.add_node(
        "perf",
        specialist_node("perf", NODE_TIMEOUT_SECONDS["perf"], SPECIALIST_RETRY_COUNT)(_perf),
    )
    graph.add_node("critic", _critic)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", route_to_specialists, ALL_SPECIALISTS)

    for node_name in ALL_SPECIALISTS:
        graph.add_edge(node_name, "critic")

    graph.add_edge("critic", END)

    return graph.compile()


compiled_graph = build_graph()


async def run_review(graph: CompiledStateGraph, state: ReviewState) -> dict[str, object]:
    callbacks = get_langfuse_callbacks()
    config = {"callbacks": callbacks} if callbacks else None
    return await graph.ainvoke(state, config=config)
