from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from .models import (
    DeploymentConfig,
    DeploymentExecutorResult,
    DeploymentPlan,
    DeploymentProfile,
    DeploymentReport,
    DeploymentRequest,
    DeploymentStatus,
    DeploymentStatusName,
    DeploymentStrategy,
    DeploymentValidation,
    EnvironmentName,
    ReleaseRecord,
    ValidationIssue,
)
from .ports import DeploymentExecutor, HealthVerifier


class ConfigurationLoader:
    """Loads common settings and applies an environment-specific overlay."""

    def load(
        self, config: DeploymentConfig, environment: EnvironmentName
    ) -> dict[str, object]:
        result = deepcopy(config.common)
        result.update(config.profiles.get(environment, {}))
        return result


class DeploymentPlanner:
    def plan(self, profile: DeploymentProfile, version: str) -> DeploymentPlan:
        release_id = f"rel-{uuid4().hex[:12]}"
        steps = [
            "validate configuration",
            "build or resolve artifacts",
            "apply namespace and configuration",
            "apply workload manifests",
            "wait for health verification",
        ]
        if profile.strategy == DeploymentStrategy.BLUE_GREEN:
            steps.insert(3, "switch service selector after green health check")
        elif profile.strategy == DeploymentStrategy.CANARY:
            steps.insert(3, f"route {profile.canary_percent}% traffic to canary")
        else:
            steps.insert(3, "perform rolling update with readiness gates")
        return DeploymentPlan(
            release_id=release_id,
            profile=profile,
            strategy=profile.strategy,
            steps=steps,
        )


class DeploymentValidator:
    def validate(self, profile: DeploymentProfile) -> DeploymentValidation:
        issues: list[ValidationIssue] = []
        if (
            profile.name == EnvironmentName.PRODUCTION
            and profile.backend_image.endswith(":latest")
        ):
            issues.append(
                ValidationIssue(
                    field="backend_image",
                    message="production requires an immutable image tag",
                )
            )
        if (
            profile.name == EnvironmentName.PRODUCTION
            and profile.frontend_image.endswith(":latest")
        ):
            issues.append(
                ValidationIssue(
                    field="frontend_image",
                    message="production requires an immutable image tag",
                )
            )
        if (
            profile.strategy == DeploymentStrategy.CANARY
            and profile.canary_percent >= 100
        ):
            issues.append(
                ValidationIssue(
                    field="canary_percent", message="canary traffic must be below 100"
                )
            )
        if not profile.host.strip():
            issues.append(
                ValidationIssue(field="host", message="deployment host is required")
            )
        return DeploymentValidation(valid=not issues, issues=issues)


class ReleaseManager:
    def __init__(self) -> None:
        self._history: list[ReleaseRecord] = []
        self._statuses: dict[str, DeploymentStatus] = {}

    def record(self, release: ReleaseRecord) -> ReleaseRecord:
        self._history.append(release)
        self._statuses[release.release_id] = DeploymentStatus(
            release_id=release.release_id,
            environment=release.environment,
            status=release.status,
            strategy=release.strategy,
            version=release.version,
            message="release recorded",
        )
        return release

    def status(self, release_id: str | None = None) -> DeploymentStatus | None:
        if release_id:
            return self._statuses.get(release_id)
        return next(reversed(self._statuses.values()), None) if self._statuses else None

    def history(self) -> list[ReleaseRecord]:
        return list(reversed(self._history))


class RollbackEngine:
    def plan(self, release: ReleaseRecord | None) -> list[str]:
        if release is None:
            return ["no release available for rollback"]
        return [
            f"restore artifacts for release {release.release_id}",
            "restore previous service selectors",
            "verify health before completing rollback",
        ]


class DeploymentEngine:
    def __init__(self, *, release_manager: ReleaseManager | None = None) -> None:
        self.planner = DeploymentPlanner()
        self.validator = DeploymentValidator()
        self.releases = release_manager or ReleaseManager()
        self.rollback = RollbackEngine()

    def prepare(
        self, request: DeploymentRequest, profile: DeploymentProfile
    ) -> tuple[DeploymentPlan, DeploymentValidation]:
        if request.strategy is not None:
            profile = profile.model_copy(update={"strategy": request.strategy})
        return self.planner.plan(profile, request.version), self.validator.validate(
            profile
        )

    def deploy(
        self, request: DeploymentRequest, profile: DeploymentProfile
    ) -> DeploymentReport:
        plan, validation = self.prepare(request, profile)
        status_name = (
            DeploymentStatusName.PLANNED
            if validation.valid
            else DeploymentStatusName.FAILED
        )
        release = ReleaseRecord(
            release_id=plan.release_id,
            version=request.version,
            environment=profile.name,
            strategy=plan.strategy,
            status=status_name,
        )
        self.releases.record(release)
        status = self.releases.status(plan.release_id)
        assert status is not None
        return DeploymentReport(
            release_id=plan.release_id,
            status=status,
            validation=validation,
            steps=plan.steps,
        )


class NoopDeploymentExecutor(DeploymentExecutor):
    def execute(self, plan: DeploymentPlan) -> DeploymentExecutorResult:
        return DeploymentExecutorResult(
            accepted=False,
            message="no deployment provider configured",
            metadata={"release_id": plan.release_id},
        )


class LocalHealthVerifier(HealthVerifier):
    def verify(self, environment: EnvironmentName) -> tuple[bool, str]:
        return True, f"local health verification passed for {environment.value}"
