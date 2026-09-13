"""Final deterministic verification and verdict report."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.execution_result import ExecutionResult
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.models.verification_report import VerificationReport
from app.services.patch_generator.models import PatchResult
from app.services.platform.models import ExecutiveSummary, HealthScoreResult
from app.services.self_healing.models import ExecutionHistoryEntry
from app.services.troubleshooter.models import TroubleshootingReport


class FinalVerificationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    repository: RepositoryMetadata
    static_analysis: RepositoryAIAnalysis
    execution: ExecutionResult
    metrics: dict[str, float] = Field(default_factory=dict)
    verification: VerificationReport
    workflow_status: Literal["SUCCESS", "FAILED"] = "SUCCESS"
    verdict: Literal[
        "REPRODUCED",
        "PARTIALLY_REPRODUCED",
        "NOT_REPRODUCED",
        "EXECUTION_FAILED",
        "EXECUTION_SKIPPED",
        "INVALID_PROJECT",
    ]
    final_ai_confidence: int = Field(ge=0, le=100)
    confidence_factors: list[str] = Field(default_factory=list)
    overall_score: float = Field(ge=0, le=100)
    explanation: str
    repair_suggestions: list[str] = Field(default_factory=list)
    timestamp: str
    system_information: str
    markdown_report: str = ""
    troubleshooting: TroubleshootingReport | None = None
    generated_patch: PatchResult | None = None
    retry_count: int = Field(default=0, ge=0, le=3)
    applied_patch: PatchResult | None = None
    execution_history: list[ExecutionHistoryEntry] = Field(default_factory=list)
    backup_path: str = ""
    rollback_available: bool = False
    final_status: str = ""
    health_score: int = Field(default=0, ge=0, le=100)
    health_score_details: HealthScoreResult | None = None
    executive_summary: ExecutiveSummary | None = None
