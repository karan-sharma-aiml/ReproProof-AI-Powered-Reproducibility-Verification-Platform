"""Final deterministic verification and verdict report."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.execution_result import ExecutionResult
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.models.verification_report import VerificationReport


class FinalVerificationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    repository: RepositoryMetadata
    static_analysis: RepositoryAIAnalysis
    execution: ExecutionResult
    metrics: dict[str, float] = Field(default_factory=dict)
    verification: VerificationReport
    verdict: Literal[
        "REPRODUCED",
        "PARTIALLY_REPRODUCED",
        "NOT_REPRODUCED",
        "EXECUTION_FAILED",
        "INVALID_PROJECT",
    ]
    confidence: int = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    explanation: str
    repair_suggestions: list[str] = Field(default_factory=list)
    timestamp: str
    system_information: str
    markdown_report: str = ""
