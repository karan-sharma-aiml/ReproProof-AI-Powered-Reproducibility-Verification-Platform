"""Models for self-healing operations and execution history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.execution_result import ExecutionResult
from app.services.patch_generator.models import PatchResult


class ApplyFixRequest(BaseModel):
    execution_id: str = Field(min_length=1)
    patch_id: str = Field(min_length=1)


class RollbackRequest(BaseModel):
    execution_id: str = Field(min_length=1)


class RerunRequest(BaseModel):
    execution_id: str = Field(min_length=1)


class ApplyResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    patch_id: str
    status: Literal["APPLIED"]
    applied_files: list[str] = Field(default_factory=list)
    backup_location: str
    verified: bool


class RollbackResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    status: Literal["ROLLED_BACK"]
    restored_files: list[str] = Field(default_factory=list)
    backup_locations: list[str] = Field(default_factory=list)


class ExecutionHistoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    attempt_number: int = Field(ge=1)
    patch_id: str = ""
    applied_files: list[str] = Field(default_factory=list)
    execution_status: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    duration: float = Field(ge=0)
    reason: str = ""
    backup_path: str = ""
    execution: ExecutionResult | None = None


class RerunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    final_status: str
    retry_count: int = Field(ge=0, le=3)
    execution: ExecutionResult
    history: list[ExecutionHistoryEntry] = Field(default_factory=list)
    applied_patch: PatchResult | None = None
    backup_path: str = ""
    rollback_available: bool = False
