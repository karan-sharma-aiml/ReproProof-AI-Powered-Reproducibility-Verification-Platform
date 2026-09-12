"""Bounded self-healing retry orchestration."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from app.core.logging import get_logger
from app.models.execution_result import ExecutionResult
from app.services.patch_generator.models import PatchGenerationInput, PatchResult
from app.services.patch_generator.patch_service import (
    PatchGenerationService,
    runtime_environment,
)
from app.services.repository_analysis_service import RepositoryAnalysisService
from app.services.self_healing.apply_service import ApplyService
from app.services.self_healing.history_service import HistoryService
from app.services.self_healing.models import ExecutionHistoryEntry, RerunResult
from app.services.self_healing.rerun_service import RerunService
from app.services.troubleshooter.service import TroubleshootingService

logger = get_logger("self_healing.retry")


class RetryEngine:
    """Rerun and, after failures, diagnose and apply at most three patches."""

    MAX_RETRIES = 3

    def __init__(
        self,
        rerun_service: RerunService | None = None,
        history_service: HistoryService | None = None,
        troubleshooter: TroubleshootingService | None = None,
        patch_generator: PatchGenerationService | None = None,
        apply_service: ApplyService | None = None,
    ) -> None:
        self._rerun = rerun_service or RerunService()
        self._history = history_service or HistoryService()
        self._troubleshooter = troubleshooter or TroubleshootingService()
        self._patch_generator = patch_generator or PatchGenerationService()
        self._apply = apply_service or ApplyService()

    def run(
        self,
        execution_id: str,
        repository: Path,
        initial_patch: PatchResult,
        initial_backup_path: str,
        max_retries: int = MAX_RETRIES,
    ) -> RerunResult:
        limit = max(1, min(max_retries, self.MAX_RETRIES))
        current = self._rerun.rerun(repository)
        self._record(
            execution_id,
            1,
            initial_patch,
            current,
            initial_backup_path,
            "Initial patched rerun",
        )
        applied_patch = initial_patch
        backup_path = initial_backup_path
        if current.success:
            return self._result(execution_id, current, applied_patch, backup_path)

        for attempt in range(2, limit + 1):
            metadata = RepositoryAnalysisService().analyze_repository(
                repository, execution_id
            )
            troubleshooting = self._troubleshooter.troubleshoot(
                execution_id, current, repository, metadata.tree
            )
            requirements_path = repository / "requirements.txt"
            requirements = (
                requirements_path.read_text(encoding="utf-8", errors="ignore")
                if requirements_path.is_file()
                else ""
            )
            patch = self._patch_generator.generate(
                PatchGenerationInput(
                    execution_id=execution_id,
                    repository_path=str(repository),
                    repository_tree=metadata.tree,
                    execution_logs=troubleshooting.execution_log,
                    stacktrace=current.stderr,
                    error_message=troubleshooting.detected_error or current.stderr,
                    root_cause=troubleshooting.root_cause,
                    human_explanation=troubleshooting.explanation,
                    suggested_fix=" ".join(troubleshooting.possible_fixes),
                    requirements=requirements,
                    environment=runtime_environment(),
                )
            )
            if not patch.git_unified_diff:
                self._record(
                    execution_id,
                    attempt,
                    patch,
                    current,
                    "",
                    "No validated follow-up patch generated",
                )
                break
            applied = self._apply.apply(execution_id, repository, patch)
            applied_patch = patch
            backup_path = applied.backup_location
            current = self._rerun.rerun(repository)
            self._record(
                execution_id,
                attempt,
                patch,
                current,
                backup_path,
                "Follow-up patch retry",
            )
            if current.success:
                break
        return self._result(execution_id, current, applied_patch, backup_path)

    def _record(
        self,
        execution_id: str,
        attempt: int,
        patch: PatchResult,
        execution: ExecutionResult,
        backup: str,
        reason: str,
    ) -> None:
        self._history.record(
            ExecutionHistoryEntry(
                execution_id=execution_id,
                attempt_number=attempt,
                patch_id=patch.patch_id,
                applied_files=patch.changed_files,
                execution_status=execution.status,
                duration=execution.execution_time,
                reason=reason,
                backup_path=backup,
                execution=execution,
            )
        )

    def _result(
        self,
        execution_id: str,
        execution: ExecutionResult,
        patch: PatchResult,
        backup: str,
    ) -> RerunResult:
        history = self._history.list(execution_id)
        return RerunResult(
            execution_id=execution_id,
            final_status="SUCCEEDED" if execution.success else "FAILED",
            retry_count=max(0, len(history) - 1),
            execution=execution,
            history=history,
            applied_patch=patch,
            backup_path=backup,
            rollback_available=bool(backup),
        )
