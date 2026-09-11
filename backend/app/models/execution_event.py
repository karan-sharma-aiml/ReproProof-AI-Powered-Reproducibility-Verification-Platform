"""Events emitted while a sandbox execution progresses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExecutionEvent(BaseModel):
    """A timestamped, progress-based execution update."""

    model_config = ConfigDict(frozen=True)

    stage: str
    status: Literal["RUNNING", "SUCCESS", "FAILED"]
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    message: str
    progress: int = Field(ge=0, le=100)
    stream: Literal["stdout", "stderr", "system"] = "system"
