from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureFlags:
    repository_analysis: bool = True
    execution_sandbox: bool = True
    risk_analysis: bool = True
    repair_planning: bool = True
    deployment_engine: bool = False
    ai_debug_logging: bool = True
    background_jobs: bool = False


class AppConstants:
    DEFAULT_TIMEOUT_SECONDS = 60
    DEFAULT_PAGE_SIZE = 20
    MAX_RETRY_ATTEMPTS = 3
    DEFAULT_ENVIRONMENT = "development"
    LANGUAGES = ("python", "javascript", "typescript", "bash")
    FEATURE_FLAGS = FeatureFlags()


DEFAULT_FEATURE_FLAGS = FeatureFlags()
