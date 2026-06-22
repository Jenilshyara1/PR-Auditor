from src.schemas.planner import PlannerOutput
from src.schemas.state import ReviewState
from src.services.ai.structured_model import StructuredModel

PLANNER_PROMPT_TEMPLATE = (
    "You are the planner in a multi-agent PR review system. Given a PR diff, decide which "
    "specialist agents are relevant (security, style, test_coverage, perf) and what scoped "
    "context each one needs. Skip agents that are clearly irrelevant to this diff (e.g. skip "
    "security for a CSS-only change).\n\n"
    "Repo language: {repo_language}\n"
    "Changed files: {changed_files}\n\n"
    "Diff:\n{pr_diff}"
)


def build_planner_prompt(state: ReviewState) -> str:
    return PLANNER_PROMPT_TEMPLATE.format(
        repo_language=state["repo_language"],
        changed_files=", ".join(state["changed_files"]),
        pr_diff=state["pr_diff"],
    )


async def planner_node(state: ReviewState, model: StructuredModel[PlannerOutput]) -> dict[str, object]:
    plan = await model.ainvoke(build_planner_prompt(state))
    return {"plan": plan}
