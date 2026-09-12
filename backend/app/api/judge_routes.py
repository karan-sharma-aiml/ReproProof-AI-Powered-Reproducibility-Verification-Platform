from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.judge.models import JudgeReport, JudgeRequest
from app.judge.service import JudgeEngine

router = APIRouter(prefix="/judge", tags=["AI judge"])
_engine = JudgeEngine()


def _repository_path(repository_id: str) -> Path:
    uploads_root = get_settings().upload_path.resolve()
    repository_path = (uploads_root / repository_id / "repository").resolve()
    if uploads_root not in repository_path.parents or not repository_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )
    return repository_path


@router.post("/evaluate", response_model=JudgeReport)
async def evaluate(request: JudgeRequest) -> JudgeReport:
    return await _engine.evaluate(request, _repository_path(request.repository_id))
