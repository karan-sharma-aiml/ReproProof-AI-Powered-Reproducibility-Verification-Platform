from __future__ import annotations

from threading import RLock

from .models import ExecutionRecord


class InMemoryExecutionCache:
    def __init__(self) -> None:
        self._values: dict[str, ExecutionRecord] = {}
        self._lock = RLock()

    def get(self, key: str) -> ExecutionRecord | None:
        with self._lock:
            return self._values.get(key)

    def put(self, key: str, record: ExecutionRecord) -> None:
        with self._lock:
            self._values[key] = record


class InMemoryJobHistory:
    def __init__(self) -> None:
        self._values: dict[str, ExecutionRecord] = {}
        self._lock = RLock()

    def append(self, record: ExecutionRecord) -> None:
        with self._lock:
            self._values[record.job_id] = record

    def get(self, job_id: str) -> ExecutionRecord | None:
        with self._lock:
            return self._values.get(job_id)

    def list(self, repository_id: str | None = None) -> list[ExecutionRecord]:
        with self._lock:
            records = list(self._values.values())
        if repository_id is not None:
            records = [
                record for record in records if record.repository_id == repository_id
            ]
        return sorted(records, key=lambda record: record.queued_at, reverse=True)
