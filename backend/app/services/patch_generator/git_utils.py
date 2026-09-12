"""Filesystem helpers for repository-safe patch previews."""

from __future__ import annotations

from pathlib import Path


def resolve_repository_file(repository: Path, file_name: str) -> Path:
    """Resolve a relative repository file and reject path traversal."""
    root = repository.resolve()
    candidate = (root / file_name).resolve()
    candidate.relative_to(root)
    return candidate


def read_text_file(path: Path) -> str:
    """Read a UTF-8 source file, rejecting binary content."""
    data = path.read_bytes()
    if b"\x00" in data:
        raise ValueError(f"Binary files cannot be patched: {path.name}")
    return data.decode("utf-8")


def repository_relative_path(repository: Path, path: Path) -> str:
    """Return a normalized repository-relative path."""
    return path.resolve().relative_to(repository.resolve()).as_posix()
