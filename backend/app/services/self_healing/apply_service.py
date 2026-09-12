"""Apply a validated patch after creating an immutable backup."""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.services.patch_generator.diff_generator import PatchCandidate
from app.services.patch_generator.models import PatchResult
from app.services.patch_generator.validators import PatchValidator
from app.services.patch_generator.git_utils import read_text_file
from app.services.self_healing.backup_service import BackupService
from app.services.self_healing.models import ApplyResult
from app.services.self_healing.utils import atomic_write, resolve_repository_file

logger = get_logger("self_healing.apply")


class ApplyService:
    """Apply only a stored, validated single-file patch preview."""

    def __init__(
        self,
        backup_service: BackupService | None = None,
        validator: PatchValidator | None = None,
    ) -> None:
        self._backup_service = backup_service or BackupService()
        self._validator = validator or PatchValidator()

    def apply(
        self, execution_id: str, repository: Path, patch: PatchResult
    ) -> ApplyResult:
        if not patch.git_unified_diff or not patch.file_name:
            raise ValueError("Patch contains no applicable file changes")
        target = resolve_repository_file(repository, patch.file_name)
        original = read_text_file(target)
        if original != patch.original_file:
            raise ValueError("Repository file no longer matches the generated patch")
        candidate = PatchCandidate(
            file_name=patch.file_name,
            original_file=patch.original_file,
            modified_file=patch.modified_file,
            summary=patch.summary,
            patch_quality=patch.patch_confidence,
            risk_level=patch.risk_level,
            estimated_success=patch.estimated_success,
            warnings=tuple(patch.warnings),
        )
        self._validator.validate(repository, candidate, patch.git_unified_diff)
        backup = self._backup_service.create_backup(
            execution_id, repository, [patch.file_name]
        )
        try:
            atomic_write(target, patch.modified_file)
            if read_text_file(target) != patch.modified_file:
                raise ValueError("Applied file does not match the validated patch")
        except Exception:
            try:
                self._backup_service.restore(repository, backup)
            except (OSError, ValueError) as rollback_error:
                logger.exception(
                    "Patch rollback failed: execution_id=%s backup=%s",
                    execution_id,
                    backup,
                )
                raise RuntimeError(
                    "Patch application failed and automatic rollback failed"
                ) from rollback_error
            logger.warning(
                "Patch application failed; backup restored: execution_id=%s backup=%s",
                execution_id,
                backup,
            )
            raise
        logger.info(
            "Patch applied: execution_id=%s patch_id=%s file=%s",
            execution_id,
            patch.patch_id,
            patch.file_name,
        )
        return ApplyResult(
            execution_id=execution_id,
            patch_id=patch.patch_id,
            status="APPLIED",
            applied_files=[patch.file_name],
            backup_location=str(backup),
            verified=True,
        )
