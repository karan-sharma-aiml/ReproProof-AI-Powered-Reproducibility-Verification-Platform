"""Enhanced patch recommendation service based on error analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger
from app.services.troubleshooter.models import TroubleshootingReport

logger = get_logger("patch_advisor")


@dataclass(frozen=True)
class PatchRecommendation:
    """Structured patch recommendation with patch quality and rationale."""

    target_file: str
    transformation_type: str
    suggested_changes: str
    patch_quality: float
    risk_level: str
    estimated_success: float
    rationale: str
    warnings: list[str]


class EnhancedPatchAdvisor:
    """Provide intelligent patch recommendations based on troubleshooting analysis."""

    def __init__(self) -> None:
        """Initialize the patch advisor."""
        self._logger = logger

    def recommend(
        self, troubleshooting: TroubleshootingReport, file_candidates: list[str]
    ) -> Optional[PatchRecommendation]:
        """
        Generate a patch recommendation based on troubleshooting report.

        Args:
            troubleshooting: TroubleshootingReport with root cause and findings
            file_candidates: List of potential files to patch (e.g., from repository tree)

        Returns:
            PatchRecommendation or None if no safe patch can be recommended
        """
        root_cause = troubleshooting.root_cause.lower()
        error_message = troubleshooting.detected_error or ""

        # ─── Dependency/Import Errors ───────────────────────────────────────
        if self._is_dependency_error(root_cause):
            return self._recommend_dependency_patch(error_message, file_candidates)

        # ─── Type/Value Errors ─────────────────────────────────────────────
        if "type" in root_cause or "typeerror" in error_message.lower():
            return self._recommend_type_fix(root_cause, error_message, file_candidates)

        if "value" in root_cause or "valueerror" in error_message.lower():
            return self._recommend_value_validation(error_message, file_candidates)

        # ─── File/Path Errors ──────────────────────────────────────────────
        if "file" in root_cause or "dataset" in root_cause:
            return self._recommend_path_fix(error_message, file_candidates)

        # ─── Pandas Deprecations ───────────────────────────────────────────
        if "pandas" in error_message.lower() or "append" in error_message.lower():
            return self._recommend_pandas_fix(file_candidates)

        # ─── NumPy Deprecations ────────────────────────────────────────────
        if "numpy" in error_message.lower() or "np.float" in error_message:
            return self._recommend_numpy_fix(file_candidates)

        # ─── Environment Variables ─────────────────────────────────────────
        if "environment" in root_cause or "environ" in error_message.lower():
            return self._recommend_env_var_fix(error_message)

        # ─── No safe patch found ───────────────────────────────────────────
        logger.info("No automatic patch recommended for root cause: %s", root_cause)
        return None

    @staticmethod
    def _is_dependency_error(root_cause: str) -> bool:
        """Check if error is dependency/import related."""
        keywords = ["import", "module", "package", "dependency", "conflict", "version"]
        return any(kw in root_cause for kw in keywords)

    def _recommend_dependency_patch(
        self, error_message: str, file_candidates: list[str]
    ) -> Optional[PatchRecommendation]:
        """Recommend adding missing dependency to requirements.txt."""
        # Extract missing package name
        match = re.search(
            r"No module named ['\"]?([A-Za-z0-9_.-]+)['\"]?", error_message, re.I
        )
        if not match:
            return None

        package_name = match.group(1).split(".", 1)[0]

        # requirements.txt should be in candidates
        if (
            "requirements.txt" not in file_candidates
            and "setup.py" not in file_candidates
        ):
            return None

        target_file = "requirements.txt"

        return PatchRecommendation(
            target_file=target_file,
            transformation_type="add_dependency",
            suggested_changes=f"Add line: {package_name}",
            patch_quality=0.90,
            risk_level="Low",
            estimated_success=0.85,
            rationale=f"Missing package '{package_name}' detected in error; add to requirements.txt",
            warnings=[
                "Verify the package version is compatible with your project",
                "Consider pinning to a specific version for reproducibility",
            ],
        )

    def _recommend_type_fix(
        self, root_cause: str, error_message: str, file_candidates: list[str]
    ) -> Optional[PatchRecommendation]:
        """Recommend type checking or conversion fix."""
        return PatchRecommendation(
            target_file=self._find_main_script(file_candidates),
            transformation_type="add_type_check",
            suggested_changes="Add type validation/conversion",
            patch_quality=0.60,
            risk_level="Medium",
            estimated_success=0.65,
            rationale="Type mismatch detected; automatic fixes require code understanding",
            warnings=[
                "Manual review recommended - automatic type fixes may not match intent",
                "Consider using type hints (Python 3.5+)",
            ],
        )

    def _recommend_value_validation(
        self, error_message: str, file_candidates: list[str]
    ) -> Optional[PatchRecommendation]:
        """Recommend input validation fix."""
        return PatchRecommendation(
            target_file=self._find_main_script(file_candidates),
            transformation_type="add_validation",
            suggested_changes="Add input validation/assertion",
            patch_quality=0.55,
            risk_level="Medium",
            estimated_success=0.60,
            rationale="Invalid value detected; add validation before use",
            warnings=[
                "Automatic detection of correct validation logic is limited",
                "Manual review of input handling strongly recommended",
            ],
        )

    def _recommend_path_fix(
        self, error_message: str, file_candidates: list[str]
    ) -> Optional[PatchRecommendation]:
        """Recommend file path fix."""
        # Extract missing path if possible
        match = re.search(r"['\"]([^'\"]+)['\"]", error_message)
        missing_file = match.group(1) if match else "data file"

        return PatchRecommendation(
            target_file=self._find_main_script(file_candidates),
            transformation_type="fix_path",
            suggested_changes=f"Verify path to '{missing_file}' exists and is correct",
            patch_quality=0.50,
            risk_level="Low",
            estimated_success=0.40,
            rationale="File not found error; verify path is correct",
            warnings=[
                "Cannot automatically fix paths - ensure dataset files are included",
                "Check working directory and relative paths",
            ],
        )

    def _recommend_pandas_fix(
        self, file_candidates: list[str]
    ) -> Optional[PatchRecommendation]:
        """Recommend pandas deprecation fix."""
        target = self._find_file_with_content(file_candidates, ["append"])
        if not target:
            return None

        return PatchRecommendation(
            target_file=target,
            transformation_type="pandas_deprecation",
            suggested_changes="Replace df.append(other) with pd.concat([df, other])",
            patch_quality=0.93,
            risk_level="Low",
            estimated_success=0.88,
            rationale="DataFrame.append is deprecated in pandas 2.0+",
            warnings=[
                "Verify ignore_index and sort parameters match intended behavior",
            ],
        )

    def _recommend_numpy_fix(
        self, file_candidates: list[str]
    ) -> Optional[PatchRecommendation]:
        """Recommend NumPy deprecation fix."""
        target = self._find_file_with_content(
            file_candidates, ["np.float", "np.int", "np.bool"]
        )
        if not target:
            return None

        return PatchRecommendation(
            target_file=target,
            transformation_type="numpy_deprecation",
            suggested_changes="Replace np.float with float, np.int with int, etc.",
            patch_quality=0.91,
            risk_level="Low",
            estimated_success=0.89,
            rationale="NumPy scalar type aliases are deprecated in NumPy 1.20+",
            warnings=[
                "Verify compatibility with code using these types",
            ],
        )

    def _recommend_env_var_fix(
        self, error_message: str
    ) -> Optional[PatchRecommendation]:
        """Recommend environment variable configuration fix."""
        # Extract env var name if possible
        match = re.search(r"([A-Z_][A-Z0-9_]*)", error_message)
        env_var = match.group(1) if match else "REQUIRED_VAR"

        return PatchRecommendation(
            target_file="setup.py or configuration",
            transformation_type="add_env_var",
            suggested_changes=f"Set environment variable: {env_var}=<value>",
            patch_quality=0.75,
            risk_level="Low",
            estimated_success=0.50,
            rationale=f"Missing environment variable '{env_var}'",
            warnings=[
                "Cannot automatically set environment variables",
                "Requires configuration outside of code patches",
            ],
        )

    @staticmethod
    def _find_main_script(file_candidates: list[str]) -> str:
        """Find the main Python script to patch."""
        # Prefer main.py, then __main__.py, then any .py file
        for name in ["main.py", "__main__.py", "run.py"]:
            if any(name in f for f in file_candidates):
                return name

        # Return first .py file
        py_files = [f for f in file_candidates if f.endswith(".py")]
        return py_files[0] if py_files else "main.py"

    @staticmethod
    def _find_file_with_content(
        file_candidates: list[str], keywords: list[str]
    ) -> Optional[str]:
        """Find file most likely containing the keywords (heuristic)."""
        # This is a heuristic - in practice, we'd need to read files
        # For now, just return first Python file
        py_files = [f for f in file_candidates if f.endswith(".py")]
        return py_files[0] if py_files else None


def create_patch_advisor() -> EnhancedPatchAdvisor:
    """Factory to create patch advisor."""
    return EnhancedPatchAdvisor()
