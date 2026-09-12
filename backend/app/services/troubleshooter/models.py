"""Domain models for troubleshooting execution failures."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["Critical", "High", "Medium", "Low", "Info"]


class ParsedExecution(BaseModel):
    """Normalized execution evidence supplied to the troubleshooting agent."""

    model_config = ConfigDict(frozen=True)

    execution_id: str
    stdout: str = ""
    stderr: str = ""
    traceback: str = ""
    exit_code: int
    execution_time: float = Field(ge=0)
    working_directory: str = ""
    python_version: str = ""
    repository_path: str = ""
    repository_tree: list[str] = Field(default_factory=list)
    requirements: str = ""
    execution_log: str = ""


class RootCauseFinding(BaseModel):
    """Deterministic finding used as evidence for the final diagnosis."""

    model_config = ConfigDict(frozen=True)

    category: str
    evidence: list[str] = Field(default_factory=list)
    finding_confidence: float = Field(ge=0, le=1)
    severity: Severity


class TroubleshootingReport(BaseModel):
    """Structured diagnosis returned by the troubleshooting engine."""

    model_config = ConfigDict(frozen=True)

    execution_id: str
    root_cause: str
    diagnostic_confidence: float = Field(ge=0, le=1)
    severity: Severity
    explanation: str
    possible_fixes: list[str] = Field(default_factory=list)
    requires_manual_action: bool
    detected_error: str = ""
    execution_log: str = ""
    findings: list[RootCauseFinding] = Field(default_factory=list)


class TroubleshootRequest(BaseModel):
    """Request body for troubleshooting a completed execution."""

    execution_id: str = Field(min_length=1)
