"""Thread-safe publisher for live execution events."""

from __future__ import annotations

from collections.abc import Callable
from queue import Queue

from app.models.execution_event import ExecutionEvent


class ExecutionEventPublisher:
    """Publish events to subscribers and an optional queue for SSE consumers."""

    def __init__(self) -> None:
        self._subscribers: list[Callable[[ExecutionEvent], None]] = []
        self.queue: Queue[ExecutionEvent] = Queue()

    def subscribe(self, callback: Callable[[ExecutionEvent], None]) -> None:
        self._subscribers.append(callback)

    def publish(self, event: ExecutionEvent) -> None:
        self.queue.put(event)
        for subscriber in tuple(self._subscribers):
            subscriber(event)
