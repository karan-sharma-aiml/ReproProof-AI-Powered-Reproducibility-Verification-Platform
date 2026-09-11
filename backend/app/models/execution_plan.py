"""Models for deterministic repository execution plans."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExecutionPlan(BaseModel):
    """A text-only plan that downstream systems may review before execution."""

    model_config = ConfigDict(frozen=True)

    python_version: str
    environment_strategy: str
    dependency_file: str
    entry_point: str
    execution_type: str
    commands: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
