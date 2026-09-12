from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..models import Alert, AlertSeverity


@dataclass(frozen=True)
class AlertRule:
    name: str
    threshold: float
    severity: AlertSeverity
    predicate: Callable[[float, float], bool]


class AlertEngine:
    """Evaluates pluggable threshold rules without binding to a notification vendor."""

    def __init__(self, rules: list[AlertRule] | None = None) -> None:
        self.rules = rules or self.default_rules()

    def evaluate(self, values: dict[str, float]) -> list[Alert]:
        alerts = []
        for rule in self.rules:
            if rule.name in values and rule.predicate(
                values[rule.name], rule.threshold
            ):
                alerts.append(
                    Alert(
                        rule=rule.name,
                        severity=rule.severity,
                        message=f"{rule.name} exceeded threshold",
                        value=values[rule.name],
                        threshold=rule.threshold,
                    )
                )
        return alerts

    @staticmethod
    def default_rules() -> list[AlertRule]:
        return [
            AlertRule(
                "error_rate",
                0.05,
                AlertSeverity.CRITICAL,
                lambda value, threshold: value > threshold,
            ),
            AlertRule(
                "agent_latency_seconds",
                30,
                AlertSeverity.WARNING,
                lambda value, threshold: value > threshold,
            ),
            AlertRule(
                "memory_bytes",
                2_000_000_000,
                AlertSeverity.CRITICAL,
                lambda value, threshold: value > threshold,
            ),
            AlertRule(
                "provider_failures",
                1,
                AlertSeverity.CRITICAL,
                lambda value, threshold: value >= threshold,
            ),
            AlertRule(
                "queue_backlog",
                100,
                AlertSeverity.WARNING,
                lambda value, threshold: value > threshold,
            ),
            AlertRule(
                "sandbox_failures",
                1,
                AlertSeverity.CRITICAL,
                lambda value, threshold: value >= threshold,
            ),
            AlertRule(
                "configuration_errors",
                1,
                AlertSeverity.CRITICAL,
                lambda value, threshold: value >= threshold,
            ),
        ]
