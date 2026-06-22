from pathlib import Path

from src.schemas.findings import AgentName, Finding
from src.schemas.planner import SpecialistScope
from src.services.ai.specialists.base import FindingsList, build_specialist_prompt
from src.services.ai.structured_model import StructuredModel
from src.services.ai.tools.coverage import list_test_files, run_coverage

ROLE_DESCRIPTION = (
    "You are the test coverage specialist in a PR review system. Flag changed functions that "
    "have no corresponding test file changes. Test-file presence and coverage signal for the "
    "relevant files are provided below."
)


async def coverage_specialist(
    pr_diff: str,
    scope: SpecialistScope,
    model: StructuredModel[FindingsList],
    repo_root: Path,
) -> list[Finding]:
    coverage_signal = {
        file_path: {
            "test_files": list_test_files(repo_root, file_path),
            "coverage": run_coverage(repo_root, file_path),
        }
        for file_path in scope.relevant_files
    }

    prompt = build_specialist_prompt(ROLE_DESCRIPTION, pr_diff, scope)
    if coverage_signal:
        prompt += f"\n\nTest coverage signal:\n{coverage_signal}"

    result = await model.ainvoke(prompt)
    return [
        finding.model_copy(update={"agent": AgentName.TEST_COVERAGE}) for finding in result.findings
    ]
