"""Models returned by verification comparisons."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VerificationReport(BaseModel):
    """Structured comparison of expected and observed research metrics."""

    model_config = ConfigDict(frozen=True)

    expected_value: float
    actual_value: float | None
    metric_name: str
    absolute_difference: float | None
    relative_difference: float | None
    tolerance: float = Field(ge=0)
    reproduced: bool
    confidence: int = Field(ge=0, le=100)
    verdict: Literal[
        "REPRODUCED", "PARTIALLY_REPRODUCED", "NOT_REPRODUCED", "UNAVAILABLE"
    ]
    explanation: str
    matched_metrics: dict[str, float] = Field(default_factory=dict)
    failed_metrics: dict[str, float] = Field(default_factory=dict)
    missing_metrics: list[str] = Field(default_factory=list)
    overall_similarity: float = Field(default=0, ge=0, le=100)
    overall_score: float = Field(default=0, ge=0, le=100)
