from __future__ import annotations

from typing import Any


class MonitoringArtifacts:
    """Generates portable Prometheus/Grafana artifacts without requiring either service."""

    def prometheus_config(self) -> dict[str, Any]:
        return {
            "global": {"scrape_interval": "15s"},
            "scrape_configs": [
                {
                    "job_name": "reproproof",
                    "metrics_path": "/metrics",
                    "static_configs": [{"targets": ["backend:8000"]}],
                }
            ],
        }

    def grafana_datasource(self) -> dict[str, Any]:
        return {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": "http://prometheus:9090",
                    "isDefault": True,
                }
            ],
        }

    def grafana_dashboard(self) -> dict[str, Any]:
        return {
            "title": "ReproProof Infrastructure",
            "schemaVersion": 39,
            "panels": [
                {
                    "title": "HTTP requests",
                    "type": "timeseries",
                    "targets": [{"expr": "reproproof_http_requests_total"}],
                },
                {
                    "title": "HTTP errors",
                    "type": "timeseries",
                    "targets": [{"expr": "reproproof_http_errors_total"}],
                },
            ],
        }

    def alert_rules(self) -> dict[str, Any]:
        return {
            "groups": [
                {
                    "name": "reproproof",
                    "rules": [
                        {
                            "alert": "ReproProofHighErrorRate",
                            "expr": "rate(reproproof_http_errors_total[5m]) > 0.05",
                            "for": "5m",
                            "labels": {"severity": "warning"},
                        }
                    ],
                }
            ]
        }


monitoring_artifacts = MonitoringArtifacts()
