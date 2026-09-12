from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.observability.logging.service import get_observability_logger
from monitoring.prometheus.exporter import PrometheusExporter

ROOT = Path(__file__).parents[2]


def test_prometheus_exporter_reuses_shared_registry() -> None:
    exporter = PrometheusExporter()
    exporter.observe_summary("monitoring_latency_seconds", 0.2)
    output = exporter.render()
    assert "# TYPE reproproof_http_requests_total counter" in output
    assert "reproproof_repository_analysis_total" in output
    assert "reproproof_active_agents" in output
    assert "reproproof_node_filesystem_free_bytes" in output
    assert "# TYPE reproproof_monitoring_latency_seconds summary" in output


def test_monitoring_routes_are_additive() -> None:
    client = TestClient(app)
    for path in (
        "/monitoring/prometheus",
        "/monitoring/grafana",
        "/monitoring/loki",
        "/monitoring/alerts",
        "/monitoring/system",
        "/monitoring/infrastructure",
        "/monitoring/containers",
        "/monitoring/dashboard",
        "/monitoring/export",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
    assert client.get("/monitoring/alerts").json()["groups"][0]["rules"]


def test_generated_artifacts_cover_required_stack() -> None:
    dashboard = json.loads(
        (ROOT / "infrastructure/monitoring/grafana-dashboard.json").read_text()
    )
    prometheus = (ROOT / "infrastructure/monitoring/prometheus.yml").read_text()
    alerts = (ROOT / "infrastructure/monitoring/alerts.yml").read_text()
    assert len(dashboard["generated_dashboards"]) >= 12
    assert "node-exporter" in prometheus and "cadvisor" in prometheus
    for name in (
        "CPUHigh",
        "MemoryHigh",
        "RedisDown",
        "PostgresDown",
        "APIDown",
        "HighLatency",
    ):
        assert name in alerts


def test_structured_logger_has_enterprise_fields(caplog) -> None:
    caplog.set_level(logging.INFO, logger="test-monitoring")
    get_observability_logger("test-monitoring").info("monitoring_test")
    record = caplog.records[-1]
    payload = json.loads(record.message)
    assert {
        "timestamp",
        "request_id",
        "repository_id",
        "user",
        "service",
        "agent",
        "provider",
        "latency",
        "status",
        "severity",
        "trace_id",
    } <= payload.keys()
