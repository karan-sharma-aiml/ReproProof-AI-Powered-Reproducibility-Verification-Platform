from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Sequence

from .contracts import (
    ChatRequest,
    ChatResponse,
    EmbeddingProvider,
    LLMProvider,
    OCRProvider,
    ProviderCapability,
    ProviderHealth,
    Usage,
    VectorProvider,
)


class MockLLMProvider(LLMProvider):
    name = "local-mock"
    default_model = "mock-model"
    priority = 1000
    capabilities = frozenset(
        {
            ProviderCapability.CHAT,
            ProviderCapability.STREAMING,
            ProviderCapability.STRUCTURED_OUTPUT,
            ProviderCapability.TOOL_CALLING,
            ProviderCapability.VISION,
            ProviderCapability.EMBEDDINGS,
        }
    )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        prompt = request.messages[-1].get("content", "") if request.messages else ""
        content = (
            '{"status":"mock_response","message":"provider credentials are not configured"}'
            if request.response_format == "json"
            else f"Mock provider response: {prompt}"[:2000]
        )
        tokens = max(1, len(content.split()))
        return ChatResponse(
            self.name,
            request.model or "mock-model",
            content,
            Usage(tokens, tokens, tokens * 2, 0.0),
            metadata={"fallback": True},
        )

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            self.name,
            True,
            False,
            "credential-free deterministic fallback",
            0,
            False,
            (self.default_model,),
        )


class MockEmbeddingProvider(EmbeddingProvider):
    name = "local-embeddings"
    dimensions = 32

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append([(byte / 255.0) for byte in digest[: self.dimensions]])
        return vectors


class InMemoryVectorProvider(VectorProvider):
    name = "local-vector"
    capabilities = frozenset({ProviderCapability.HYBRID_SEARCH})

    def __init__(self) -> None:
        self._collections: dict[tuple[str, str | None], dict[str, dict[str, Any]]] = (
            defaultdict(dict)
        )

    async def upsert(
        self,
        collection: str,
        records: Sequence[dict[str, Any]],
        namespace: str | None = None,
    ) -> None:
        bucket = self._collections[(collection, namespace)]
        for record in records:
            bucket[str(record["id"])] = dict(record)

    async def delete(
        self, collection: str, ids: Sequence[str], namespace: str | None = None
    ) -> None:
        bucket = self._collections[(collection, namespace)]
        for record_id in ids:
            bucket.pop(record_id, None)

    async def search(
        self,
        collection: str,
        vector: Sequence[float],
        *,
        limit: int = 10,
        namespace: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        records = list(self._collections[(collection, namespace)].values())
        if filters:
            records = [
                record
                for record in records
                if all(
                    record.get("metadata", {}).get(key) == value
                    for key, value in filters.items()
                )
            ]
        return records[:limit]


class MockOCRProvider(OCRProvider):
    name = "local-ocr"

    async def extract_text(self, document: bytes) -> str:
        return document.decode("utf-8", errors="ignore")
