from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import TelemetryProviderStatus, TraceRecord


class TelemetryProvider(ABC):
    """Optional export boundary for a telemetry backend."""

    name: str

    @abstractmethod
    def export_metrics(self, payload: dict[str, Any]) -> None:
        """Export metrics when a deployment configures this provider."""

    @abstractmethod
    def export_trace(self, trace: TraceRecord) -> None:
        """Export a completed trace when a deployment configures this provider."""

    def status(self) -> TelemetryProviderStatus:
        return TelemetryProviderStatus(
            name=self.name, enabled=True, reason="configured"
        )


class OpenTelemetryProvider(TelemetryProvider):
    name = "opentelemetry"

    def export_metrics(self, payload: dict[str, Any]) -> None:
        return None

    def export_trace(self, trace: TraceRecord) -> None:
        return None


class PrometheusProvider(TelemetryProvider):
    name = "prometheus"

    def export_metrics(self, payload: dict[str, Any]) -> None:
        return None

    def export_trace(self, trace: TraceRecord) -> None:
        return None


class GrafanaProvider(TelemetryProvider):
    name = "grafana"

    def export_metrics(self, payload: dict[str, Any]) -> None:
        return None

    def export_trace(self, trace: TraceRecord) -> None:
        return None


class JaegerProvider(TelemetryProvider):
    name = "jaeger"

    def export_metrics(self, payload: dict[str, Any]) -> None:
        return None

    def export_trace(self, trace: TraceRecord) -> None:
        return None
