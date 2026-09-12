"""Domain models for generated, unapplied code patches."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["Low", "Medium", "High", "Critical"]


class PatchGenerationInput(BaseModel):
    """Evidence and context used to generate one patch preview."""

    model_config = ConfigDict(frozen=True)

    execution_id: str
    repository_path: str
    repository_tree: list[str] = Field(default_factory=list)
    problematic_file: str = ""
    execution_logs: str = ""
    stacktrace: str = ""
    error_message: str = ""
    root_cause: str = ""
    human_explanation: str = ""
    suggested_fix: str = ""
    requirements: str = ""
    environment: dict[str, str] = Field(default_factory=dict)


class PatchResult(BaseModel):
    """A validated patch preview. This model contains no apply operation."""

    model_config = ConfigDict(frozen=True)

    patch_id: str
    file_name: str
    original_file: str
    modified_file: str
    git_unified_diff: str
    summary: str
    patch_confidence: float = Field(ge=0, le=1)
    risk_level: RiskLevel
    estimated_success: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    provider: str = "deterministic-local"
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0, ge=0)


class GeneratePatchRequest(BaseModel):
    """HTTP request for a patch preview for a completed execution."""

    execution_id: str = Field(min_length=1)
