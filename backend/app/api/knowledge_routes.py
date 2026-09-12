from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.knowledge_graph import (
    EntityType,
    GraphEntity,
    GraphRelationship,
    RelationshipType,
    graph_builder,
    knowledge_graph,
)
from app.knowledge_graph.models import (
    GraphIndexRequest,
    GraphSearchResult,
    GraphStatistics,
    KnowledgeGraph,
    NeighborResult,
    RelationshipRequest,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge graph"])


def _repository_path(repository_id: str):
    root = get_settings().upload_path.resolve()
    path = (root / repository_id / "repository").resolve()
    if root not in path.parents or not path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )
    return path


@router.post("/index", response_model=KnowledgeGraph)
def index(request: GraphIndexRequest) -> KnowledgeGraph:
    return graph_builder.index_repository(
        request.repository_id, _repository_path(request.repository_id)
    )


@router.get("/entities", response_model=list[GraphEntity])
def entities(entity_type: EntityType | None = None) -> list[GraphEntity]:
    graph = knowledge_graph.graph()
    return [
        entity
        for entity in graph.entities
        if entity_type is None or entity.type == entity_type
    ]


@router.get("/graph", response_model=KnowledgeGraph)
def graph(entity_id: str | None = None) -> KnowledgeGraph:
    return knowledge_graph.graph(entity_id)


@router.get("/search", response_model=list[GraphSearchResult])
def search(
    query: str = Query(..., min_length=1),
    entity_type: EntityType | None = None,
    limit: int = Query(20, ge=1, le=100),
) -> list[GraphSearchResult]:
    return knowledge_graph.search(query, entity_type=entity_type, limit=limit)


@router.get("/neighbors", response_model=list[NeighborResult])
def neighbors(
    entity_id: str,
    depth: int = Query(1, ge=1, le=5),
    limit: int = Query(50, ge=1, le=200),
) -> list[NeighborResult]:
    return knowledge_graph.neighbors(entity_id, depth=depth, limit=limit)


@router.get("/relationships", response_model=list[GraphRelationship])
def relationships(
    relation_type: RelationshipType | None = None,
) -> list[GraphRelationship]:
    relationships = knowledge_graph.graph().relationships
    return [
        item
        for item in relationships
        if relation_type is None or item.type == relation_type
    ]


@router.get("/statistics", response_model=GraphStatistics)
def statistics() -> GraphStatistics:
    return knowledge_graph.statistics()


@router.post("/relationships", response_model=GraphRelationship)
def add_relationship(request: RelationshipRequest) -> GraphRelationship:
    knowledge_graph.upsert_entity(request.source)
    knowledge_graph.upsert_entity(request.target)
    return knowledge_graph.relate(
        GraphRelationship(
            source=request.source.id,
            target=request.target.id,
            type=request.type,
            weight=request.weight,
            properties=request.properties,
        )
    )
