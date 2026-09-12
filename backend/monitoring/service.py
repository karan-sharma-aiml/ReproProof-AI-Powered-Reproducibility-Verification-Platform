"""Portable monitoring configuration and dashboard generation."""

from __future__ import annotations

from typing import Any

from app.infrastructure.monitoring import monitoring_artifacts
from app.observability.dashboard.service import observability_dashboard
from app.observability.health.service import observability_health

from .prometheus.exporter import PrometheusExporter

_DASHBOARD_TITLES = (
    "Platform Overview",
    "Repository Analytics",
    "AI Provider Usage",
    "Research Analytics",
    "Agent Activity",
    "Judge Activity",
    "Execution Queue",
    "Memory Usage",
    "Security Dashboard",
    "Deployment Dashboard",
    "System Dashboard",
    "Infrastructure Dashboard",
)
_ALERTS = (
    ("CPUHigh", "reproproof_node_cpu_percent > 85", "warning"),
    ("MemoryHigh", "reproproof_node_memory_bytes > 2000000000", "warning"),
    (
        "RepositoryFailure",
        'rate(reproproof_repository_analysis_total{status="failed"}[5m]) > 0',
        "critical",
    ),
    (
        "AIProviderFailure",
        "rate(reproproof_provider_failures_total[5m]) > 0",
        "critical",
    ),
    (
        "ExecutionTimeout",
        "rate(reproproof_execution_timeouts_total[5m]) > 0",
        "critical",
    ),
    ("ResearchFailure", "rate(reproproof_research_failures_total[5m]) > 0", "critical"),
    ("JudgeFailure", "rate(reproproof_judge_failures_total[5m]) > 0", "critical"),
    ("OCRFailure", "rate(reproproof_ocr_failures_total[5m]) > 0", "critical"),
    (
        "DeploymentFailure",
        "rate(reproproof_deployment_failures_total[5m]) > 0",
        "critical",
    ),
    ("RedisDown", 'up{job="redis"} == 0', "critical"),
    ("PostgresDown", 'up{job="postgres"} == 0', "critical"),
    ("StorageFailure", "rate(reproproof_storage_failures_total[5m]) > 0", "critical"),
    ("DiskFull", "reproproof_node_filesystem_free_bytes < 1000000000", "warning"),
    ("QueueOverflow", "reproproof_queue_size > 100", "warning"),
    ("SecurityAttack", "rate(reproproof_security_events_total[5m]) > 10", "critical"),
    ("TooManyErrors", "rate(reproproof_http_errors_total[5m]) > 0.05", "critical"),
    (
        "HighLatency",
        "histogram_quantile(0.95, rate(reproproof_http_request_duration_seconds_bucket[5m])) > 2",
        "warning",
    ),
    ("APIDown", 'up{job="reproproof"} == 0', "critical"),
)


class MonitoringService:
    def __init__(self) -> None:
        self.exporter = PrometheusExporter()

    def prometheus(self) -> dict[str, Any]:
        return monitoring_artifacts.prometheus_config()

    def grafana(self) -> dict[str, Any]:
        return {
            "apiVersion": 1,
            "provider": {
                "name": "ReproProof",
                "type": "file",
                "folder": "ReproProof",
                "options": {"path": "/var/lib/grafana/dashboards"},
            },
            "dashboards": [self._dashboard(title) for title in _DASHBOARD_TITLES],
            "datasource": monitoring_artifacts.grafana_datasource(),
        }

    def loki(self) -> dict[str, Any]:
        return {
            "server": {"http_listen_port": 3100},
            "common": {
                "path_prefix": "/loki",
                "replication_factor": 1,
                "ring": {"kvstore": {"store": "inmemory"}},
            },
            "schema_config": {
                "configs": [
                    {
                        "from": "2024-01-01",
                        "store": "tsdb",
                        "object_store": "filesystem",
                        "schema": "v13",
                        "index": {"prefix": "index_", "period": "24h"},
                    }
                ]
            },
            "storage_config": {"filesystem": {"directory": "/loki/chunks"}},
        }

    def alerts(self) -> dict[str, Any]:
        return {
            "groups": [
                {
                    "name": "reproproof-enterprise",
                    "rules": [self._alert(*item) for item in _ALERTS],
                }
            ]
        }

    def alertmanager(self) -> dict[str, Any]:
        return {
            "global": {"resolve_timeout": "5m"},
            "route": {"receiver": "default"},
            "receivers": [{"name": "default"}],
        }

    def system(self) -> dict[str, Any]:
        return {
            "metrics": self.exporter.snapshot(),
            "dashboard": observability_dashboard.aggregate().model_dump(mode="json"),
        }

    def infrastructure(self) -> dict[str, Any]:
        return monitoring_artifacts.prometheus_config()

    def containers(self) -> dict[str, Any]:
        return {
            "collector": "cAdvisor",
            "metrics_path": "/metrics",
            "status": "deployment-managed",
        }

    async def providers(self) -> list[dict[str, Any]]:
        from app.integrations.composition import provider_manager

        return [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else vars(item)
            for item in await provider_manager.health()
        ]

    def dashboard(self) -> dict[str, Any]:
        return {
            "dashboards": [self._dashboard(title) for title in _DASHBOARD_TITLES],
            "health": observability_health.summary().model_dump(mode="json"),
        }

    def export(self) -> str:
        return self.exporter.render()

    @staticmethod
    def _dashboard(title: str) -> dict[str, Any]:
        slug = title.lower().replace(" ", "-")
        return {
            "uid": f"reproproof-{slug}",
            "title": title,
            "schemaVersion": 39,
            "tags": ["reproproof", "enterprise"],
            "panels": [
                {
                    "id": 1,
                    "title": title,
                    "type": "timeseries",
                    "targets": [{"expr": "reproproof_http_requests_total"}],
                }
            ],
        }

    @staticmethod
    def _alert(name: str, expr: str, severity: str) -> dict[str, Any]:
        return {
            "alert": f"ReproProof{name}",
            "expr": expr,
            "for": "5m",
            "labels": {"severity": severity, "service": "reproproof"},
            "annotations": {"summary": f"ReproProof {name} condition detected"},
        }


monitoring_service = MonitoringService()
