from pathlib import Path

from src.schemas.findings import AgentName, Finding
from src.schemas.planner import SpecialistScope
from src.services.ai.specialists.base import FindingsList, build_specialist_prompt
from src.services.ai.structured_model import StructuredModel
from src.services.ai.tools.lint import run_linter

ROLE_DESCRIPTION = (
    "You are the style specialist in a PR review system. Check the diff for naming issues, "
    "dead code, and anything a linter's rules might miss. Lint violations are provided below "
    "as additional signal, not a substitute for your own review."
)


async def style_specialist(
    pr_diff: str,
    scope: SpecialistScope,
    model: StructuredModel[FindingsList],
    repo_root: Path,
) -> list[Finding]:
    lint_violations = [
        violation
        for file_path in scope.relevant_files
        for violation in run_linter(repo_root, file_path)
    ]

    prompt = build_specialist_prompt(ROLE_DESCRIPTION, pr_diff, scope)
    if lint_violations:
        prompt += f"\n\nLinter violations:\n{lint_violations}"

    result = await model.ainvoke(prompt)
    return [_with_agent(finding) for finding in result.findings]


def _with_agent(finding: Finding) -> Finding:
    return finding.model_copy(update={"agent": AgentName.STYLE})
