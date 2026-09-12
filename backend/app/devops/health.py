from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass
class HealthMonitor:
    """Dependency health registry with liveness and readiness separation."""

    checks: dict[str, Callable[[], bool]] = field(default_factory=dict)

    def register(self, name: str, check: Callable[[], bool]) -> None:
        self.checks[name] = check

    def live(self) -> dict[str, object]:
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    def ready(self) -> dict[str, object]:
        dependencies: dict[str, bool] = {}
        for name, check in self.checks.items():
            try:
                dependencies[name] = bool(check())
            except Exception:
                dependencies[name] = False
        ready = all(dependencies.values())
        return {
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "dependencies": dependencies,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


health_monitor = HealthMonitor()
