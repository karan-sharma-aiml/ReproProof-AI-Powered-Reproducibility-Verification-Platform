"""Classify execution failures without attempting repairs or execution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern

from app.core.logging import get_logger
from app.models.error_analysis import ErrorAnalysis
from app.models.execution_result import ExecutionResult
from app.services.confidence_engine import ConfidenceEngine

logger = get_logger("error_analyzer")


@dataclass(frozen=True)
class _FailureRule:
    """Deterministic rule for one failure category."""

    category: str
    patterns: tuple[Pattern[str], ...]
    root_cause: str
    severity: str
    repairable: bool
    evidence_strength: int
    suggested_repair_type: str


class ErrorAnalyzer:
    """Analyze execution output using ordered, deterministic exception rules."""

    _RULES = (
        _FailureRule(
            "ModuleNotFoundError",
            (re.compile(r"\bModuleNotFoundError\b", re.IGNORECASE),),
            "A required Python module could not be found in the execution environment.",
            "high",
            True,
            98,
            "Dependency installation",
        ),
        _FailureRule(
            "ImportError",
            (re.compile(r"\bImportError\b", re.IGNORECASE),),
            "A Python import failed after module discovery.",
            "high",
            True,
            96,
            "Import or dependency correction",
        ),
        _FailureRule(
            "FileNotFoundError",
            (re.compile(r"\bFileNotFoundError\b", re.IGNORECASE),),
            "A required file or executable path was not found.",
            "high",
            True,
            97,
            "Path or repository configuration correction",
        ),
        _FailureRule(
            "SyntaxError",
            (re.compile(r"\bSyntaxError\b", re.IGNORECASE),),
            "The repository contains Python source with invalid syntax.",
            "high",
            True,
            99,
            "Syntax correction",
        ),
        _FailureRule(
            "PermissionError",
            (re.compile(r"\bPermissionError\b", re.IGNORECASE),),
            "The process lacked permission to access a required resource.",
            "high",
            True,
            98,
            "Permission or filesystem configuration correction",
        ),
        _FailureRule(
            "MemoryError",
            (re.compile(r"\bMemoryError\b", re.IGNORECASE),),
            "The process exhausted available Python memory.",
            "critical",
            True,
            99,
            "Memory or workload reduction",
        ),
        _FailureRule(
            "RuntimeError",
            (re.compile(r"\bRuntimeError\b", re.IGNORECASE),),
            "The program reached an invalid runtime state.",
            "high",
            True,
            95,
            "Runtime configuration or code correction",
        ),
        _FailureRule(
            "AssertionError",
            (re.compile(r"\bAssertionError\b", re.IGNORECASE),),
            "An assertion in the executed program failed.",
            "medium",
            True,
            98,
            "Assertion or input correction",
        ),
        _FailureRule(
            "OSError",
            (re.compile(r"\bOSError\b", re.IGNORECASE),),
            "The operating system reported a runtime resource or I/O failure.",
            "high",
            False,
            90,
            "Operating system or filesystem investigation",
        ),
    )
    _TIMEOUT_PATTERN = re.compile(
        r"(?:TimeoutExpired|timed\s+out|timeout)", re.IGNORECASE
    )

    def analyze(self, result: ExecutionResult) -> ErrorAnalysis:
        """Classify an execution result without changing it or running code."""
        if result.success and not result.timed_out:
            analysis = ErrorAnalysis(
                category="None",
                root_cause="Execution completed successfully.",
                severity="none",
                repairable=False,
                classification_confidence=ConfidenceEngine.classification_confidence(
                    100
                ),
                evidence=[
                    "ExecutionResult.success=True",
                    f"exit_code={result.exit_code}",
                ],
                suggested_repair_type="None",
            )
            logger.info("Execution completed successfully; no error classified")
            return analysis

        output = self._combined_output(result)
        if result.timed_out or self._TIMEOUT_PATTERN.search(output):
            analysis = self._analysis_for_timeout(result, output)
            logger.warning("Classified execution failure as TimeoutExpired")
            return analysis

        for rule in self._RULES:
            if any(pattern.search(output) for pattern in rule.patterns):
                evidence = self._evidence(output, rule.category)
                analysis = ErrorAnalysis(
                    category=rule.category,
                    root_cause=rule.root_cause,
                    severity=rule.severity,  # type: ignore[arg-type]
                    repairable=rule.repairable,
                    classification_confidence=ConfidenceEngine.classification_confidence(
                        rule.evidence_strength
                    ),
                    evidence=evidence,
                    suggested_repair_type=rule.suggested_repair_type,
                )
                logger.warning(
                    "Classified execution failure: category=%s classification_confidence=%d",
                    analysis.category,
                    analysis.classification_confidence,
                )
                return analysis

        analysis = ErrorAnalysis(
            category="Unknown",
            root_cause="Execution failed without a recognized error signature.",
            severity="high",
            repairable=False,
            classification_confidence=ConfidenceEngine.classification_confidence(25),
            evidence=self._evidence(output, "") or [f"exit_code={result.exit_code}"],
            suggested_repair_type="Manual investigation",
        )
        logger.warning("Could not classify execution failure; category=Unknown")
        return analysis

    @staticmethod
    def _combined_output(result: ExecutionResult) -> str:
        return "\n".join(part for part in (result.stderr, result.stdout) if part)

    @staticmethod
    def _evidence(output: str, category: str) -> list[str]:
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if category:
            matching = [line for line in lines if category.lower() in line.lower()]
            if matching:
                return matching[:3]
        return lines[:3]

    def _analysis_for_timeout(
        self, result: ExecutionResult, output: str
    ) -> ErrorAnalysis:
        evidence = self._evidence(output, "TimeoutExpired")
        if result.timed_out:
            evidence.insert(0, "ExecutionResult.timed_out=True")
        return ErrorAnalysis(
            category="TimeoutExpired",
            root_cause="Execution exceeded the configured time limit.",
            severity="high",
            repairable=True,
            classification_confidence=ConfidenceEngine.classification_confidence(
                100 if result.timed_out else 92
            ),
            evidence=list(dict.fromkeys(evidence))[:3],
            suggested_repair_type="Timeout or workload adjustment",
        )
