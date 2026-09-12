"""Prometheus text exporter using the existing DevOps metrics registry."""

from __future__ import annotations

import re
from typing import Any

from app.devops.metrics import MetricsRegistry, metrics as default_metrics

from .collectors import MetricCollector

_CANONICAL_ALIASES = {
    "repository_analysis_count": "repository_analysis_total",
    "execution_count": "execution_jobs_total",
    "provider_latency_seconds": "provider_calls_latency_seconds",
    "http_requests_total": "http_requests_total",
}
_REQUIRED_ZERO_METRICS = {
    "http_requests_total": "counter",
    "http_errors_total": "counter",
    "repository_analysis_total": "counter",
    "judge_requests_total": "counter",
    "active_agents": "gauge",
    "execution_jobs_total": "counter",
    "execution_duration_seconds": "histogram",
    "memory_queries_total": "counter",
    "vector_searches_total": "counter",
    "research_reports_total": "counter",
    "dashboard_views_total": "counter",
    "provider_calls_total": "counter",
    "provider_failures_total": "counter",
    "ocr_requests_total": "counter",
    "docker_builds_total": "counter",
    "deployment_count_total": "counter",
    "security_events_total": "counter",
    "authentication_failures_total": "counter",
    "rate_limit_hits_total": "counter",
}


class PrometheusExporter:
    """Expose application metrics, host gauges, and stable metric families."""

    def __init__(
        self,
        registry: MetricsRegistry | None = None,
        collector: MetricCollector | None = None,
    ) -> None:
        self.registry = registry or default_metrics
        self.collector = collector or MetricCollector()
        self._summaries: dict[str, list[float]] = {}

    def observe_summary(self, name: str, value: float) -> None:
        """Record a Summary family without creating a second application registry."""
        self._summaries.setdefault(name, []).append(value)

    def snapshot(self) -> dict[str, Any]:
        raw = self.registry.snapshot()
        return {
            "counters": {
                self._name(name): value
                for (name, _labels), value in raw["counters"].items()
            },
            "histograms": {
                self._name(name): values
                for (name, _labels), values in raw["histograms"].items()
            },
            "system": self.collector.collect(),
        }

    def render(self) -> str:
        lines: list[str] = [
            "# ReproProof metrics generated from the shared observability registry"
        ]
        seen: set[str] = set()
        raw = self.registry.snapshot()
        for (name, labels), value in raw["counters"].items():
            metric = self._name(name)
            self._type(lines, metric, "counter", seen)
            lines.append(f"{metric}{self._labels(labels)} {value}")
        for (name, labels), values in raw["histograms"].items():
            metric = self._name(name)
            self._type(lines, metric, "histogram", seen)
            label_text = self._labels(labels)
            lines.append(f"{metric}_count{label_text} {len(values)}")
            lines.append(f"{metric}_sum{label_text} {sum(values)}")
        for name, values in self._summaries.items():
            metric = self._safe_name(name)
            self._type(lines, metric, "summary", seen)
            ordered = sorted(values)
            for quantile in (0.5, 0.9, 0.99):
                index = min(len(ordered) - 1, int(quantile * len(ordered)))
                lines.append(f'{metric}{{quantile="{quantile}"}} {ordered[index]}')
            lines.append(f"{metric}_count {len(values)}")
            lines.append(f"{metric}_sum {sum(values)}")
        for name, value in self.collector.collect().items():
            metric = self._safe_name(name)
            self._type(lines, metric, "gauge", seen)
            lines.append(f"{metric} {value}")
        for name, metric_type in _REQUIRED_ZERO_METRICS.items():
            metric = f"reproproof_{name}"
            self._type(lines, metric, metric_type, seen)
            if not any(line.startswith(metric + " ") for line in lines):
                lines.append(f"{metric} 0")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _name(name: str) -> str:
        return "reproproof_" + _CANONICAL_ALIASES.get(name, name).lower().replace(
            " ", "_"
        )

    @staticmethod
    def _safe_name(name: str) -> str:
        return "reproproof_" + re.sub(r"[^a-zA-Z0-9_:]", "_", name.lower())

    @staticmethod
    def _type(lines: list[str], metric: str, metric_type: str, seen: set[str]) -> None:
        if metric not in seen:
            lines.append(f"# TYPE {metric} {metric_type}")
            seen.add(metric)

    @staticmethod
    def _labels(labels: tuple[tuple[str, str], ...]) -> str:
        if not labels:
            return ""
        escaped = [
            f'{key}="{value.replace(chr(34), chr(92) + chr(34))}"'
            for key, value in labels
        ]
        return "{" + ",".join(escaped) + "}"
