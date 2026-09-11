"""Structured static-analysis results for extracted repositories."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepositoryIssue(BaseModel):
    """One deterministic reproducibility issue."""

    model_config = ConfigDict(frozen=True)

    issue_type: str
    title: str
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    confidence: int = Field(ge=0, le=100)
    reason: str
    recommended_fix: str
    evidence: list[str] = Field(default_factory=list)
    affected_file: str = ""


class RepositoryAIAnalysis(BaseModel):
    """Complete static analysis report for an extracted repository."""

    model_config = ConfigDict(frozen=True)

    repository_id: str
    repository_name: str
    issues: list[RepositoryIssue] = Field(default_factory=list)
    execution_probability: int = Field(ge=0, le=100)
    reproducibility_score: int = Field(ge=0, le=100)
    risk_score: int = Field(ge=0, le=100)
    summary: str
