from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CacheLayer(StrEnum):
    MEMORY = "memory"
    DISTRIBUTED = "distributed"
    HYBRID = "hybrid"


class CacheStatistics(BaseModel):
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    entries: int = 0
    bytes_used: int = 0
    hit_ratio: float = Field(default=0, ge=0, le=1)


class QueueStatus(BaseModel):
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    workers: int = 0
    delayed: int = 0


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRecord(BaseModel):
    task_id: str
    name: str
    priority: int = 100
    status: JobStatus = JobStatus.QUEUED
    progress: float = Field(default=0, ge=0, le=1)
    attempts: int = 0
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResourceSnapshot(BaseModel):
    cpu_seconds: float = 0
    memory_bytes: int = 0
    disk_bytes: int = 0
    network_bytes: int = 0
    active_agents: int = 0
    running_workflows: int = 0
    queue_size: int = 0
    cache_entries: int = 0
    rag_latency_seconds: float = 0
    provider_latency_seconds: float = 0


class LatencySummary(BaseModel):
    request_seconds: float = 0
    ai_provider_seconds: float = 0
    rag_seconds: float = 0
    repository_seconds: float = 0
    queue_seconds: float = 0
    throughput_per_second: float = 0
    bottlenecks: list[str] = Field(default_factory=list)


class BenchmarkResult(BaseModel):
    benchmark_id: str
    category: str
    operation: str
    iterations: int
    total_seconds: float
    average_seconds: float
    throughput_per_second: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PerformanceOverview(BaseModel):
    cache: CacheStatistics
    queue: QueueStatus
    resources: ResourceSnapshot
    latency: LatencySummary
    benchmarks: list[BenchmarkResult] = Field(default_factory=list)
