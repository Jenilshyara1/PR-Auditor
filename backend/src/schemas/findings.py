from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AgentName(str, Enum):
    SECURITY = "security"
    STYLE = "style"
    TEST_COVERAGE = "test_coverage"
    PERF = "perf"


class Finding(BaseModel):
    agent: AgentName
    file: str
    line: int
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
    dismissed: bool = False
    dismissed_reason: str | None = None
