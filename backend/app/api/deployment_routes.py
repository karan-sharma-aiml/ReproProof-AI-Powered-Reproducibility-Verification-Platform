from __future__ import annotations

from fastapi import APIRouter, Query

from app.deployment.cicd import PipelineFactory, PipelineProvider
from app.deployment.docker import DockerArtifactBuilder
from app.deployment.kubernetes import KubernetesManifestBuilder
from app.deployment.models import (
    DeploymentConfig,
    DeploymentPlan,
    DeploymentProfile,
    DeploymentReport,
    DeploymentRequest,
    DeploymentStatus,
    DeploymentValidation,
    EnvironmentName,
)
from app.deployment.services import ConfigurationLoader, DeploymentEngine

router = APIRouter(prefix="/deployment", tags=["deployment"])
_engine = DeploymentEngine()
_config_loader = ConfigurationLoader()
_docker = DockerArtifactBuilder()
_kubernetes = KubernetesManifestBuilder()
_pipelines = PipelineFactory()


def _profile(environment: EnvironmentName) -> DeploymentProfile:
    return DeploymentProfile(name=environment)


@router.get("/status", response_model=DeploymentStatus | None)
def status(release_id: str | None = None) -> DeploymentStatus | None:
    return _engine.releases.status(release_id)


@router.get("/history")
def history() -> list[dict[str, object]]:
    return [record.model_dump(mode="json") for record in _engine.releases.history()]


@router.get("/config")
def config(
    environment: EnvironmentName = EnvironmentName.DEVELOPMENT,
) -> dict[str, object]:
    loaded = _config_loader.load(DeploymentConfig(), environment)
    return {"environment": environment.value, "config": loaded}


@router.post("/plan", response_model=DeploymentPlan)
def plan(request: DeploymentRequest) -> DeploymentPlan:
    deployment_plan, _ = _engine.prepare(request, _profile(request.environment))
    return deployment_plan


@router.post("/validate", response_model=DeploymentValidation)
def validate(request: DeploymentRequest) -> DeploymentValidation:
    return _engine.validator.validate(_profile(request.environment))


@router.post("/report", response_model=DeploymentReport)
def report(request: DeploymentRequest) -> DeploymentReport:
    return _engine.deploy(request, _profile(request.environment))


@router.get("/kubernetes")
def kubernetes(
    environment: EnvironmentName = EnvironmentName.DEVELOPMENT,
) -> list[dict[str, object]]:
    return _kubernetes.build(_profile(environment))


@router.get("/docker")
def docker(
    mode: str = Query(
        "production", pattern="^(development|production|worker|monitoring)$"
    ),
    environment: EnvironmentName = EnvironmentName.DEVELOPMENT,
) -> dict[str, object]:
    profile = _profile(environment)
    return {
        "backend_dockerfile": _docker.backend_dockerfile(),
        "frontend_dockerfile": _docker.frontend_dockerfile(),
        "compose": _docker.compose(profile, mode),
    }


@router.get("/pipeline")
def pipeline(
    provider: PipelineProvider = PipelineProvider.GITHUB_ACTIONS,
) -> dict[str, object]:
    return _pipelines.build(provider)
