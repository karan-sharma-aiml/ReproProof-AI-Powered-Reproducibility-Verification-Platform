"""Models for deterministic repair strategies."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepairPlan(BaseModel):
    """A reviewable repair strategy that performs no changes itself."""

    model_config = ConfigDict(frozen=True)

    repair_type: Literal[
        "INSTALL_DEPENDENCY",
        "FIX_DATASET_PATH",
        "VERIFY_ENTRY_POINT",
        "CHECK_PERMISSIONS",
        "REVIEW_SOURCE_CODE",
        "INCREASE_TIMEOUT",
        "REDUCE_MEMORY_USAGE",
        "MANUAL_INVESTIGATION",
        "NO_ACTION_REQUIRED",
    ]
    description: str
    suggested_commands: list[str] = Field(default_factory=list)
    manual_actions: list[str] = Field(default_factory=list)
    repair_plan_confidence: int = Field(ge=0, le=100)
    safe_to_apply: bool
    requires_human_review: bool
