"""Process-local execution history for self-healing attempts."""

from __future__ import annotations

from threading import RLock

from app.services.self_healing.models import ExecutionHistoryEntry


class HistoryService:
    """Store immutable attempt records keyed by execution ID."""

    def __init__(self) -> None:
        self._records: dict[str, list[ExecutionHistoryEntry]] = {}
        self._lock = RLock()

    def record(self, entry: ExecutionHistoryEntry) -> ExecutionHistoryEntry:
        with self._lock:
            self._records.setdefault(entry.execution_id, []).append(entry)
        return entry

    def list(self, execution_id: str | None = None) -> list[ExecutionHistoryEntry]:
        with self._lock:
            if execution_id:
                return list(self._records.get(execution_id, []))
            return [entry for entries in self._records.values() for entry in entries]

    def clear(self, execution_id: str) -> None:
        with self._lock:
            self._records.pop(execution_id, None)
