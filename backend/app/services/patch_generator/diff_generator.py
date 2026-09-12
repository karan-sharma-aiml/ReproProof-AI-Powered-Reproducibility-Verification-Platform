"""Generate real Git-style unified diffs from validated text changes."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PatchCandidate:
    """Candidate file contents and the rationale for a preview."""

    file_name: str
    original_file: str
    modified_file: str
    summary: str
    patch_quality: float
    risk_level: str
    estimated_success: float
    warnings: tuple[str, ...] = ()


class UnifiedDiffGenerator:
    """Generate conservative candidates for known, local transformations."""

    def generate(
        self,
        file_name: str,
        original_file: str,
        root_cause: str,
        error_message: str,
        suggested_fix: str,
        requirements: str,
    ) -> PatchCandidate:
        text = original_file
        summary = "No safe deterministic patch was found."
        patch_quality = 0.0
        risk = "High"
        success = 0.0
        warnings: list[str] = []
        normalized = " ".join((root_cause, error_message, suggested_fix)).lower()

        if (
            self._is_missing_module(normalized)
            and file_name.lower() == "requirements.txt"
        ):
            text, package = self._add_missing_requirement(original_file, error_message)
            if package:
                summary = f"Add missing dependency '{package}' to requirements.txt."
                patch_quality, risk, success = 0.88, "Medium", 0.78
            else:
                warnings.append(
                    "The missing module name could not be safely extracted."
                )
        elif "pandas" in normalized or ".append(" in original_file:
            text = re.sub(
                r"(?P<receiver>\b[A-Za-z_]\w*)\.append\((?P<argument>[^()\n]+)\)",
                r"pd.concat([\g<receiver>, \g<argument>], ignore_index=True)",
                original_file,
            )
            if text != original_file:
                summary = "Replace deprecated pandas DataFrame.append usage with pandas.concat."
                patch_quality, risk, success = 0.93, "Medium", 0.86
            else:
                warnings.append(
                    "No simple pandas append call was found in the target file."
                )
        elif "numpy" in normalized or "numpy alias" in normalized:
            text = re.sub(
                r"\bnp\.(float|int|bool|object|str)\b",
                lambda match: {
                    "float": "float",
                    "int": "int",
                    "bool": "bool",
                    "object": "object",
                    "str": "str",
                }[match.group(1)],
                original_file,
            )
            if text != original_file:
                summary = (
                    "Replace deprecated NumPy scalar aliases with supported built-ins."
                )
                patch_quality, risk, success = 0.91, "Low", 0.89
            else:
                warnings.append(
                    "No deprecated NumPy scalar alias was found in the target file."
                )
        elif "torch._six" in original_file:
            text = original_file.replace(
                "from torch._six import string_classes",
                "string_classes = (str,)",
            )
            if text != original_file:
                summary = "Remove the deprecated torch._six string_classes import."
                patch_quality, risk, success = 0.78, "High", 0.68
            else:
                warnings.append(
                    "The torch import did not match a supported safe transformation."
                )
        else:
            warnings.append(
                "This diagnosis requires human review before a safe patch can be generated."
            )

        return PatchCandidate(
            file_name=file_name,
            original_file=original_file,
            modified_file=text,
            summary=summary,
            patch_quality=patch_quality,
            risk_level=risk,
            estimated_success=success,
            warnings=tuple(warnings),
        )

    @staticmethod
    def unified_diff(file_name: str, original_file: str, modified_file: str) -> str:
        if original_file == modified_file:
            return ""
        return "".join(
            difflib.unified_diff(
                original_file.splitlines(keepends=True),
                modified_file.splitlines(keepends=True),
                fromfile=f"a/{file_name}",
                tofile=f"b/{file_name}",
            )
        )

    @staticmethod
    def _is_missing_module(text: str) -> bool:
        return "modulenotfounderror" in text or "no module named" in text

    @staticmethod
    def _add_missing_requirement(original: str, error_message: str) -> tuple[str, str]:
        match = re.search(
            r"No module named ['\"]([A-Za-z0-9_.-]+)['\"]", error_message, re.I
        )
        if not match:
            return original, ""
        package = match.group(1).split(".", 1)[0]
        existing = {
            line.strip().split("==", 1)[0].lower()
            for line in original.splitlines()
            if line.strip()
        }
        if package.lower() in existing:
            return original, ""
        suffix = "" if not original or original.endswith("\n") else "\n"
        return f"{original}{suffix}{package}\n", package
