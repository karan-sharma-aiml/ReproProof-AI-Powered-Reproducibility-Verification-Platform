from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MetricSnapshot(BaseModel):
    counters: dict[str, float] = Field(default_factory=dict)
    histograms: dict[str, list[float]] = Field(default_factory=dict)


class MetricName(StrEnum):
    REPOSITORY_ANALYSIS_COUNT = "repository_analysis_count"
    EXECUTION_COUNT = "execution_count"
    ACTIVE_AI_AGENTS = "active_ai_agents"
    FAILED_AI_JOBS = "failed_ai_jobs"
    ANALYSIS_DURATION_SECONDS = "analysis_duration_seconds"
    REPAIR_DURATION_SECONDS = "repair_duration_seconds"
    JUDGE_SCORE = "judge_score"
    RESEARCH_SCORE = "research_score"
    MEMORY_USAGE_BYTES = "memory_usage_bytes"
    CPU_USAGE_SECONDS = "cpu_usage_seconds"
    QUEUE_SIZE = "queue_size"
    WORKER_COUNT = "worker_count"
    ACTIVE_SESSIONS = "active_sessions"
    API_REQUEST_COUNT = "api_request_count"
    API_ERROR_COUNT = "api_error_count"


class ComponentStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ComponentHealth(BaseModel):
    name: str
    status: ComponentStatus
    latency_ms: float = 0
    reason: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class HealthSummary(BaseModel):
    status: ComponentStatus
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    components: list[ComponentHealth] = Field(default_factory=list)


class DashboardMetrics(BaseModel):
    http_requests: float = 0
    api_latency_seconds: float = 0
    agent_execution_seconds: float = 0
    judge_evaluation_seconds: float = 0
    repository_scan_seconds: float = 0
    ai_analysis_seconds: float = 0
    queue_processing_seconds: float = 0
    background_tasks: float = 0
    cache_hits: float = 0
    cache_misses: float = 0
    export_seconds: float = 0
    errors: float = 0
    success_rate: float = Field(default=0, ge=0, le=1)
    token_usage: float = 0
    memory_bytes: int = 0
    cpu_seconds: float = 0
    agent_success_rate: float = Field(default=0, ge=0, le=1)
    confidence_samples: list[float] = Field(default_factory=list)
    provider_latency_seconds: list[float] = Field(default_factory=list)
    retry_count: float = 0


class AlertSeverity(StrEnum):
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(BaseModel):
    rule: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionDashboard(BaseModel):
    recent_executions: list[dict[str, Any]] = Field(default_factory=list)
    system_load: dict[str, float] = Field(default_factory=dict)
    agent_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    ai_metrics: dict[str, Any] = Field(default_factory=dict)


class TraceRecord(BaseModel):
    trace_id: str
    span_id: str
    name: str
    duration_ms: float = 0
    status: str = "ok"
    started_at: datetime
    ended_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SystemMetrics(BaseModel):
    cpu_usage_seconds: float = 0
    memory_usage_bytes: int = 0
    queue_size: float = 0
    worker_count: float = 0
    active_sessions: float = 0


class PlatformStatus(BaseModel):
    status: ComponentStatus
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""


class RunningWorkflow(BaseModel):
    workflow_id: str
    name: str
    status: str = "running"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DashboardAggregation(BaseModel):
    platform_status: PlatformStatus
    system_metrics: SystemMetrics
    health_summary: HealthSummary
    running_workflows: list[RunningWorkflow] = Field(default_factory=list)
    top_ai_agents: list[dict[str, Any]] = Field(default_factory=list)
    repository_statistics: dict[str, Any] = Field(default_factory=dict)
    execution_statistics: dict[str, Any] = Field(default_factory=dict)
    error_summary: dict[str, Any] = Field(default_factory=dict)
    performance_summary: dict[str, Any] = Field(default_factory=dict)


class TelemetryProviderStatus(BaseModel):
    name: str
    enabled: bool = False
    reason: str = "provider_not_configured"
