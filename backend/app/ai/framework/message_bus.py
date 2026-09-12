from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from .events import AgentEvent, EventType

EventHandler = Callable[[AgentEvent], Any]


class MessageBus:
    """In-process event bus; subscribers never need agent-to-agent imports."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self.history: list[AgentEvent] = []

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: AgentEvent) -> None:
        self.history.append(event)
        for handler in self._handlers[event.event_type]:
            result = handler(event)
            if hasattr(result, "__await__"):
                await result
