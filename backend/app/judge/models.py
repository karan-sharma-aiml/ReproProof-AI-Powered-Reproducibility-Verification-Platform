from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    PASS = "Pass"
    WEAK_PASS = "Weak Pass"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    REJECT = "Reject"


class ScoreExplanation(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    rationale: str
    confidence: float = Field(ge=0, le=1)
    limitations: list[str] = Field(default_factory=list)


class JudgeRequest(BaseModel):
    repository_id: str
    execution_success: bool | None = None
    execution_confidence: float | None = Field(default=None, ge=0, le=1)
    dataset_path: str | None = None
    research_paper_path: str | None = None


class JudgeReport(BaseModel):
    repository_id: str
    verdict: Verdict
    overall_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    scores: dict[str, ScoreExplanation]
    recommendations: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_summary: list[str] = Field(default_factory=list)

    @property
    def explainability(self) -> dict[str, Any]:
        return {name: score.model_dump() for name, score in self.scores.items()}
