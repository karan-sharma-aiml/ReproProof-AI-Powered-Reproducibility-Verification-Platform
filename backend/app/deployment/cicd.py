from __future__ import annotations

from enum import StrEnum
from typing import Any


class PipelineProvider(StrEnum):
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    AZURE_DEVOPS = "azure_devops"
    JENKINS = "jenkins"
    BUILDKITE = "buildkite"


class PipelineFactory:
    """Returns provider-neutral pipeline steps with optional renderer metadata."""

    def build(self, provider: PipelineProvider) -> dict[str, Any]:
        steps = [
            "checkout",
            "compile",
            "test",
            "build_artifacts",
            "validate_manifests",
            "publish_artifacts",
        ]
        return {
            "provider": provider.value,
            "stages": steps,
            "deployment_gate": "health_verified",
        }
