from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    REPOSITORY = "repository"
    PROJECT = "project"
    RESEARCH_PAPER = "research_paper"
    DATASET = "dataset"
    AGENT = "agent"
    USER = "user"
    WORKFLOW = "workflow"
    SCORE = "score"
    JUDGE_RESULT = "judge_result"
    DEPENDENCY = "dependency"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    EXPERIMENT = "experiment"
    PUBLICATION = "publication"
    EVIDENCE = "evidence"
    RECOMMENDATION = "recommendation"


class RelationshipType(StrEnum):
    DEPENDS_ON = "depends_on"
    GENERATED_BY = "generated_by"
    REVIEWED_BY = "reviewed_by"
    RELATED_TO = "related_to"
    CITES = "cites"
    IMPORTS = "imports"
    EXTENDS = "extends"
    EXECUTES = "executes"
    EVALUATES = "evaluates"
    REFERENCES = "references"
    CONTAINS = "contains"


class GraphEntity(BaseModel):
    id: str
    type: EntityType
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GraphRelationship(BaseModel):
    source: str
    target: str
    type: RelationshipType
    weight: float = Field(default=1.0, ge=0, le=1)
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraph(BaseModel):
    entities: list[GraphEntity] = Field(default_factory=list)
    relationships: list[GraphRelationship] = Field(default_factory=list)


class GraphSearchResult(BaseModel):
    entity: GraphEntity
    score: float = Field(ge=0, le=1)
    matched_fields: list[str] = Field(default_factory=list)


class NeighborResult(BaseModel):
    entity: GraphEntity
    relationship: GraphRelationship
    direction: str
    distance: int = 1


class GraphStatistics(BaseModel):
    entities: int
    relationships: int
    by_type: dict[str, int] = Field(default_factory=dict)
    centrality: dict[str, float] = Field(default_factory=dict)


class GraphIndexRequest(BaseModel):
    repository_id: str


class RelationshipRequest(BaseModel):
    source: GraphEntity
    target: GraphEntity
    type: RelationshipType
    weight: float = Field(default=1.0, ge=0, le=1)
    properties: dict[str, Any] = Field(default_factory=dict)
