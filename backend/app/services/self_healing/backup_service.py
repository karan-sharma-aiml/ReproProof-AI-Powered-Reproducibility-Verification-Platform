"""Immutable backup snapshots for self-healing file changes."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.logging import get_logger
from app.services.self_healing.models import RollbackResult
from app.services.self_healing.utils import ensure_backup_path, resolve_repository_file

logger = get_logger("self_healing.backup")


class BackupService:
    """Create uniquely named snapshots before any repository write."""

    def __init__(self, backups_root: Path | None = None) -> None:
        self._backups_root = (
            backups_root or Path(__file__).resolve().parents[3] / "backups"
        ).resolve()

    @property
    def backups_root(self) -> Path:
        return self._backups_root

    def create_backup(
        self, execution_id: str, repository: Path, files: list[str]
    ) -> Path:
        if not files:
            raise ValueError("At least one file is required for a backup")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot = (
            self._backups_root / execution_id / f"{timestamp}-{uuid.uuid4().hex[:8]}"
        )
        snapshot.mkdir(parents=True, exist_ok=False)
        manifest: list[str] = []
        for file_name in files:
            source = resolve_repository_file(repository, file_name)
            if not source.is_file():
                raise ValueError(f"Cannot back up missing file: {file_name}")
            destination = snapshot / Path(file_name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            manifest.append(Path(file_name).as_posix())
        (snapshot / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        logger.info(
            "Backup created: execution_id=%s location=%s files=%d",
            execution_id,
            snapshot,
            len(manifest),
        )
        return snapshot

    def restore(self, repository: Path, backup_path: Path) -> list[str]:
        snapshot = ensure_backup_path(backup_path, self._backups_root)
        manifest_path = snapshot / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError("Backup manifest not found")
        files = json.loads(manifest_path.read_text(encoding="utf-8"))
        restored: list[str] = []
        for file_name in files:
            source = ensure_backup_path(snapshot / file_name, snapshot)
            target = resolve_repository_file(repository, file_name)
            if not source.is_file():
                raise ValueError(f"Backup file not found: {file_name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            restored.append(Path(file_name).as_posix())
        logger.info("Backup restored: location=%s files=%d", snapshot, len(restored))
        return restored
