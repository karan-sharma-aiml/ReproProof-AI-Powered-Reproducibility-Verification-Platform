from __future__ import annotations

import time
from collections.abc import Callable

from app.devops.health import HealthMonitor, health_monitor

from ..models import ComponentHealth, ComponentStatus, HealthSummary


class ObservabilityHealth:
    """Typed health facade over the existing readiness registry."""

    COMPONENTS = (
        "application",
        "database",
        "redis",
        "providers",
        "ai_providers",
        "vector_database",
        "storage",
        "execution_engine",
        "execution",
        "docker",
        "memory_layer",
        "memory",
        "research_layer",
        "research",
        "judge_layer",
        "judge",
        "agents",
        "deployment",
        "monitoring",
    )

    def __init__(self, monitor: HealthMonitor | None = None) -> None:
        self.monitor = monitor or health_monitor

    def register(self, name: str, check: Callable[[], bool]) -> None:
        self.monitor.register(name, check)

    def register_provider(self, provider: "HealthProvider") -> None:
        self.register(provider.name, provider.check)

    def summary(self) -> HealthSummary:
        readiness = self.monitor.ready()
        registered = readiness["dependencies"]
        components = []
        for name in self.COMPONENTS:
            started = time.perf_counter()
            if name in registered:
                healthy = bool(registered[name])
                status = (
                    ComponentStatus.HEALTHY if healthy else ComponentStatus.UNAVAILABLE
                )
                details = {"registered": True}
                reason = "check_passed" if healthy else "check_failed"
            else:
                status = ComponentStatus.HEALTHY
                details = {"registered": False, "mode": "not_configured"}
                reason = "provider_not_configured"
            components.append(
                ComponentHealth(
                    name=name,
                    status=status,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    reason=reason,
                    details=details,
                )
            )
        overall = (
            ComponentStatus.HEALTHY if readiness["ready"] else ComponentStatus.DEGRADED
        )
        return HealthSummary(status=overall, components=components)

    def liveness(self) -> HealthSummary:
        return HealthSummary(status=ComponentStatus.HEALTHY, components=[])


observability_health = ObservabilityHealth()


class HealthProvider:
    """Provider contract for a single dependency health check."""

    def __init__(self, name: str, check: Callable[[], bool]) -> None:
        self.name = name
        self.check = check
