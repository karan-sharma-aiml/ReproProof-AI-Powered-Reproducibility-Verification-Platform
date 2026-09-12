from __future__ import annotations

from typing import Any

from .context import AgentContext
from .contracts import Agent, AgentMetadata
from .events import AgentEvent, EventType
from .memory import AgentMemory
from .message_bus import MessageBus


class BaseAgent(Agent):
    """Runtime-aware base class for production agents."""

    metadata: AgentMetadata

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        memory: AgentMemory | None = None,
    ) -> None:
        self.message_bus = message_bus
        self.memory = memory
        self._output: Any = None
        self._confidence = 0.0

    def attach_runtime(self, message_bus: MessageBus, memory: AgentMemory) -> None:
        self.message_bus = message_bus
        self.memory = memory

    async def initialize(self, context: AgentContext) -> None:
        return None

    async def validate(self, context: AgentContext) -> None:
        return None

    async def plan(self, context: AgentContext) -> Any:
        return None

    async def analyze(self, context: AgentContext) -> Any:
        return None

    async def execute(self, context: AgentContext) -> Any:
        return self._output

    async def evaluate(self, context: AgentContext) -> float | None:
        return self._confidence

    async def summarize(self, context: AgentContext) -> Any:
        return self.explain(context)

    async def cleanup(self, context: AgentContext) -> None:
        return None

    async def publish(
        self, event_type: EventType, payload: dict[str, Any] | None = None
    ) -> None:
        if self.message_bus is not None:
            await self.message_bus.publish(
                AgentEvent(event_type, self.metadata.name, payload or {})
            )

    def remember(self, key: str, value: Any) -> None:
        if self.memory is not None:
            self.memory.remember(f"{self.metadata.name}:{key}", value)

    async def write_context(self, context: AgentContext, key: str, value: Any) -> None:
        context.set(key, value)
        self.remember(key, value)
        await self.publish(EventType.CONTEXT_UPDATED, {"key": key})

    def explain(self, context: AgentContext) -> dict[str, Any]:
        return {
            "agent": self.metadata.name,
            "why": "The result is derived from the evidence available in AgentContext.",
            "how": "The agent used its bounded capability and wrote the result to shared context.",
            "evidence": list(
                context.intermediate_results.get(self.metadata.name, {}).get(
                    "evidence", []
                )
            ),
            "confidence": self._confidence,
            "alternatives": [],
            "tradeoffs": [],
        }
