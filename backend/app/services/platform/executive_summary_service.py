"""Explainable executive summaries over existing execution evidence."""

from __future__ import annotations

from app.models.final_verification_report import FinalVerificationReport
from app.services.platform.health_score_service import HealthScoreService
from app.services.platform.models import ExecutiveSummary


class ExecutiveSummaryService:
    """Create concise stakeholder summaries without changing execution behavior."""

    def __init__(self, health_service: HealthScoreService | None = None) -> None:
        self._health = health_service or HealthScoreService()

    def build(
        self, execution_id: str, report: FinalVerificationReport
    ) -> ExecutiveSummary:
        health = self._health.calculate(
            report.repository,
            report.static_analysis,
            report.execution,
            patch_success=report.final_status in {"SUCCEEDED", "REPRODUCED"},
            retry_success=report.retry_count > 0 and report.execution.success,
        )
        cause = (
            report.troubleshooting.root_cause
            if report.troubleshooting
            else "No failure diagnosis was required"
        )
        patch_sentence = (
            f" The AI generated a patch for {report.applied_patch.file_name}."
            if report.applied_patch and report.applied_patch.file_name
            else " No patch was applied."
        )
        retry_sentence = (
            f" Execution succeeded after {report.retry_count} retry attempt(s)."
            if report.retry_count
            else ""
        )
        text = (
            f"{report.repository.repository_name} finished with status {report.verdict}. "
            f"The primary finding was {cause}.{patch_sentence}{retry_sentence} "
            f"Overall reproducibility score: {health.score}/100."
        )
        return ExecutiveSummary(
            execution_id=execution_id,
            summary=text,
            status=report.final_status or report.verdict,
            final_ai_confidence=report.final_ai_confidence,
            health_score=health.score,
        )
