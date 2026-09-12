from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import ExecutionMetadata


class LLMProvider(ABC):
    """Provider port for research assistance; no model or vendor is hardcoded."""

    @abstractmethod
    async def complete(
        self, prompt: str, *, context: dict[str, Any] | None = None
    ) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


class OCRProvider(ABC):
    @abstractmethod
    async def extract_text(self, document: bytes) -> str: ...


class NoveltyProvider(ABC):
    @abstractmethod
    async def assess(
        self, subject: dict[str, Any], corpus: list[dict[str, Any]]
    ) -> dict[str, Any]: ...


class ResearchAnalysisProvider(ABC):
    """Provider port for claims, gaps, recommendations, and review synthesis."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def analyze(
        self, capability: str, document: dict[str, Any]
    ) -> dict[str, Any]: ...


class SandboxProvider(ABC):
    """Execution boundary. Implementations own isolation and resource limits."""

    @abstractmethod
    async def execute(
        self, command: list[str], *, timeout_seconds: float
    ) -> ExecutionMetadata: ...
