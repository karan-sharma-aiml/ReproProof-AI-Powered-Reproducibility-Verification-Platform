from __future__ import annotations

import math
import re
from typing import Any

from app.integrations.composition import ai_gateway

from .documents import DocumentIntelligence
from .models import Citation, DocumentChunk, DocumentSource, RAGAnswer, RetrievalResult


class RAGEngine:
    """Hybrid lexical/vector-ready retrieval and explainable answer assembly."""

    def __init__(
        self, document_intelligence: DocumentIntelligence | None = None
    ) -> None:
        self.documents = document_intelligence or DocumentIntelligence()
        self.sources: dict[str, DocumentSource] = {}
        self.chunks: dict[str, DocumentChunk] = {}

    def index(
        self,
        uri: str,
        content: str | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentSource:
        source, chunks = self.documents.extract(uri, content, title, metadata)
        self.sources[source.id] = source
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
        return source

    def retrieve(
        self, query: str, *, source_id: str | None = None, limit: int = 5
    ) -> list[RetrievalResult]:
        terms = self._terms(query)
        scored: list[RetrievalResult] = []
        for chunk in self.chunks.values():
            if source_id and chunk.source_id != source_id:
                continue
            chunk_terms = self._terms(chunk.text)
            overlap = len(terms & chunk_terms)
            if overlap:
                score = min(
                    1.0, overlap / math.sqrt(max(1, len(terms) * len(chunk_terms)))
                )
                scored.append(
                    RetrievalResult(
                        chunk=chunk,
                        source=self.sources[chunk.source_id],
                        score=score,
                        match_type="lexical",
                    )
                )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

    async def query(
        self,
        query: str,
        *,
        source_id: str | None = None,
        limit: int = 5,
        generate_answer: bool = True,
    ) -> RAGAnswer:
        retrieved = self.retrieve(query, source_id=source_id, limit=limit)
        context = "\n\n".join(item.chunk.text for item in retrieved)
        if generate_answer and context:
            response = await ai_gateway.complete(
                f"Answer using only this evidence:\n{context}\n\nQuestion: {query}"
            )
            provider = "ai-gateway"
        elif context:
            response = context
            provider = "local-retrieval"
        else:
            response = "No indexed evidence matched the query."
            provider = "local-retrieval"
        citations = [
            Citation(
                source_id=item.source.id,
                chunk_id=item.chunk.id,
                title=item.source.title,
                quote=item.chunk.text[:240],
                uri=item.source.uri,
                score=item.score,
            )
            for item in retrieved
        ]
        sources = list({item.source.id: item.source for item in retrieved}.values())
        confidence = (
            sum(item.score for item in retrieved) / len(retrieved) if retrieved else 0.0
        )
        return RAGAnswer(
            query=query,
            answer=response,
            confidence=min(1.0, confidence),
            sources=sources,
            evidence=[citation.quote for citation in citations],
            retrieved_context=retrieved,
            citations=citations,
            related_documents=sources,
            provider=provider,
        )

    def source(self, source_id: str) -> DocumentSource | None:
        return self.sources.get(source_id)

    def context(self, query: str, limit: int = 5) -> list[RetrievalResult]:
        return self.retrieve(query, limit=limit)

    @staticmethod
    def _terms(value: str) -> set[str]:
        return {
            term
            for term in re.findall(r"[a-zA-Z0-9_]{2,}", value.lower())
            if term not in {"the", "and", "for", "with", "from"}
        }


rag_engine = RAGEngine()
