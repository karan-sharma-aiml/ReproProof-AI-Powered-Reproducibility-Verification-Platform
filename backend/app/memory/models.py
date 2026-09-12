from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryNamespace(StrEnum):
    REPOSITORY = "repository"
    RESEARCH = "research"
    DATASET = "dataset"
    EXECUTION = "execution"
    PATCH = "patch"
    CONVERSATION = "conversation"


class MemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    namespace: MemoryNamespace
    subject_id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    embedding_id: str | None = None


class MemoryQuery(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    namespace: MemoryNamespace | None = None
    subject_id: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    record: MemoryRecord
    score: float = Field(ge=0, le=1)
    match_type: str = "lexical"


class GraphNode(BaseModel):
    id: str
    label: str
    kind: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float = Field(default=1.0, ge=0, le=1)


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class MemoryRelation(BaseModel):
    source_id: str
    target_id: str
    relation: str
    weight: float = Field(default=1.0, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryWriteRequest(BaseModel):
    namespace: MemoryNamespace
    subject_id: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=100_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphRelationRequest(BaseModel):
    source: GraphNode
    target: GraphNode
    relation: str = Field(min_length=1, max_length=120)
    weight: float = Field(default=1.0, ge=0, le=1)


class Embedding(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    vector: list[float]
    model: str
    dimensions: int
