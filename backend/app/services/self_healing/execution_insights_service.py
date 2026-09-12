"""Analytics and insights service for self-healing execution history."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.core.logging import get_logger
from app.models.final_verification_report import FinalVerificationReport
from app.services.self_healing.history_service import HistoryService
from app.services.self_healing.models import ExecutionHistoryEntry
from app.services.troubleshooter.models import TroubleshootingReport
from app.services.confidence_engine import ConfidenceEngine

logger = get_logger("execution_insights")


@dataclass(frozen=True)
class ExecutionInsight:
    """Structured insight about an execution attempt."""

    execution_id: str
    total_attempts: int
    successful_attempt: int | None
    final_status: Literal["SUCCESS", "FAILED", "PARTIAL"]
    total_duration: float
    patches_applied: int
    root_cause: str
    diagnostic_confidence: float
    recommendations: list[str]
    error_progression: list[str]


class ExecutionInsightsService:
    """Analyze execution history and provide actionable insights."""

    def __init__(self, history_service: HistoryService | None = None) -> None:
        self._history = history_service or HistoryService()

    def analyze_report(self, report: FinalVerificationReport) -> ExecutionInsight:
        """Generate insights from a final verification report."""
        execution_id = (
            report.execution.executed_command or report.repository.repository_id
        )
        history = report.execution_history or []

        successful_attempt = self._find_successful_attempt(history)
        final_status = self._determine_status(report, successful_attempt)
        total_duration = self._calculate_total_duration(history)
        patches_applied = len([h for h in history if h.applied_files])
        root_cause = (
            report.troubleshooting.root_cause if report.troubleshooting else "Unknown"
        )
        diagnostic_confidence = ConfidenceEngine.diagnostic_confidence(
            report.troubleshooting.diagnostic_confidence
            if report.troubleshooting
            else 0.0
        )
        error_progression = self._extract_error_progression(history)
        recommendations = self._generate_recommendations(
            report, final_status, error_progression
        )

        return ExecutionInsight(
            execution_id=execution_id,
            total_attempts=len(history),
            successful_attempt=successful_attempt,
            final_status=final_status,
            total_duration=total_duration,
            patches_applied=patches_applied,
            root_cause=root_cause,
            diagnostic_confidence=diagnostic_confidence,
            recommendations=recommendations,
            error_progression=error_progression,
        )

    @staticmethod
    def _find_successful_attempt(history: list[ExecutionHistoryEntry]) -> int | None:
        """Find which attempt number succeeded (if any)."""
        for entry in history:
            if entry.execution_status == "SUCCESS":
                return entry.attempt_number
        return None

    @staticmethod
    def _determine_status(
        report: FinalVerificationReport, successful_attempt: int | None
    ) -> Literal["SUCCESS", "FAILED", "PARTIAL"]:
        """Determine overall status of execution."""
        if successful_attempt is not None:
            return "SUCCESS"
        if report.execution.success:
            return "PARTIAL"
        return "FAILED"

    @staticmethod
    def _calculate_total_duration(history: list[ExecutionHistoryEntry]) -> float:
        """Calculate total execution time across all attempts."""
        return sum(entry.duration for entry in history)

    @staticmethod
    def _extract_error_progression(history: list[ExecutionHistoryEntry]) -> list[str]:
        """Extract list of errors from each attempt for progression analysis."""
        progression = []
        for entry in history:
            if entry.execution and entry.execution.stderr:
                first_line = entry.execution.stderr.split("\n")[0]
                if first_line:
                    progression.append(
                        f"Attempt {entry.attempt_number}: {first_line[:80]}"
                    )
        return progression

    @staticmethod
    def _generate_recommendations(
        report: FinalVerificationReport,
        final_status: Literal["SUCCESS", "FAILED", "PARTIAL"],
        error_progression: list[str],
    ) -> list[str]:
        """Generate actionable recommendations based on execution outcome."""
        recommendations: list[str] = []

        if final_status == "SUCCESS":
            recommendations.append("✓ Execution succeeded after patch application.")
            if report.execution_history and len(report.execution_history) > 1:
                recommendations.append(
                    f"Note: Required {len(report.execution_history)} attempts to resolve."
                )
        elif final_status == "PARTIAL":
            recommendations.append(
                "⚠ Execution completed but verification metrics were not met."
            )
            recommendations.append(
                "Consider running verification analysis for detailed insights."
            )
        else:
            recommendations.append("✗ Execution failed after all retry attempts.")

            # Add specific recommendations based on root cause
            if report.troubleshooting:
                root_cause = report.troubleshooting.root_cause.lower()

                if "syntax" in root_cause:
                    recommendations.append(
                        "Manual code review required for syntax errors."
                    )
                elif "import" in root_cause or "module" in root_cause:
                    recommendations.append(
                        "Review and update project dependencies in requirements.txt."
                    )
                elif "file" in root_cause or "dataset" in root_cause:
                    recommendations.append(
                        "Verify that all required data files are present in the repository."
                    )
                elif "permission" in root_cause:
                    recommendations.append(
                        "Check file and directory permissions in the sandbox."
                    )
                elif "database" in root_cause or "connection" in root_cause:
                    recommendations.append(
                        "Verify database connection string and service availability."
                    )
                elif "timeout" in root_cause:
                    recommendations.append(
                        "Increase execution timeout or optimize code for performance."
                    )
                elif "memory" in root_cause:
                    recommendations.append("Reduce data size or optimize memory usage.")

                # Add diagnostic-confidence-based recommendations
                if report.troubleshooting.diagnostic_confidence < 0.6:
                    recommendations.append(
                        "Low diagnostic confidence; consider manual investigation of logs."
                    )

        # Add patch-related recommendations
        if report.applied_patch:
            recommendations.append(
                f"Patch applied to {report.applied_patch.file_name}; "
                f"patch_confidence {report.applied_patch.patch_confidence:.0%}, "
                f"risk {report.applied_patch.risk_level}."
            )

        return recommendations

    def get_summary(self, execution_id: str) -> dict:
        """Get a summary of execution history for a given ID."""
        history = self._history.list(execution_id)

        if not history:
            return {
                "execution_id": execution_id,
                "message": "No execution history found",
                "attempts": 0,
            }

        successful = next((h for h in history if h.execution_status == "SUCCESS"), None)
        total_duration = sum(h.duration for h in history)

        return {
            "execution_id": execution_id,
            "total_attempts": len(history),
            "successful_attempt": successful.attempt_number if successful else None,
            "total_duration": total_duration,
            "patches_applied": len([h for h in history if h.applied_files]),
            "attempt_details": [
                {
                    "attempt": h.attempt_number,
                    "status": h.execution_status,
                    "duration": h.duration,
                    "files_modified": h.applied_files,
                    "reason": h.reason,
                }
                for h in history
            ],
        }


def create_insights_service() -> ExecutionInsightsService:
    """Factory to create configured insights service."""
    return ExecutionInsightsService()
