from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.research.errors import ResearchFeatureError, RepositoryNotFoundError
from app.research.engines import DockerBuilder, ScoreEngine
from app.research.models import (
    DatasetQualityReport,
    DependencyGraph,
    DockerBuildRequest,
    DockerBuildResult,
    EnvironmentSpec,
    HealthScore,
    RiskHeatmap,
    ScoreReport,
    Timeline,
)
from app.research.services import ResearchIntelligenceService

logger = get_logger("research.api")
router = APIRouter(prefix="/research", tags=["research intelligence"])
_service = ResearchIntelligenceService()
_score_engine = ScoreEngine()
_docker_builder = DockerBuilder()


def _repository_path(repository_id: str) -> Path:
    root = (get_settings().upload_path / repository_id / "repository").resolve()
    uploads_root = get_settings().upload_path.resolve()
    if uploads_root not in root.parents or not root.is_dir():
        raise RepositoryNotFoundError(repository_id)
    return root


def _path_or_404(repository_id: str) -> Path:
    try:
        return _repository_path(repository_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/{repository_id}/risk-heatmap", response_model=RiskHeatmap)
def risk_heatmap(repository_id: str) -> RiskHeatmap:
    return _service.risk_heatmap(repository_id, _path_or_404(repository_id))


@router.get("/{repository_id}/dependency-graph", response_model=DependencyGraph)
def dependency_graph(repository_id: str) -> DependencyGraph:
    return _service.dependency_graph(repository_id, _path_or_404(repository_id))


@router.get("/{repository_id}/health", response_model=HealthScore)
def health(repository_id: str) -> HealthScore:
    return _service.health_score(repository_id, _path_or_404(repository_id))


@router.get("/{repository_id}/environment", response_model=EnvironmentSpec)
def environment(repository_id: str) -> EnvironmentSpec:
    return _service.environment(_path_or_404(repository_id))


@router.get("/{repository_id}/timeline", response_model=Timeline)
def timeline(repository_id: str) -> Timeline:
    return _service.timeline(repository_id, _path_or_404(repository_id))


@router.get("/{repository_id}/scores/{score_name}", response_model=ScoreReport)
def score(repository_id: str, score_name: str) -> ScoreReport:
    """Return a dashboard-ready score from repository evidence."""
    root = _path_or_404(repository_id)
    health_result = _service.health_score(repository_id, root)
    risk_result = _service.risk_heatmap(repository_id, root)
    signals = dict(health_result.subscores)
    signals["risk_control"] = 100 - risk_result.overall_risk
    return _score_engine.score(score_name, signals)


@router.post("/dockerfile", response_model=DockerBuildResult)
def dockerfile(request: DockerBuildRequest) -> DockerBuildResult:
    return _docker_builder.build(request.target)


@router.get("/dataset", response_model=DatasetQualityReport)
def dataset_quality(
    path: str = Query(..., description="Absolute path to an approved local dataset")
) -> DatasetQualityReport:
    dataset_path = Path(path).resolve()
    uploads_root = get_settings().upload_path.resolve()
    if uploads_root not in dataset_path.parents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dataset must be inside the configured upload directory",
        )
    try:
        return _service.dataset_report(dataset_path)
    except ResearchFeatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
