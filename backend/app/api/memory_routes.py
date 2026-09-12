from __future__ import annotations

from fastapi import APIRouter

from app.memory.engine import MemoryEngine
from app.memory.models import (
    GraphRelationRequest,
    KnowledgeGraph,
    MemoryQuery,
    MemoryRecord,
    MemoryWriteRequest,
    SearchResult,
)

router = APIRouter(prefix="/memory", tags=["enterprise memory"])
_engine = MemoryEngine()


@router.post("/records", response_model=MemoryRecord)
async def remember(request: MemoryWriteRequest) -> MemoryRecord:
    return await _engine.remember(
        request.namespace, request.subject_id, request.content, request.metadata
    )


@router.post("/search", response_model=list[SearchResult])
async def search(request: MemoryQuery) -> list[SearchResult]:
    return await _engine.retrieve(request)


@router.post("/context", response_model=list[SearchResult])
async def retrieve_context(request: MemoryQuery) -> list[SearchResult]:
    return await _engine.retrieve_context(request.query, limit=request.limit)


@router.post("/graph/relations", response_model=KnowledgeGraph)
def add_relation(request: GraphRelationRequest) -> KnowledgeGraph:
    _engine.add_relation(
        request.source, request.target, request.relation, request.weight
    )
    return _engine.graph()


@router.get("/graph", response_model=KnowledgeGraph)
def graph(subject_id: str | None = None) -> KnowledgeGraph:
    return _engine.graph(subject_id)
