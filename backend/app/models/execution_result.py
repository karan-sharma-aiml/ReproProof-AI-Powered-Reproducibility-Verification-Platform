"""Models returned by sandboxed plan execution."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExecutionResult(BaseModel):
    """Structured result of a bounded command execution sequence."""

    model_config = ConfigDict(frozen=True)

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float = Field(ge=0)
    timed_out: bool
    status: str = "COMPLETED"
    logs: list[str] = Field(default_factory=list)
    executed_command: str = ""
    installed_dependencies: list[str] = Field(default_factory=list)
    sandbox_path: str = ""
    log_path: str = ""
