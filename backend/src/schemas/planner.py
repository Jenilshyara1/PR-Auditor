from pydantic import BaseModel, Field, field_validator

from src.schemas.findings import AgentName


class SpecialistScope(BaseModel):
    agent: AgentName
    instructions: str
    relevant_files: list[str] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    activate: list[AgentName]
    scopes: list[SpecialistScope]
    reasoning: str

    @field_validator("activate")
    @classmethod
    def _non_empty_activate(cls, value: list[AgentName]) -> list[AgentName]:
        if not value:
            return [AgentName.STYLE]
        return value

    def scope_for(self, agent: AgentName) -> SpecialistScope | None:
        return next((scope for scope in self.scopes if scope.agent == agent), None)
