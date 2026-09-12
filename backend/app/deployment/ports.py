from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import (
    DeploymentExecutorResult,
    DeploymentPlan,
    DeploymentProfile,
    EnvironmentName,
)


class SecretProvider(ABC):
    @abstractmethod
    def get(self, name: str) -> str | None: ...


class CloudProvider(ABC):
    name: str

    @abstractmethod
    def describe(self) -> dict[str, Any]: ...


class ArtifactBuilder(ABC):
    @abstractmethod
    def build(self, profile: DeploymentProfile) -> dict[str, Any]: ...


class DeploymentExecutor(ABC):
    @abstractmethod
    def execute(self, plan: DeploymentPlan) -> DeploymentExecutorResult: ...


class ServiceDiscovery(ABC):
    @abstractmethod
    def resolve(self, service: str, environment: EnvironmentName) -> str | None: ...


class HealthVerifier(ABC):
    @abstractmethod
    def verify(self, environment: EnvironmentName) -> tuple[bool, str]: ...
