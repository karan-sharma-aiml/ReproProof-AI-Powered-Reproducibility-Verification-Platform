"""Restore one or more self-healing backups."""

from __future__ import annotations

from pathlib import Path

from app.services.self_healing.backup_service import BackupService
from app.services.self_healing.models import RollbackResult


class RollbackService:
    """Restore snapshots in reverse order without running repository code."""

    def __init__(self, backup_service: BackupService | None = None) -> None:
        self._backup_service = backup_service or BackupService()

    def rollback(
        self, execution_id: str, repository: Path, backup_paths: list[str]
    ) -> RollbackResult:
        if not backup_paths:
            raise ValueError("No backup is available for rollback")
        restored: list[str] = []
        for location in reversed(list(dict.fromkeys(backup_paths))):
            restored.extend(self._backup_service.restore(repository, Path(location)))
        return RollbackResult(
            execution_id=execution_id,
            status="ROLLED_BACK",
            restored_files=list(dict.fromkeys(restored)),
            backup_locations=backup_paths,
        )
