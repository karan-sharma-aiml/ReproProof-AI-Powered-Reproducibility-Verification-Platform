from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol

from .models import Embedding, GraphEdge, GraphNode, MemoryRecord, SearchResult


class EmbeddingProvider(ABC):
    """Vendor-neutral embedding port for future semantic/RAG providers."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> list[Embedding]: ...


class VectorStore(ABC):
    """Port for pgvector, Qdrant, Pinecone, Milvus, or another vector backend."""

    @abstractmethod
    async def upsert(
        self, records: Sequence[MemoryRecord], embeddings: Sequence[Embedding]
    ) -> None: ...

    @abstractmethod
    async def search(
        self,
        vector: Sequence[float],
        *,
        limit: int,
        namespace: str | None = None,
        subject_id: str | None = None,
    ) -> list[SearchResult]: ...


class MemoryStore(Protocol):
    def append(self, record: MemoryRecord) -> None: ...
    def list(
        self, namespace: str | None = None, subject_id: str | None = None
    ) -> list[MemoryRecord]: ...
    def get(self, record_id: str) -> MemoryRecord | None: ...


class KnowledgeGraphStore(Protocol):
    def upsert_node(self, node: GraphNode) -> None: ...
    def upsert_edge(self, edge: GraphEdge) -> None: ...
    def graph(
        self, subject_id: str | None = None
    ) -> tuple[list[GraphNode], list[GraphEdge]]: ...
