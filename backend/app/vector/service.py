from __future__ import annotations

from app.providers.contracts import ProviderCapability, VectorProvider
from app.providers.mock import InMemoryVectorProvider


class FAISSProvider(InMemoryVectorProvider):
    name = "faiss"


class ChromaDBProvider(InMemoryVectorProvider):
    name = "chromadb"


class QdrantProvider(InMemoryVectorProvider):
    name = "qdrant"


class PineconeProvider(InMemoryVectorProvider):
    name = "pinecone"


class WeaviateProvider(InMemoryVectorProvider):
    name = "weaviate"


class MilvusProvider(InMemoryVectorProvider):
    name = "milvus"


class VectorGateway:
    def __init__(self, provider: VectorProvider | None = None) -> None:
        self.provider = provider or InMemoryVectorProvider()

    async def upsert(self, *args, **kwargs):
        return await self.provider.upsert(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self.provider.delete(*args, **kwargs)

    async def search(self, *args, **kwargs):
        return await self.provider.search(*args, **kwargs)
