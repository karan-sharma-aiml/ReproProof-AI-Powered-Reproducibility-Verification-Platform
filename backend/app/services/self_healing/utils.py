"""Shared path and file helpers for self-healing operations."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_repository_file(repository: Path, file_name: str) -> Path:
    root = repository.resolve()
    candidate = (root / file_name).resolve()
    candidate.relative_to(root)
    return candidate


def atomic_write(path: Path, content: str) -> None:
    """Write text beside the target and atomically replace it."""
    temporary = path.with_name(f".{path.name}.reproproof.tmp")
    try:
        temporary.write_text(content, encoding="utf-8", newline="")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_backup_path(path: Path, backups_root: Path) -> Path:
    candidate = path.resolve()
    candidate.relative_to(backups_root.resolve())
    return candidate
