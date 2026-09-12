from __future__ import annotations

import hashlib
from collections.abc import Sequence

from app.memory.models import Embedding
from app.memory.ports import EmbeddingProvider as MemoryEmbeddingProvider


class LocalEmbeddingProvider(MemoryEmbeddingProvider):
    def __init__(self, name: str = "local-embeddings", dimensions: int = 32) -> None:
        self._name = name
        self._dimensions = dimensions

    @property
    def name(self) -> str:
        return self._name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, texts: Sequence[str]) -> list[Embedding]:
        result = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vector = [byte / 255.0 for byte in digest[: self._dimensions]]
            result.append(
                Embedding(vector=vector, model=self.name, dimensions=self.dimensions)
            )
        return result


class OpenAIEmbeddingProvider(LocalEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__("openai-embeddings", 1536)


class GeminiEmbeddingProvider(LocalEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__("gemini-embeddings", 768)


class SentenceTransformersProvider(LocalEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__("sentence-transformers", 384)


class InstructorXLProvider(LocalEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__("instructor-xl", 768)


class BGEProvider(LocalEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__("bge", 1024)
