from __future__ import annotations

from typing import Any

from ..metrics.service import ObservabilityMetrics, observability_metrics
from ..models import TelemetryProviderStatus
from .providers import TelemetryProvider


class TelemetryService:
    """Application-facing telemetry facade for reusable event measurements."""

    def __init__(self, metrics: ObservabilityMetrics | None = None) -> None:
        self.metrics = metrics or observability_metrics
        self._providers: list[TelemetryProvider] = []

    def register_provider(self, provider: TelemetryProvider) -> None:
        self._providers.append(provider)

    def providers_status(self) -> list[TelemetryProviderStatus]:
        known = {provider.name: provider.status() for provider in self._providers}
        return [
            known.get(name, TelemetryProviderStatus(name=name))
            for name in ("opentelemetry", "prometheus", "grafana", "jaeger")
        ]

    def record(
        self,
        event: str,
        duration_seconds: float,
        *,
        status: str = "success",
        **attributes: Any,
    ) -> None:
        self.metrics.observe(
            f"{event}_duration_seconds",
            duration_seconds,
            {
                "status": status,
                **{key: str(value) for key, value in attributes.items()},
            },
        )
        self.metrics.increment(f"{event}_total", labels={"status": status})


telemetry = TelemetryService()
