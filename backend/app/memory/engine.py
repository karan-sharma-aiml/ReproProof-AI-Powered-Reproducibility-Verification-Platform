from __future__ import annotations

import math
import re
from collections.abc import Sequence
from typing import Any

from app.core.logging import get_logger

from .models import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    MemoryNamespace,
    MemoryQuery,
    MemoryRecord,
    SearchResult,
)
from .ports import EmbeddingProvider, KnowledgeGraphStore, MemoryStore, VectorStore
from .stores import InMemoryKnowledgeGraphStore, InMemoryMemoryStore

logger = get_logger("memory.engine")


class MemoryEngine:
    """Coordinates durable memory, optional semantic retrieval, and knowledge graphs."""

    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        graph_store: KnowledgeGraphStore | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.memory_store = memory_store or InMemoryMemoryStore()
        self.graph_store = graph_store or InMemoryKnowledgeGraphStore()
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    async def remember(
        self,
        namespace: MemoryNamespace,
        subject_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        if not content.strip():
            raise ValueError("Memory content cannot be empty")
        record = MemoryRecord(
            namespace=namespace,
            subject_id=subject_id,
            content=content,
            metadata=metadata or {},
        )
        self.memory_store.append(record)
        if self.embedding_provider and self.vector_store:
            embedding = (await self.embedding_provider.embed([content]))[0]
            record = record.model_copy(update={"embedding_id": embedding.id})
            self.memory_store.append(record)
            await self.vector_store.upsert([record], [embedding])
        return record

    async def retrieve(self, query: MemoryQuery) -> list[SearchResult]:
        if self.embedding_provider and self.vector_store:
            embedding = (await self.embedding_provider.embed([query.query]))[0]
            return await self.vector_store.search(
                embedding.vector,
                limit=query.limit,
                namespace=query.namespace.value if query.namespace else None,
                subject_id=query.subject_id,
            )
        records = self.memory_store.list(
            query.namespace.value if query.namespace else None, query.subject_id
        )
        terms = self._terms(query.query)
        scored = []
        for record in records:
            text_terms = self._terms(record.content)
            overlap = len(terms & text_terms)
            score = overlap / math.sqrt(max(1, len(terms) * len(text_terms)))
            if overlap:
                scored.append(
                    SearchResult(
                        record=record, score=min(1, score), match_type="lexical"
                    )
                )
        return sorted(scored, key=lambda result: result.score, reverse=True)[
            : query.limit
        ]

    def add_node(self, node: GraphNode) -> None:
        self.graph_store.upsert_node(node)

    def add_relation(
        self, source: GraphNode, target: GraphNode, relation: str, weight: float = 1.0
    ) -> None:
        self.graph_store.upsert_node(source)
        self.graph_store.upsert_node(target)
        self.graph_store.upsert_edge(
            GraphEdge(
                source=source.id, target=target.id, relation=relation, weight=weight
            )
        )

    def graph(self, subject_id: str | None = None) -> KnowledgeGraph:
        nodes, edges = self.graph_store.graph(subject_id)
        return KnowledgeGraph(nodes=nodes, edges=edges)

    async def retrieve_context(
        self,
        query: str,
        *,
        namespaces: Sequence[MemoryNamespace] | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        if namespaces is None:
            return await self.retrieve(MemoryQuery(query=query, limit=limit))
        results: list[SearchResult] = []
        for namespace in namespaces:
            results.extend(
                await self.retrieve(
                    MemoryQuery(query=query, namespace=namespace, limit=limit)
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    @staticmethod
    def _terms(value: str) -> set[str]:
        return {
            term
            for term in re.findall(r"[a-z0-9_]{3,}", value.lower())
            if term not in {"the", "and", "for", "with", "from", "that", "this"}
        }
