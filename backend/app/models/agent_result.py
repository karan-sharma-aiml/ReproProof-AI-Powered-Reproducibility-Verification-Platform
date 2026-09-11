"""Models returned by the ReproProof coordination agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.execution_plan import ExecutionPlan
from app.models.observation_report import ObservationReport


class AgentResult(BaseModel):
    """Structured result of the non-executing observation workflow."""

    model_config = ConfigDict(frozen=True)

    goal: str = "Verify repository"
    observation: ObservationReport
    plan: ExecutionPlan
    status: Literal["READY", "BLOCKED"]
    next_action: Literal["EXECUTE", "STOP"]
    explanation: str
    blocking_reasons: list[str] = Field(default_factory=list)
