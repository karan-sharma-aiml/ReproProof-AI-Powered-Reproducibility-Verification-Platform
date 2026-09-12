from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.execution.docker import DockerSandboxBuilder
from app.execution.environment import EnvironmentDetector
from app.execution.models import (
    DockerSandboxSpec,
    EnvironmentReport,
    ExecutionJob,
    ExecutionRecord,
)
from app.execution.service import EnterpriseExecutionEngine

router = APIRouter(prefix="/execution-engine", tags=["enterprise execution"])
_engine = EnterpriseExecutionEngine()
_detector = EnvironmentDetector()
_builder = DockerSandboxBuilder()


def _approved_path(path: str) -> Path:
    candidate = Path(path).resolve()
    uploads_root = get_settings().upload_path.resolve()
    if uploads_root not in candidate.parents or not candidate.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository is not inside configured uploads",
        )
    return candidate


@router.get("/environment", response_model=EnvironmentReport)
def environment(
    path: str = Query(
        ..., description="Absolute path to an approved extracted repository"
    )
) -> EnvironmentReport:
    return _detector.detect(_approved_path(path))


@router.post("/docker-spec", response_model=DockerSandboxSpec)
def docker_spec(job: ExecutionJob) -> DockerSandboxSpec:
    _approved_path(job.repository_path)
    return _builder.build(job)


@router.get("/history", response_model=list[ExecutionRecord])
def history(repository_id: str | None = None) -> list[ExecutionRecord]:
    return _engine.history.list(repository_id)
