from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.devops.health import health_monitor
from app.devops.metrics import metrics

router = APIRouter(tags=["operations"])


@router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def prometheus_metrics() -> str:
    return metrics.prometheus()


@router.get("/health/live")
def liveness() -> dict[str, object]:
    return health_monitor.live()


@router.get("/health/ready")
def readiness() -> dict[str, object]:
    return health_monitor.ready()


@router.get("/analytics/requests")
def request_analytics() -> dict[str, object]:
    return metrics.snapshot()
