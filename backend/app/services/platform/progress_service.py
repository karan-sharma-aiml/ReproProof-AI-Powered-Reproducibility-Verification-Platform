"""Thread-safe progress broker used by the Phase 4 WebSocket stream."""

from __future__ import annotations

from datetime import datetime, timezone
from queue import Queue
from threading import RLock

from app.services.platform.models import ProgressEvent


class ProgressBroker:
    """Fan out progress events without coupling producers to WebSocket clients."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Queue[ProgressEvent]]] = {}
        self._lock = RLock()

    def publish(
        self,
        execution_id: str,
        stage: str,
        status: str,
        progress: int,
        message: str,
        eta_seconds: float | None = None,
    ) -> ProgressEvent:
        event = ProgressEvent(
            execution_id=execution_id,
            stage=stage,
            status=status,
            progress=progress,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            eta_seconds=eta_seconds,
        )
        with self._lock:
            for subscriber in tuple(self._subscribers.get(execution_id, [])):
                subscriber.put(event)
        return event

    def subscribe(self, execution_id: str) -> Queue[ProgressEvent]:
        subscriber: Queue[ProgressEvent] = Queue()
        with self._lock:
            self._subscribers.setdefault(execution_id, []).append(subscriber)
        return subscriber

    def unsubscribe(self, execution_id: str, subscriber: Queue[ProgressEvent]) -> None:
        with self._lock:
            subscribers = self._subscribers.get(execution_id, [])
            if subscriber in subscribers:
                subscribers.remove(subscriber)
            if not subscribers:
                self._subscribers.pop(execution_id, None)
