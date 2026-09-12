from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .contracts import Agent

AgentFactoryFunction = Callable[[], "Agent"]


class AgentRegistry:
    """Process-local registry for discoverable, independently packaged agents."""

    def __init__(self) -> None:
        self._factories: dict[str, AgentFactoryFunction] = {}

    def register(self, name: str, factory: AgentFactoryFunction) -> None:
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("Agent name cannot be empty")
        if normalized in self._factories:
            raise ValueError(f"Agent already registered: {name}")
        self._factories[normalized] = factory

    def unregister(self, name: str) -> None:
        self._factories.pop(name.strip().lower(), None)

    def contains(self, name: str) -> bool:
        return name.strip().lower() in self._factories

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    def resolve(self, name: str) -> AgentFactoryFunction:
        normalized = name.strip().lower()
        try:
            return self._factories[normalized]
        except KeyError as exc:
            raise KeyError(f"Agent is not registered: {name}") from exc
