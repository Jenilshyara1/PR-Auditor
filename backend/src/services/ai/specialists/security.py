from pathlib import Path

from src.schemas.findings import AgentName, Finding
from src.schemas.planner import SpecialistScope
from src.services.ai.specialists.base import FindingsList, build_specialist_prompt
from src.services.ai.structured_model import StructuredModel
from src.services.ai.tools.repo_access import fetch_file, grep_pattern

ROLE_DESCRIPTION = (
    "You are the security specialist in a PR review system. Check the diff for hardcoded "
    "secrets, injection risk, and unsafe deserialization. Grep matches and file contents for "
    "the relevant files are provided below as additional signal."
)

SECRET_LIKE_PATTERNS = (
    r"(api[_-]?key|secret|password|token)\s*=\s*['\"]",
)


async def security_specialist(
    pr_diff: str,
    scope: SpecialistScope,
    model: StructuredModel[FindingsList],
    repo_root: Path,
) -> list[Finding]:
    grep_hits = [
        match
        for pattern in SECRET_LIKE_PATTERNS
        for match in grep_pattern(repo_root, pattern)
    ]
    file_contents = {
        file_path: contents
        for file_path in scope.relevant_files
        if (contents := fetch_file(repo_root, file_path)) is not None
    }

    prompt = build_specialist_prompt(ROLE_DESCRIPTION, pr_diff, scope)
    if grep_hits:
        prompt += f"\n\nGrep matches for secret-like patterns:\n{grep_hits}"
    if file_contents:
        prompt += f"\n\nFull contents of relevant files:\n{file_contents}"

    result = await model.ainvoke(prompt)
    return [finding.model_copy(update={"agent": AgentName.SECURITY}) for finding in result.findings]
