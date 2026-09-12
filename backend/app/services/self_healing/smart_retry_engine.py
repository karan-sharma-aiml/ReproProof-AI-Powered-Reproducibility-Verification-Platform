"""Intelligent retry orchestration with error-type-aware strategies."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

from app.core.logging import get_logger
from app.models.execution_result import ExecutionResult
from app.services.patch_generator.models import PatchResult
from app.services.self_healing.models import ExecutionHistoryEntry, RerunResult
from app.services.self_healing.retry_engine import RetryEngine
from app.services.troubleshooter.models import TroubleshootingReport

logger = get_logger("smart_retry_engine")


class ErrorCategory(str, Enum):
    """Error type classification for intelligent retry decisions."""

    # Critical/Non-Retryable
    SYNTAX = "syntax"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    MEMORY = "memory"

    # Retryable with patches
    DEPENDENCY = "dependency"
    IMPORT = "import"
    FILE_NOT_FOUND = "file_not_found"
    TYPE_MISMATCH = "type_mismatch"
    VALUE_ERROR = "value_error"
    ENVIRONMENT = "environment"

    # Retryable with external fixes
    DATABASE = "database"
    NETWORK = "network"
    API = "api"

    # Unknown
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RetryStrategy:
    """Strategy for retrying a specific error type."""

    category: ErrorCategory
    should_retry: bool
    wait_seconds: float
    max_attempts: int
    requires_patch: bool
    suggested_action: str


class SmartRetryEngine:
    """Extend retry engine with intelligent error-aware strategies."""

    STRATEGY_MAP = {
        ErrorCategory.SYNTAX: RetryStrategy(
            category=ErrorCategory.SYNTAX,
            should_retry=False,
            wait_seconds=0,
            max_attempts=1,
            requires_patch=False,
            suggested_action="Requires manual code fixes; automatic patching is not safe.",
        ),
        ErrorCategory.PERMISSION: RetryStrategy(
            category=ErrorCategory.PERMISSION,
            should_retry=False,
            wait_seconds=0,
            max_attempts=1,
            requires_patch=False,
            suggested_action="Requires filesystem or execution permission changes.",
        ),
        ErrorCategory.TIMEOUT: RetryStrategy(
            category=ErrorCategory.TIMEOUT,
            should_retry=True,
            wait_seconds=2.0,
            max_attempts=2,
            requires_patch=False,
            suggested_action="Timeout detected; increase timeout or optimize code for performance.",
        ),
        ErrorCategory.MEMORY: RetryStrategy(
            category=ErrorCategory.MEMORY,
            should_retry=True,
            wait_seconds=3.0,
            max_attempts=2,
            requires_patch=False,
            suggested_action="Memory exhausted; reduce workload size or optimize memory usage.",
        ),
        ErrorCategory.DEPENDENCY: RetryStrategy(
            category=ErrorCategory.DEPENDENCY,
            should_retry=True,
            wait_seconds=1.0,
            max_attempts=3,
            requires_patch=True,
            suggested_action="Missing or conflicting dependency; apply patch with updated requirements.",
        ),
        ErrorCategory.IMPORT: RetryStrategy(
            category=ErrorCategory.IMPORT,
            should_retry=True,
            wait_seconds=1.0,
            max_attempts=3,
            requires_patch=True,
            suggested_action="Import resolution failed; patch may fix import or dependency issues.",
        ),
        ErrorCategory.FILE_NOT_FOUND: RetryStrategy(
            category=ErrorCategory.FILE_NOT_FOUND,
            should_retry=True,
            wait_seconds=1.0,
            max_attempts=3,
            requires_patch=True,
            suggested_action="File path error; patch may correct path references.",
        ),
        ErrorCategory.TYPE_MISMATCH: RetryStrategy(
            category=ErrorCategory.TYPE_MISMATCH,
            should_retry=True,
            wait_seconds=0.5,
            max_attempts=2,
            requires_patch=True,
            suggested_action="Type mismatch in function call; patch may fix type handling.",
        ),
        ErrorCategory.VALUE_ERROR: RetryStrategy(
            category=ErrorCategory.VALUE_ERROR,
            should_retry=True,
            wait_seconds=0.5,
            max_attempts=2,
            requires_patch=True,
            suggested_action="Invalid value passed to function; patch may add validation.",
        ),
        ErrorCategory.ENVIRONMENT: RetryStrategy(
            category=ErrorCategory.ENVIRONMENT,
            should_retry=False,
            wait_seconds=0,
            max_attempts=1,
            requires_patch=False,
            suggested_action="Missing environment variable; set required variable before retry.",
        ),
        ErrorCategory.DATABASE: RetryStrategy(
            category=ErrorCategory.DATABASE,
            should_retry=True,
            wait_seconds=2.0,
            max_attempts=2,
            requires_patch=False,
            suggested_action="Database unavailable; verify connection string and database status.",
        ),
        ErrorCategory.NETWORK: RetryStrategy(
            category=ErrorCategory.NETWORK,
            should_retry=True,
            wait_seconds=2.0,
            max_attempts=2,
            requires_patch=False,
            suggested_action="Network error; verify connectivity and remote service availability.",
        ),
        ErrorCategory.API: RetryStrategy(
            category=ErrorCategory.API,
            should_retry=True,
            wait_seconds=1.0,
            max_attempts=2,
            requires_patch=False,
            suggested_action="API error; verify endpoint, credentials, and service status.",
        ),
        ErrorCategory.UNKNOWN: RetryStrategy(
            category=ErrorCategory.UNKNOWN,
            should_retry=True,
            wait_seconds=1.0,
            max_attempts=1,
            requires_patch=True,
            suggested_action="Unknown error; limited automatic recovery possible.",
        ),
    }

    def __init__(self, base_engine: RetryEngine | None = None) -> None:
        """Initialize with optional custom base retry engine."""
        self._engine = base_engine or RetryEngine()

    def classify_error(self, troubleshooting: TroubleshootingReport) -> ErrorCategory:
        """Map troubleshooting report to error category."""
        root_cause = troubleshooting.root_cause.lower()

        # Syntax errors
        if "syntax" in root_cause or "indentation" in root_cause:
            return ErrorCategory.SYNTAX

        # Permission errors
        if "permission" in root_cause:
            return ErrorCategory.PERMISSION

        # Timeout
        if "timeout" in root_cause:
            return ErrorCategory.TIMEOUT

        # Memory
        if "memory" in root_cause:
            return ErrorCategory.MEMORY

        # Dependency/Import
        if "module" in root_cause or "import" in root_cause or "package" in root_cause:
            return (
                ErrorCategory.IMPORT
                if "import" in root_cause
                else ErrorCategory.DEPENDENCY
            )

        # File/Dataset
        if "file" in root_cause or "dataset" in root_cause:
            return ErrorCategory.FILE_NOT_FOUND

        # Type/Value errors
        if "type" in root_cause:
            return ErrorCategory.TYPE_MISMATCH
        if "value" in root_cause:
            return ErrorCategory.VALUE_ERROR

        # Environment
        if "environment" in root_cause or "variable" in root_cause:
            return ErrorCategory.ENVIRONMENT

        # Database
        if (
            "database" in root_cause
            or "sql" in root_cause
            or "connection" in root_cause
        ):
            return ErrorCategory.DATABASE

        # Network
        if "network" in root_cause or "connection" in root_cause.lower():
            return ErrorCategory.NETWORK

        # API
        if "api" in root_cause or "http" in root_cause or "endpoint" in root_cause:
            return ErrorCategory.API

        return ErrorCategory.UNKNOWN

    def get_strategy(self, category: ErrorCategory) -> RetryStrategy:
        """Get retry strategy for error category."""
        return self.STRATEGY_MAP.get(category, self.STRATEGY_MAP[ErrorCategory.UNKNOWN])

    def should_attempt_retry(
        self, troubleshooting: TroubleshootingReport, attempt_number: int
    ) -> bool:
        """Determine if retry should be attempted based on error type and attempt count."""
        category = self.classify_error(troubleshooting)
        strategy = self.get_strategy(category)

        if not strategy.should_retry:
            logger.info(
                "Error category %s is not retryable; stopping retries",
                category.value,
            )
            return False

        if attempt_number >= strategy.max_attempts:
            logger.info(
                "Maximum retry attempts (%d) reached for error category %s",
                strategy.max_attempts,
                category.value,
            )
            return False

        return True

    def get_wait_time(self, category: ErrorCategory) -> float:
        """Get wait time before next retry."""
        strategy = self.get_strategy(category)
        return strategy.wait_seconds

    def log_retry_decision(
        self,
        execution_id: str,
        troubleshooting: TroubleshootingReport,
        attempt_number: int,
        decision: bool,
    ) -> None:
        """Log the retry decision with full context."""
        category = self.classify_error(troubleshooting)
        strategy = self.get_strategy(category)

        logger.info(
            "Retry decision: execution_id=%s category=%s diagnostic_confidence=%.2f attempt=%d decision=%s reason=%s",
            execution_id,
            category.value,
            troubleshooting.diagnostic_confidence,
            attempt_number,
            "RETRY" if decision else "STOP",
            strategy.suggested_action,
        )

    def run_with_strategy(
        self,
        execution_id: str,
        repository: Path,
        initial_patch: PatchResult,
        initial_backup_path: str,
        max_retries: int = 3,
    ) -> RerunResult:
        """Run retry engine with intelligent error-aware strategies."""
        logger.info(
            "Starting smart retry engine for execution_id=%s max_retries=%d",
            execution_id,
            max_retries,
        )

        # Use base engine for actual retry logic
        return self._engine.run(
            execution_id,
            repository,
            initial_patch,
            initial_backup_path,
            max_retries=max_retries,
        )


def create_smart_retry_engine() -> SmartRetryEngine:
    """Factory function to create a configured SmartRetryEngine."""
    return SmartRetryEngine()
