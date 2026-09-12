from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, AsyncIterator, Sequence


class ProviderKind(StrEnum):
    LLM = "llm"
    EMBEDDING = "embedding"
    VECTOR = "vector"
    OCR = "ocr"


class ProviderCapability(StrEnum):
    CHAT = "chat"
    STREAMING = "streaming"
    STRUCTURED_OUTPUT = "structured_output"
    TOOL_CALLING = "tool_calling"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    OCR = "ocr"
    TABLE_EXTRACTION = "table_extraction"
    HYBRID_SEARCH = "hybrid_search"


@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    healthy: bool
    configured: bool
    reason: str = ""
    latency_ms: float = 0
    connected: bool = False
    available_models: tuple[str, ...] = ()
    default_provider: bool = False
    model: str = ""
    last_error: str = ""
    api_reachable: bool = False


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0


@dataclass(frozen=True)
class ChatRequest:
    messages: Sequence[dict[str, Any]]
    model: str | None = None
    temperature: float = 0.0
    tools: Sequence[dict[str, Any]] = field(default_factory=tuple)
    response_format: str | None = None
    image_inputs: Sequence[str] = field(default_factory=tuple)
    timeout_seconds: float = 30
    max_tokens: int | None = None


@dataclass(frozen=True)
class ChatResponse:
    provider: str
    model: str
    content: str
    usage: Usage = field(default_factory=Usage)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    name: str
    capabilities: frozenset[ProviderCapability]
    priority: int = 100
    cost_per_1k_tokens: float = 0.0

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse: ...

    async def stream(self, request: ChatRequest) -> AsyncIterator[str]:
        response = await self.chat(request)
        yield response.content

    async def structured(self, request: ChatRequest) -> ChatResponse:
        return await self.chat(
            ChatRequest(**{**request.__dict__, "response_format": "json"})
        )

    async def vision(self, request: ChatRequest) -> ChatResponse:
        if ProviderCapability.VISION not in self.capabilities:
            raise NotImplementedError(f"{self.name} does not support vision")
        return await self.chat(request)

    def retry_policy(self) -> dict[str, float]:
        return {"max_attempts": 2, "timeout_seconds": 30, "backoff_seconds": 0.1}

    async def health(self) -> ProviderHealth:
        return ProviderHealth(self.name, True, False, "mock_or_local_provider")


class EmbeddingProvider(ABC):
    name: str
    dimensions: int = 384

    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...

    async def health(self) -> ProviderHealth:
        return ProviderHealth(self.name, True, False, "mock_or_local_provider")


class VectorProvider(ABC):
    name: str
    capabilities: frozenset[ProviderCapability] = frozenset()

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        records: Sequence[dict[str, Any]],
        namespace: str | None = None,
    ) -> None: ...

    @abstractmethod
    async def delete(
        self, collection: str, ids: Sequence[str], namespace: str | None = None
    ) -> None: ...

    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: Sequence[float],
        *,
        limit: int = 10,
        namespace: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...

    async def update(
        self,
        collection: str,
        records: Sequence[dict[str, Any]],
        namespace: str | None = None,
    ) -> None:
        await self.upsert(collection, records, namespace)

    async def hybrid_search(
        self,
        collection: str,
        vector: Sequence[float],
        text: str,
        *,
        limit: int = 10,
        namespace: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self.search(
            collection, vector, limit=limit, namespace=namespace, filters=filters
        )

    async def health(self) -> ProviderHealth:
        return ProviderHealth(self.name, True, False, "mock_or_local_provider")


class OCRProvider(ABC):
    name: str
    capabilities: frozenset[ProviderCapability] = frozenset({ProviderCapability.OCR})

    @abstractmethod
    async def extract_text(self, document: bytes) -> str: ...

    async def extract_tables(self, document: bytes) -> list[list[list[str]]]:
        return []

    async def health(self) -> ProviderHealth:
        return ProviderHealth(self.name, True, False, "mock_or_local_provider")
