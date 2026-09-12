from __future__ import annotations

from typing import Any

from ..health.service import ObservabilityHealth, observability_health
from ..metrics.service import ObservabilityMetrics, observability_metrics
from ..models import (
    ComponentStatus,
    DashboardAggregation,
    PlatformStatus,
    SystemMetrics,
)


class ObservabilityDashboard:
    """Builds backend dashboard data without owning a UI or business workflow."""

    def __init__(
        self,
        metrics: ObservabilityMetrics | None = None,
        health: ObservabilityHealth | None = None,
    ) -> None:
        self.metrics = metrics or observability_metrics
        self.health = health or observability_health

    def aggregate(self) -> DashboardAggregation:
        health_summary = self.health.summary()
        dashboard_metrics = self.metrics.dashboard()
        snapshot = self.metrics.snapshot()
        components = health_summary.components
        unavailable = sum(
            component.status == ComponentStatus.UNAVAILABLE for component in components
        )
        degraded = sum(
            component.status == ComponentStatus.DEGRADED for component in components
        )
        platform_status = health_summary.status
        reason = "all_registered_checks_passed"
        if unavailable:
            platform_status = ComponentStatus.UNAVAILABLE
            reason = f"{unavailable}_health_checks_unavailable"
        elif degraded:
            platform_status = ComponentStatus.DEGRADED
            reason = f"{degraded}_health_checks_degraded"

        counters = snapshot.counters
        return DashboardAggregation(
            platform_status=PlatformStatus(status=platform_status, reason=reason),
            system_metrics=SystemMetrics(
                cpu_usage_seconds=dashboard_metrics.cpu_seconds,
                memory_usage_bytes=dashboard_metrics.memory_bytes,
                queue_size=self._sum_metric(counters, "queue_size"),
                worker_count=self._sum_metric(counters, "worker_count"),
                active_sessions=self._sum_metric(counters, "active_sessions"),
            ),
            health_summary=health_summary,
            top_ai_agents=self._agent_summary(counters),
            repository_statistics={
                "analysis_count": self._sum_metric(
                    counters, "repository_analysis_count"
                ),
            },
            execution_statistics={
                "execution_count": self._sum_metric(counters, "execution_count"),
                "failed_ai_jobs": self._sum_metric(counters, "failed_ai_jobs"),
            },
            error_summary={
                "api_errors": dashboard_metrics.errors,
                "alerts": 0,
            },
            performance_summary={
                "api_latency_seconds": dashboard_metrics.api_latency_seconds,
                "agent_execution_seconds": dashboard_metrics.agent_execution_seconds,
                "repair_time_seconds": self._histogram_sum(
                    snapshot.histograms, "repair_duration_seconds"
                ),
                "analysis_time_seconds": self._histogram_sum(
                    snapshot.histograms, "analysis_duration_seconds"
                ),
            },
        )

    @staticmethod
    def _sum_metric(values: dict[str, float], name: str) -> float:
        return sum(
            value
            for key, value in values.items()
            if key == name or key.startswith(name + "{")
        )

    @staticmethod
    def _histogram_sum(values: dict[str, list[float]], name: str) -> float:
        return sum(
            sum(items)
            for key, items in values.items()
            if key == name or key.startswith(name + "{")
        )

    @staticmethod
    def _agent_summary(counters: dict[str, float]) -> list[dict[str, Any]]:
        totals: dict[str, float] = {}
        for key, value in counters.items():
            if key.startswith("agent_executions_total{agent="):
                agent = key.split("agent=", 1)[1].rstrip("}")
                totals[agent] = value
        return [
            {"agent": name, "executions": count}
            for name, count in sorted(
                totals.items(), key=lambda item: item[1], reverse=True
            )
        ][:10]


observability_dashboard = ObservabilityDashboard()
