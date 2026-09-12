"""Typed platform-level analytics, health, summary, and progress models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProgressEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    stage: str
    status: Literal["QUEUED", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"]
    progress: int = Field(ge=0, le=100)
    message: str
    timestamp: str
    eta_seconds: float | None = Field(default=None, ge=0)


class HealthScoreResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    repository_id: str
    score: int = Field(ge=0, le=100)
    recommendations: list[str] = Field(default_factory=list)
    dimensions: dict[str, int] = Field(default_factory=dict)


class ExecutiveSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    summary: str
    status: str
    final_ai_confidence: int = Field(ge=0, le=100)
    health_score: int = Field(ge=0, le=100)


class AnalyticsResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_runs: int = Field(ge=0)
    successful_runs: int = Field(ge=0)
    failed_runs: int = Field(ge=0)
    average_runtime: float = Field(ge=0)
    average_ai_confidence: float = Field(ge=0, le=100)
    patch_success_rate: float = Field(ge=0, le=100)
    retry_success_rate: float = Field(ge=0, le=100)
    most_common_errors: dict[str, int] = Field(default_factory=dict)
    most_common_root_causes: dict[str, int] = Field(default_factory=dict)
    top_missing_dependencies: dict[str, int] = Field(default_factory=dict)
    language_distribution: dict[str, int] = Field(default_factory=dict)
    framework_distribution: dict[str, int] = Field(default_factory=dict)
    repository_statistics: dict[str, float] = Field(default_factory=dict)
