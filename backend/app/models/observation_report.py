"""Unified observation report models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_detection import ProjectDetection
from app.models.repository import RepositoryMetadata


class ObservationReport(BaseModel):
    """Combined repository and project observations for downstream consumers."""

    model_config = ConfigDict(frozen=True)

    repository: RepositoryMetadata
    project: ProjectDetection
    health_score: int = Field(ge=0, le=100)
    execution_ready: bool
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
