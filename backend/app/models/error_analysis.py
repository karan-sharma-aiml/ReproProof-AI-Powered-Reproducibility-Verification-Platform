"""Models for deterministic execution-failure classification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorAnalysis(BaseModel):
    """Structured classification of one execution result."""

    model_config = ConfigDict(frozen=True)

    category: str
    root_cause: str
    severity: Literal["none", "low", "medium", "high", "critical"]
    repairable: bool
    classification_confidence: int = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    suggested_repair_type: str
