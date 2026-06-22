from src.schemas.findings import Finding
from src.schemas.state import ReviewState
from src.services.ai.specialists.base import FindingsList
from src.services.ai.structured_model import StructuredModel

CRITIC_PROMPT_TEMPLATE = (
    "You are the critic in a multi-agent PR review system. Below is the full list of findings "
    "raised by specialist agents for one PR. Dedupe overlapping findings (the same file/line "
    "flagged by more than one agent), down-weight or drop low-confidence findings, and resolve "
    "direct contradictions between agents.\n\n"
    "For every finding you decide not to surface, set dismissed=true and fill in "
    "dismissed_reason with your reasoning — never delete a finding, only mark it dismissed. "
    "Return the full list, including dismissed ones.\n\n"
    "Specialists that did not complete (timed out or produced invalid output): {failed}\n\n"
    "Findings:\n{findings}"
)


def build_critic_prompt(state: ReviewState) -> str:
    failed = ", ".join(state["specialists_failed"]) or "none"
    findings_repr = "\n".join(f.model_dump_json() for f in state["findings"])
    return CRITIC_PROMPT_TEMPLATE.format(failed=failed, findings=findings_repr)


async def critic_node(state: ReviewState, model: StructuredModel[FindingsList]) -> dict[str, list[Finding]]:
    if not state["findings"]:
        return {"final_report": []}

    result = await model.ainvoke(build_critic_prompt(state))
    return {"final_report": result.findings}
