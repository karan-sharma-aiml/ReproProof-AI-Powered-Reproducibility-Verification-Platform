from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CACHED = "cached"


class ResourceLimits(BaseModel):
    model_config = ConfigDict(frozen=True)

    cpu_count: float = Field(default=1.0, gt=0, le=64)
    memory_bytes: int = Field(default=512 * 1024 * 1024, gt=0)
    timeout_seconds: float = Field(default=300.0, gt=0, le=86_400)
    pids_limit: int = Field(default=128, gt=0)
    network_enabled: bool = False


class ExecutionJob(BaseModel):
    model_config = ConfigDict(frozen=True)

    repository_id: str
    repository_path: str
    command: list[str] = Field(min_length=1)
    limits: ResourceLimits = Field(default_factory=ResourceLimits)
    environment_hash: str = ""
    job_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionRecord(BaseModel):
    job_id: str
    repository_id: str
    status: JobStatus
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    runtime_seconds: float = 0.0
    memory_bytes: int | None = None
    cpu_seconds: float | None = None
    timeout_seconds: float | None = None
    cache_key: str | None = None
    logs: list[str] = Field(default_factory=list)
    error: str | None = None


class EnvironmentReport(BaseModel):
    repository_path: str
    languages: list[str] = Field(default_factory=list)
    virtual_environments: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    dependency_files: list[str] = Field(default_factory=list)
    runtime_files: list[str] = Field(default_factory=list)
    compatibility_notes: list[str] = Field(default_factory=list)


class BenchmarkResult(BaseModel):
    repository_id: str
    iterations: int = Field(ge=1)
    successful_iterations: int = 0
    runtimes_seconds: list[float] = Field(default_factory=list)
    mean_runtime_seconds: float = 0.0
    min_runtime_seconds: float = 0.0
    max_runtime_seconds: float = 0.0
    regression_detected: bool = False
    history_key: str


class ReproducibilityResult(BaseModel):
    repository_id: str
    reproducible: bool
    runs: int = Field(ge=1)
    output_digests: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    environment_hash: str


class DockerSandboxSpec(BaseModel):
    image: str
    command: list[str]
    args: list[str]
    limits: ResourceLimits
    network_mode: str = "none"
    non_root: bool = True
