from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.ai.composition import (
    create_production_orchestrator,
    default_reproducibility_workflow,
)
from app.ai.framework import AgentContext
from app.core.config import get_settings

router = APIRouter(prefix="/agents", tags=["agent workflows"])


@router.post("/workflows/reproducibility/{repository_id}")
async def run_reproducibility_workflow(repository_id: str) -> dict[str, Any]:
    """Run the opt-in agent workflow over an already extracted repository."""
    uploads_root = get_settings().upload_path.resolve()
    repository_path = (uploads_root / repository_id / "repository").resolve()
    if uploads_root not in repository_path.parents or not repository_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )
    context = AgentContext(
        repository_metadata={
            "path": str(repository_path),
            "repository_id": repository_id,
        }
    )
    orchestrator = create_production_orchestrator()
    results = await orchestrator.run(default_reproducibility_workflow(), context)
    return {
        "repository_id": repository_id,
        "results": {name: jsonable_encoder(result) for name, result in results.items()},
        "confidence_scores": context.confidence_scores,
        "events": [
            jsonable_encoder(event) for event in orchestrator.message_bus.history
        ],
    }
