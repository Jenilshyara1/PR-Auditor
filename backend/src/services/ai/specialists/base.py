from pydantic import BaseModel, Field

from src.schemas.findings import Finding
from src.schemas.planner import SpecialistScope


class FindingsList(BaseModel):
    findings: list[Finding] = Field(default_factory=list)


def build_specialist_prompt(role_description: str, pr_diff: str, scope: SpecialistScope) -> str:
    relevant_files = ", ".join(scope.relevant_files) or "all changed files"
    return (
        f"{role_description}\n\n"
        f"Planner instructions: {scope.instructions}\n"
        f"Relevant files: {relevant_files}\n\n"
        f"Diff:\n{pr_diff}"
    )
