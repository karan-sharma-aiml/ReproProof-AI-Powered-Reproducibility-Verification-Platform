"""Application service for preview-only patch generation."""

from __future__ import annotations

import platform
import sys
import time
import uuid
from pathlib import Path

from app.core.logging import get_logger
from app.services.patch_generator.diff_generator import UnifiedDiffGenerator
from app.services.patch_generator.git_utils import (
    read_text_file,
    repository_relative_path,
    resolve_repository_file,
)
from app.services.patch_generator.models import PatchGenerationInput, PatchResult
from app.services.patch_generator.prompts import build_patch_prompt
from app.services.patch_generator.validators import PatchValidator
from app.services.confidence_engine import ConfidenceEngine

logger = get_logger("patch_generator")


class PatchGenerationService:
    """Generate and validate a patch preview without applying or executing it."""

    PROVIDER = "deterministic-local"

    def __init__(
        self,
        diff_generator: UnifiedDiffGenerator | None = None,
        validator: PatchValidator | None = None,
    ) -> None:
        self._diff_generator = diff_generator or UnifiedDiffGenerator()
        self._validator = validator or PatchValidator()

    def generate(self, evidence: PatchGenerationInput) -> PatchResult:
        started = time.perf_counter()
        repository = Path(evidence.repository_path).resolve()
        file_name = self._target_file(evidence, repository)
        warnings: list[str] = []
        original = ""
        modified = ""
        unified_diff = ""
        summary = "No safe deterministic patch was found."
        patch_quality = 0.0
        risk_level = "High"
        estimated_success = 0.0

        if file_name:
            target = resolve_repository_file(repository, file_name)
            original = read_text_file(target)
            candidate = self._diff_generator.generate(
                repository_relative_path(repository, target),
                original,
                evidence.root_cause,
                evidence.error_message,
                evidence.suggested_fix,
                evidence.requirements,
            )
            modified = candidate.modified_file
            unified_diff = self._diff_generator.unified_diff(
                candidate.file_name, candidate.original_file, candidate.modified_file
            )
            warnings.extend(
                self._validator.validate(repository, candidate, unified_diff)
            )
            file_name = candidate.file_name
            summary = candidate.summary
            patch_quality = candidate.patch_quality
            risk_level = candidate.risk_level
            estimated_success = candidate.estimated_success
        else:
            warnings.append(
                "No problematic source file could be identified from the execution evidence."
            )

        prompt = build_patch_prompt(evidence.model_dump())
        completion = " ".join((summary, *warnings))
        latency_ms = (time.perf_counter() - started) * 1000
        result = PatchResult(
            patch_id=uuid.uuid4().hex[:12],
            file_name=file_name,
            original_file=original,
            modified_file=modified,
            git_unified_diff=unified_diff,
            summary=summary,
            patch_confidence=ConfidenceEngine.patch_confidence(patch_quality),
            risk_level=risk_level,
            estimated_success=estimated_success,
            warnings=warnings,
            changed_files=[file_name] if unified_diff else [],
            provider=self.PROVIDER,
            prompt_tokens=self._token_count(prompt),
            completion_tokens=self._token_count(completion),
            latency_ms=latency_ms,
        )
        logger.info(
            "Patch generation complete: execution_id=%s provider=%s prompt_tokens=%d completion_tokens=%d latency_ms=%.2f patch_confidence=%.2f",
            evidence.execution_id,
            result.provider,
            result.prompt_tokens,
            result.completion_tokens,
            result.latency_ms,
            result.patch_confidence,
        )
        return result

    @staticmethod
    def _target_file(evidence: PatchGenerationInput, repository: Path) -> str:
        if evidence.problematic_file:
            return evidence.problematic_file
        for line in evidence.stacktrace.splitlines():
            if ".py" in line:
                start = line.find('File "')
                if start >= 0:
                    value = Path(line[start + 6 :].split('"', 1)[0])
                    try:
                        return repository_relative_path(repository, value)
                    except ValueError:
                        return value.name
        if evidence.root_cause == "ModuleNotFoundError" and any(
            Path(item).name == "requirements.txt" for item in evidence.repository_tree
        ):
            return "requirements.txt"
        diagnosis = " ".join(
            (evidence.root_cause, evidence.error_message, evidence.suggested_fix)
        ).lower()
        for item in evidence.repository_tree:
            if not item.lower().endswith(".py"):
                continue
            try:
                content = read_text_file(resolve_repository_file(repository, item))
            except (OSError, UnicodeError, ValueError):
                continue
            if "append(" in content and (
                "pandas" in diagnosis or "deprecated" in diagnosis
            ):
                return item
            if "np." in content and "numpy" in diagnosis:
                return item
            if "torch._six" in content and "torch" in diagnosis:
                return item
        return ""

    @staticmethod
    def _token_count(text: str) -> int:
        return len(text.split())


def runtime_environment() -> dict[str, str]:
    """Return stable runtime context for patch-generation requests."""
    return {
        "python": sys.version.split()[0],
        "os": platform.system(),
        "release": platform.release(),
    }
