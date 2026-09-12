"""Models for detected project characteristics."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProjectDetection(BaseModel):
    """JSON-serializable result of a project type detection pass."""

    model_config = ConfigDict(frozen=True)

    project_type: str
    framework: str
    detection_confidence: int = Field(ge=0, le=100)
    reason: str
