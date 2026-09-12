from __future__ import annotations

import os

try:
    import resource
except ImportError:  # pragma: no cover - platform-specific fallback
    resource = None
from collections.abc import Mapping
from typing import Any

from app.devops.metrics import MetricsRegistry, metrics as default_metrics

from ..models import DashboardMetrics, MetricName, MetricSnapshot


class ObservabilityMetrics:
    """Reusable domain metric facade; HTTP instrumentation remains in DevOpsMiddleware."""

    def __init__(self, registry: MetricsRegistry | None = None) -> None:
        self.registry = registry or default_metrics

    def increment(
        self, name: str, value: float = 1, labels: Mapping[str, str] | None = None
    ) -> None:
        self.registry.increment(name, value, dict(labels or {}))

    def observe(
        self, name: str, value: float, labels: Mapping[str, str] | None = None
    ) -> None:
        self.registry.observe(name, value, dict(labels or {}))

    def count(self, metric: MetricName, value: float = 1, **labels: str) -> None:
        self.increment(metric.value, value, labels)

    def gauge(self, metric: MetricName, value: float, **labels: str) -> None:
        self.observe(metric.value, value, labels)

    def score(self, metric: MetricName, value: float, **labels: str) -> None:
        self.observe(metric.value, value, labels)

    def record_platform_metrics(
        self,
        *,
        repository_analyses: int = 0,
        executions: int = 0,
        active_agents: int = 0,
        failed_jobs: int = 0,
        queue_size: int = 0,
        workers: int = 0,
        active_sessions: int = 0,
    ) -> None:
        values = {
            MetricName.REPOSITORY_ANALYSIS_COUNT: repository_analyses,
            MetricName.EXECUTION_COUNT: executions,
            MetricName.ACTIVE_AI_AGENTS: active_agents,
            MetricName.FAILED_AI_JOBS: failed_jobs,
            MetricName.QUEUE_SIZE: queue_size,
            MetricName.WORKER_COUNT: workers,
            MetricName.ACTIVE_SESSIONS: active_sessions,
        }
        for metric, value in values.items():
            self.gauge(metric, value)

    def record_agent(
        self,
        agent_name: str,
        duration_seconds: float,
        confidence: float | None,
        success: bool,
        retries: int = 0,
    ) -> None:
        labels = {"agent": agent_name}
        self.observe("agent_execution_seconds", duration_seconds, labels)
        self.increment("agent_executions_total", labels=labels)
        self.increment(
            "agent_failures_total" if not success else "agent_successes_total",
            labels=labels,
        )
        self.increment("agent_retries_total", retries, labels=labels)
        if confidence is not None:
            self.observe("confidence", confidence, labels)

    def record_ai(
        self,
        provider: str,
        latency_seconds: float,
        prompt_size: int,
        completion_size: int,
        tokens: int = 0,
        hallucination_warning: bool = False,
    ) -> None:
        labels = {"provider": provider}
        self.observe("provider_latency_seconds", latency_seconds, labels)
        self.observe("prompt_size_bytes", float(prompt_size), labels)
        self.observe("completion_size_bytes", float(completion_size), labels)
        self.increment("token_usage_total", tokens, labels=labels)
        if hallucination_warning:
            self.increment("hallucination_warnings_total", labels=labels)

    def snapshot(self) -> MetricSnapshot:
        raw = self.registry.snapshot()
        counters = {
            self._key(name, labels): value
            for (name, labels), value in raw["counters"].items()
        }
        histograms = {
            self._key(name, labels): values
            for (name, labels), values in raw["histograms"].items()
        }
        return MetricSnapshot(counters=counters, histograms=histograms)

    def dashboard(self) -> DashboardMetrics:
        raw = self.snapshot()
        counters = raw.counters
        histograms = raw.histograms
        request_count = self._sum(counters, "http_requests_total")
        successes = self._sum(counters, "agent_successes_total")
        executions = successes + self._sum(counters, "agent_failures_total")
        return DashboardMetrics(
            http_requests=request_count,
            api_latency_seconds=self._sum_histograms(
                histograms, "http_request_duration_seconds"
            ),
            agent_execution_seconds=self._sum_histograms(
                histograms, "agent_execution_seconds"
            ),
            judge_evaluation_seconds=self._sum_histograms(
                histograms, "judge_evaluation_seconds"
            ),
            repository_scan_seconds=self._sum_histograms(
                histograms, "repository_scan_seconds"
            ),
            ai_analysis_seconds=self._sum_histograms(histograms, "ai_analysis_seconds"),
            queue_processing_seconds=self._sum_histograms(
                histograms, "queue_processing_seconds"
            ),
            background_tasks=self._sum(counters, "background_tasks_total"),
            cache_hits=self._sum(counters, "cache_hits_total"),
            cache_misses=self._sum(counters, "cache_misses_total"),
            export_seconds=self._sum_histograms(histograms, "export_seconds"),
            errors=self._sum(counters, "http_errors_total"),
            success_rate=(successes / executions if executions else 0),
            token_usage=self._sum(counters, "token_usage_total"),
            memory_bytes=self._memory_bytes(),
            cpu_seconds=self._cpu_seconds(),
            agent_success_rate=(successes / executions if executions else 0),
            confidence_samples=self._flatten(histograms, "confidence"),
            provider_latency_seconds=self._flatten(
                histograms, "provider_latency_seconds"
            ),
            retry_count=self._sum(counters, "agent_retries_total"),
        )

    @staticmethod
    def _key(name: str, labels: tuple[tuple[str, str], ...]) -> str:
        return (
            name
            if not labels
            else name + "{" + ",".join(f"{key}={value}" for key, value in labels) + "}"
        )

    @staticmethod
    def _sum(values: dict[str, float], name: str) -> float:
        return sum(
            value
            for key, value in values.items()
            if key == name or key.startswith(name + "{")
        )

    @staticmethod
    def _sum_histograms(values: dict[str, list[float]], name: str) -> float:
        return sum(
            sum(items)
            for key, items in values.items()
            if key == name or key.startswith(name + "{")
        )

    @staticmethod
    def _flatten(values: dict[str, list[float]], name: str) -> list[float]:
        return [
            item
            for key, items in values.items()
            if key == name or key.startswith(name + "{")
            for item in items
        ]

    @staticmethod
    def _memory_bytes() -> int:
        if resource is None:
            try:
                import psutil

                return int(psutil.Process().memory_info().rss)
            except (ImportError, OSError):
                return 0
        try:
            return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
        except (AttributeError, OSError):
            return 0

    @staticmethod
    def _cpu_seconds() -> float:
        return os.times().user + os.times().system


observability_metrics = ObservabilityMetrics()
