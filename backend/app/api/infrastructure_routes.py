from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.monitoring import monitoring_artifacts
from app.infrastructure.service import infrastructure_service

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


@router.get("/status")
async def status() -> dict[str, object]:
    return (await infrastructure_service.overview_async()).model_dump(mode="json")


@router.get("/database")
def database() -> dict[str, object]:
    return infrastructure_service.database_health().model_dump(mode="json")


@router.get("/cache")
async def cache() -> dict[str, object]:
    return (await infrastructure_service.cache_health()).model_dump(mode="json")


@router.get("/storage")
def storage() -> dict[str, object]:
    return infrastructure_service.storage.health().model_dump(mode="json")


@router.get("/monitoring")
def monitoring() -> dict[str, object]:
    return {
        "status": "healthy",
        "prometheus": monitoring_artifacts.prometheus_config(),
        "grafana_datasource": monitoring_artifacts.grafana_datasource(),
        "grafana_dashboard": monitoring_artifacts.grafana_dashboard(),
        "alert_rules": monitoring_artifacts.alert_rules(),
    }
