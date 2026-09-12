from __future__ import annotations

from collections import defaultdict
from threading import Lock


class MetricsRegistry:
    """Small Prometheus exposition registry with no mandatory external dependency."""

    def __init__(self) -> None:
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = (
            defaultdict(float)
        )
        self._histograms: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = (
            defaultdict(list)
        )
        self._lock = Lock()

    def increment(
        self, name: str, value: float = 1, labels: dict[str, str] | None = None
    ) -> None:
        key = (name, tuple(sorted((labels or {}).items())))
        with self._lock:
            self._counters[key] += value

    def observe(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        key = (name, tuple(sorted((labels or {}).items())))
        with self._lock:
            self._histograms[key].append(value)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "histograms": {
                    key: list(values) for key, values in self._histograms.items()
                },
            }

    def prometheus(self) -> str:
        lines = ["# TYPE reproproof_http_requests_total counter"]
        with self._lock:
            for (name, labels), value in self._counters.items():
                lines.append(
                    f"{self._format_name(name)}{self._format_labels(labels)} {value}"
                )
            for (name, labels), values in self._histograms.items():
                prefix = self._format_name(name)
                lines.append(
                    f"{prefix}_count{self._format_labels(labels)} {len(values)}"
                )
                lines.append(f"{prefix}_sum{self._format_labels(labels)} {sum(values)}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_name(name: str) -> str:
        return "reproproof_" + "_".join(part for part in name.lower().split() if part)

    @staticmethod
    def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
        if not labels:
            return ""
        return (
            "{"
            + ",".join(
                f'{key}="{value.replace(chr(34), chr(92) + chr(34))}"'
                for key, value in labels
            )
            + "}"
        )


metrics = MetricsRegistry()
