"""Additive enterprise monitoring APIs."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from monitoring.service import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/prometheus")
def prometheus() -> dict[str, object]:
    return monitoring_service.prometheus()


@router.get("/grafana")
def grafana() -> dict[str, object]:
    return monitoring_service.grafana()


@router.get("/loki")
def loki() -> dict[str, object]:
    return monitoring_service.loki()


@router.get("/alerts")
def alerts() -> dict[str, object]:
    return monitoring_service.alerts()


@router.get("/system")
def system() -> dict[str, object]:
    return monitoring_service.system()


@router.get("/infrastructure")
def infrastructure() -> dict[str, object]:
    return monitoring_service.infrastructure()


@router.get("/containers")
def containers() -> dict[str, object]:
    return monitoring_service.containers()


@router.get("/providers")
async def providers() -> list[dict[str, object]]:
    return await monitoring_service.providers()


@router.get("/dashboard")
def dashboard() -> dict[str, object]:
    return monitoring_service.dashboard()


@router.get("/export", response_class=PlainTextResponse)
def export_metrics() -> str:
    return monitoring_service.export()
