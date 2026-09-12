"""Tests for backup, apply, rollback, history, and bounded reruns."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models.execution_result import ExecutionResult
from app.services.patch_generator.models import PatchResult
from app.services.self_healing.apply_service import ApplyService
from app.services.self_healing.backup_service import BackupService
from app.services.self_healing.history_service import HistoryService
from app.services.self_healing.models import ExecutionHistoryEntry
from app.services.self_healing.retry_engine import RetryEngine
from app.services.self_healing.rollback_service import RollbackService

PATCH = PatchResult(
    patch_id="patch-1",
    file_name="main.py",
    original_file="value = 1\n",
    modified_file="value = 2\n",
    git_unified_diff="--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n",
    summary="Update value",
    patch_confidence=0.9,
    risk_level="Low",
    estimated_success=0.9,
)


class FakeRerun:
    def rerun(self, repository: Path) -> ExecutionResult:
        return ExecutionResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="still failed",
            execution_time=0.1,
            timed_out=False,
            status="SUBPROCESS_FAILED",
        )


class SelfHealingTest(unittest.TestCase):
    def test_failed_patch_write_is_rolled_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            repository.mkdir()
            target = repository / "main.py"
            target.write_bytes(PATCH.original_file.encode("utf-8"))
            backups = Path(temporary_directory) / "backups"
            service = ApplyService(BackupService(backups))

            with patch(
                "app.services.self_healing.apply_service.atomic_write",
                side_effect=OSError("simulated write failure"),
            ):
                with self.assertRaises(OSError):
                    service.apply("execution-rollback", repository, PATCH)

            self.assertEqual(target.read_text(encoding="utf-8"), PATCH.original_file)

    def test_apply_creates_backup_and_rollback_restores_original(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            repository.mkdir()
            target = repository / "main.py"
            target.write_bytes(PATCH.original_file.encode("utf-8"))
            backups = Path(temporary_directory) / "backups"
            backup_service = BackupService(backups)
            applied = ApplyService(backup_service).apply(
                "execution-1", repository, PATCH
            )
            self.assertEqual(target.read_text(encoding="utf-8"), PATCH.modified_file)
            rolled_back = RollbackService(backup_service).rollback(
                "execution-1", repository, [applied.backup_location]
            )
            self.assertEqual(rolled_back.restored_files, ["main.py"])
            self.assertEqual(target.read_text(encoding="utf-8"), PATCH.original_file)

    def test_history_records_attempts(self) -> None:
        history = HistoryService()
        history.record(
            ExecutionHistoryEntry(
                execution_id="execution-2",
                attempt_number=1,
                execution_status="FAILED",
                duration=0.2,
                reason="initial rerun",
            )
        )
        self.assertEqual(len(history.list("execution-2")), 1)

    def test_retry_engine_stops_at_configured_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            history = HistoryService()
            result = RetryEngine(
                rerun_service=FakeRerun(),
                history_service=history,
            ).run("execution-3", repository, PATCH, "backup-location", max_retries=1)
        self.assertFalse(result.execution.success)
        self.assertEqual(result.retry_count, 0)
        self.assertEqual(len(result.history), 1)


if __name__ == "__main__":
    unittest.main()
