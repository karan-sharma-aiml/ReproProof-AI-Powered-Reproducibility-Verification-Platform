from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .context import AgentContext


class AgentStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentMetadata:
    name: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: tuple[str, ...] = ()


@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus
    output: Any = None
    error: str | None = None
    confidence: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)


class Agent(ABC):
    """Common lifecycle contract for every independently deployable agent."""

    metadata: AgentMetadata

    @abstractmethod
    async def initialize(self, context: AgentContext) -> None: ...

    @abstractmethod
    async def validate(self, context: AgentContext) -> None: ...

    @abstractmethod
    async def plan(self, context: AgentContext) -> Any: ...

    @abstractmethod
    async def analyze(self, context: AgentContext) -> Any: ...

    @abstractmethod
    async def execute(self, context: AgentContext) -> Any: ...

    @abstractmethod
    async def evaluate(self, context: AgentContext) -> float | None: ...

    @abstractmethod
    async def summarize(self, context: AgentContext) -> Any: ...

    @abstractmethod
    async def cleanup(self, context: AgentContext) -> None: ...
