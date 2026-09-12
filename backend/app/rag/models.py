from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentSource(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    uri: str
    title: str
    document_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    source_id: str
    text: str
    index: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    chunk: DocumentChunk
    source: DocumentSource
    score: float = Field(ge=0, le=1)
    match_type: str = "lexical"


class Citation(BaseModel):
    source_id: str
    chunk_id: str
    title: str
    quote: str
    uri: str
    score: float = Field(ge=0, le=1)


class RAGAnswer(BaseModel):
    query: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    sources: list[DocumentSource] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    retrieved_context: list[RetrievalResult] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    related_documents: list[DocumentSource] = Field(default_factory=list)
    provider: str = "local-retrieval"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    source_id: str | None = None
    limit: int = Field(default=5, ge=1, le=50)
    generate_answer: bool = True


class IndexDocumentRequest(BaseModel):
    uri: str
    title: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
