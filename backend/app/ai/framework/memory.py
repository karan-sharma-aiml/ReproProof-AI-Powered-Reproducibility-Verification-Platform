from __future__ import annotations

from threading import RLock
from typing import Any


class AgentMemory:
    """Small workflow-scoped memory store, independent from any agent class."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        self._lock = RLock()

    def remember(self, key: str, value: Any) -> None:
        with self._lock:
            self._values[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._values.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._values)
