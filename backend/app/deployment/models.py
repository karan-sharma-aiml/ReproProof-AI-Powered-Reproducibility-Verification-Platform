from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EnvironmentName(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStrategy(StrEnum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"


class DeploymentStatusName(StrEnum):
    PLANNED = "planned"
    VALIDATED = "validated"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentProfile(BaseModel):
    name: EnvironmentName = EnvironmentName.DEVELOPMENT
    namespace: str = "reproproof"
    backend_image: str = "reproproof/backend:latest"
    frontend_image: str = "reproproof/frontend:latest"
    replicas: int = Field(default=1, ge=1)
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    canary_percent: int = Field(default=10, ge=1, le=100)
    host: str = "reproproof.local"
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: list[str] = Field(default_factory=list)
    resources: dict[str, str] = Field(
        default_factory=lambda: {"cpu": "500m", "memory": "512Mi"}
    )


class DeploymentConfig(BaseModel):
    common: dict[str, Any] = Field(default_factory=dict)
    profiles: dict[EnvironmentName, dict[str, Any]] = Field(default_factory=dict)


class DeploymentPlan(BaseModel):
    release_id: str
    profile: DeploymentProfile
    strategy: DeploymentStrategy
    steps: list[str] = Field(default_factory=list)
    manifests: list[dict[str, Any]] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    field: str
    message: str
    severity: str = "error"


class DeploymentValidation(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class DeploymentStatus(BaseModel):
    release_id: str
    environment: EnvironmentName
    status: DeploymentStatusName
    strategy: DeploymentStrategy
    version: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = ""


class ReleaseRecord(BaseModel):
    release_id: str
    version: str
    environment: EnvironmentName
    strategy: DeploymentStrategy
    status: DeploymentStatusName
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeploymentReport(BaseModel):
    release_id: str
    status: DeploymentStatus
    validation: DeploymentValidation
    health_verified: bool = False
    verification_reason: str = "not_verified"
    steps: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)


class DeploymentRequest(BaseModel):
    environment: EnvironmentName = EnvironmentName.DEVELOPMENT
    version: str = "latest"
    strategy: DeploymentStrategy | None = None


class DeploymentExecutorResult(BaseModel):
    accepted: bool
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
