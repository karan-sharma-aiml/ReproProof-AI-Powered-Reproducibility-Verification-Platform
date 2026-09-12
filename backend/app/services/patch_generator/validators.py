"""Validation gates for generated patch previews."""

from __future__ import annotations

import ast
from pathlib import Path

from app.services.patch_generator.diff_generator import (
    PatchCandidate,
    UnifiedDiffGenerator,
)
from app.services.patch_generator.git_utils import (
    read_text_file,
    resolve_repository_file,
)


class PatchValidator:
    """Validate target safety, text format, Python syntax, and diff structure."""

    def validate(
        self,
        repository: Path,
        candidate: PatchCandidate,
        unified_diff: str,
    ) -> list[str]:
        warnings = list(candidate.warnings)
        target = resolve_repository_file(repository, candidate.file_name)
        if not target.is_file():
            raise ValueError(f"Patch target does not exist: {candidate.file_name}")
        if read_text_file(target) != candidate.original_file:
            raise ValueError("Patch target changed while the preview was generated")
        if "\x00" in candidate.modified_file:
            raise ValueError("Binary modifications are not allowed")
        if candidate.file_name.lower().endswith(".py"):
            try:
                ast.parse(candidate.modified_file, filename=candidate.file_name)
            except SyntaxError as exc:
                raise ValueError(f"Generated Python is invalid: {exc}") from exc
        if unified_diff:
            if not unified_diff.startswith(f"--- a/{candidate.file_name}\n"):
                raise ValueError("Malformed unified diff header")
            if f"+++ b/{candidate.file_name}\n" not in unified_diff:
                raise ValueError("Malformed unified diff target")
            if "@@" not in unified_diff:
                raise ValueError("Unified diff is missing a hunk header")
            if not self._preserves_unrelated_lines(
                candidate.original_file, candidate.modified_file
            ):
                raise ValueError("Generated patch removes unrelated code")
        return warnings

    @staticmethod
    def _preserves_unrelated_lines(original: str, modified: str) -> bool:
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        removed = [line for line in original_lines if line not in modified_lines]
        return len(removed) <= 3
