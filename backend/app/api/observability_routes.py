from __future__ import annotations

from fastapi import APIRouter

from app.observability.dashboard.service import observability_dashboard
from app.observability.health.service import observability_health
from app.observability.metrics.service import observability_metrics
from app.observability.models import (
    HealthSummary,
    MetricSnapshot,
    DashboardAggregation,
    TraceRecord,
)
from app.observability.telemetry.service import telemetry
from app.observability.tracing.service import tracer

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/metrics", response_model=MetricSnapshot)
def metrics() -> MetricSnapshot:
    return observability_metrics.snapshot()


@router.get("/health", response_model=HealthSummary)
def health() -> HealthSummary:
    return observability_health.summary()


@router.get("/platform", response_model=DashboardAggregation)
def platform() -> DashboardAggregation:
    return observability_dashboard.aggregate()


@router.get("/system", response_model=dict[str, object])
def system() -> dict[str, object]:
    return observability_dashboard.aggregate().system_metrics.model_dump()


@router.get("/traces", response_model=list[TraceRecord])
def traces() -> list[TraceRecord]:
    return tracer.recent()


@router.get("/telemetry", response_model=list[dict[str, object]])
def telemetry_status() -> list[dict[str, object]]:
    return [status.model_dump() for status in telemetry.providers_status()]
