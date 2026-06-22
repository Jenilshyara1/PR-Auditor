from src.schemas.findings import AgentName, Finding
from src.schemas.planner import SpecialistScope
from src.services.ai.specialists.base import FindingsList, build_specialist_prompt
from src.services.ai.structured_model import StructuredModel

ROLE_DESCRIPTION = (
    "You are the performance specialist in a PR review system. Pattern-match the diff for "
    "N+1 queries, unbounded loops, and synchronous calls inside async code. You have no tools "
    "available — reason only from the diff text."
)


async def perf_specialist(
    pr_diff: str,
    scope: SpecialistScope,
    model: StructuredModel[FindingsList],
) -> list[Finding]:
    prompt = build_specialist_prompt(ROLE_DESCRIPTION, pr_diff, scope)
    result = await model.ainvoke(prompt)
    return [finding.model_copy(update={"agent": AgentName.PERF}) for finding in result.findings]
