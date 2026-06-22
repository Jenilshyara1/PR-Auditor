import operator
from typing import Annotated, TypedDict

from src.schemas.findings import Finding
from src.schemas.planner import PlannerOutput


class ReviewState(TypedDict):
    pr_diff: str
    changed_files: list[str]
    repo_language: str
    repo_root: str  # checked-out working copy that tools (grep/fetch/lint/coverage) operate against
    plan: PlannerOutput | None
    findings: Annotated[list[Finding], operator.add]
    final_report: list[Finding] | None
    specialists_run: Annotated[list[str], operator.add]
    specialists_failed: Annotated[list[str], operator.add]
