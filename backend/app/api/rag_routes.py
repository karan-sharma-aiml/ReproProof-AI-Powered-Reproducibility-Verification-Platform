from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.rag import RAGAnswer, RAGQueryRequest, RetrievalResult, rag_engine
from app.rag.models import DocumentSource, IndexDocumentRequest

router = APIRouter(prefix="/rag", tags=["retrieval augmented generation"])


def _approved_uri(uri: str) -> str:
    path = Path(uri).resolve()
    root = get_settings().upload_path.resolve()
    if root not in path.parents and not uri.startswith("memory:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RAG sources must be inside the upload directory",
        )
    return str(path)


@router.post("/index", response_model=DocumentSource)
def index(request: IndexDocumentRequest) -> DocumentSource:
    uri = request.uri if request.content is not None else _approved_uri(request.uri)
    return rag_engine.index(uri, request.content, request.title, request.metadata)


@router.post("/index/repository")
def index_repository(repository_id: str) -> dict[str, object]:
    root = get_settings().upload_path.resolve()
    repository = (root / repository_id / "repository").resolve()
    if root not in repository.parents or not repository.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )
    indexed = 0
    for path in repository.rglob("*"):
        if path.is_file() and path.suffix.lower() in {
            ".py",
            ".md",
            ".txt",
            ".rst",
            ".json",
            ".csv",
            ".ts",
            ".tsx",
        }:
            rag_engine.index(
                str(path), title=path.name, metadata={"repository_id": repository_id}
            )
            indexed += 1
    return {"repository_id": repository_id, "indexed_documents": indexed}


@router.get("/search", response_model=list[RetrievalResult])
def search(
    query: str = Query(..., min_length=1),
    source_id: str | None = None,
    limit: int = Query(5, ge=1, le=50),
) -> list[RetrievalResult]:
    return rag_engine.retrieve(query, source_id=source_id, limit=limit)


@router.post("/query", response_model=RAGAnswer)
async def query(request: RAGQueryRequest) -> RAGAnswer:
    return await rag_engine.query(
        request.query,
        source_id=request.source_id,
        limit=request.limit,
        generate_answer=request.generate_answer,
    )


@router.get("/context", response_model=list[RetrievalResult])
def context(
    query: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=50)
) -> list[RetrievalResult]:
    return rag_engine.context(query, limit)


@router.get("/citations")
def citations(
    query: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=50)
) -> list[dict[str, object]]:
    results = rag_engine.retrieve(query, limit=limit)
    return [
        {
            "source_id": item.source.id,
            "chunk_id": item.chunk.id,
            "title": item.source.title,
            "quote": item.chunk.text[:240],
            "uri": item.source.uri,
            "score": item.score,
        }
        for item in results
    ]


@router.get("/sources", response_model=list[DocumentSource])
def sources() -> list[DocumentSource]:
    return list(rag_engine.sources.values())
