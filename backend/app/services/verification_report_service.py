"""Compose final deterministic verdicts and downloadable reports."""

from __future__ import annotations

import html
import platform
from datetime import datetime, timezone

from app.models.execution_result import ExecutionResult
from app.models.final_verification_report import FinalVerificationReport
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.models.repair_plan import RepairPlan
from app.models.verification_report import VerificationReport
from app.services.troubleshooter.models import TroubleshootingReport
from app.services.confidence_engine import ConfidenceEngine


class VerificationReportService:
    """Combine existing observations without executing or repairing repositories."""

    def build(
        self,
        repository: RepositoryMetadata,
        static_analysis: RepositoryAIAnalysis,
        execution: ExecutionResult,
        metrics: dict[str, float],
        verification: VerificationReport,
        repair_plan: RepairPlan,
        troubleshooting: TroubleshootingReport | None = None,
    ) -> FinalVerificationReport:
        if not execution.success:
            verdict = "EXECUTION_FAILED"
        elif repository.health_score < 35 or static_analysis.risk_score >= 85:
            verdict = "INVALID_PROJECT"
        elif verification.verdict == "REPRODUCED":
            verdict = "REPRODUCED"
        elif verification.verdict == "PARTIALLY_REPRODUCED":
            verdict = "PARTIALLY_REPRODUCED"
        else:
            verdict = "NOT_REPRODUCED"

        execution_quality = 100 if execution.success else 0
        overall_score = max(
            0.0,
            min(
                100.0,
                repository.health_score * 0.25
                + execution_quality * 0.25
                + verification.overall_score * 0.35
                + (100 - static_analysis.risk_score) * 0.15,
            ),
        )
        final_ai_confidence = ConfidenceEngine.final_ai_confidence(
            verification_confidence=verification.verification_confidence,
            execution_probability=static_analysis.execution_probability,
            risk_score=static_analysis.risk_score,
        )
        explanation = self._explanation(verdict, verification, execution)
        return FinalVerificationReport(
            repository=repository,
            static_analysis=static_analysis,
            execution=execution,
            metrics=metrics,
            verification=verification,
            verdict=verdict,
            final_ai_confidence=final_ai_confidence,
            overall_score=overall_score,
            explanation=explanation,
            repair_suggestions=repair_plan.manual_actions
            + repair_plan.suggested_commands,
            timestamp=datetime.now(timezone.utc).isoformat(),
            system_information=f"{platform.system()} {platform.release()} | Python {platform.python_version()}",
            markdown_report=self._markdown(
                repository,
                execution,
                metrics,
                verification,
                verdict,
                final_ai_confidence,
                repair_plan,
            ),
            troubleshooting=troubleshooting,
        )

    @staticmethod
    def _explanation(
        verdict: str, verification: VerificationReport, execution: ExecutionResult
    ) -> str:
        if verdict == "EXECUTION_FAILED":
            return "Repository execution failed, so metric reproduction could not be completed."
        if verdict == "REPRODUCED":
            return f"Repository executed successfully and all {len(verification.matched_metrics)} expected metrics matched within tolerance."
        if verdict == "PARTIALLY_REPRODUCED":
            return f"Repository executed successfully; {len(verification.matched_metrics)} metrics matched while some metrics failed or were missing."
        return "Repository execution completed, but the observed metrics did not reproduce the expected result."

    @staticmethod
    def _markdown(
        repository,
        execution,
        metrics,
        verification,
        verdict,
        final_ai_confidence,
        repair_plan,
    ) -> str:
        metric_lines = (
            "\n".join(f"| {name} | {value} |" for name, value in metrics.items())
            or "| None | N/A |"
        )
        return f"""# ReproProof Verification Report

## Repository Summary
- Name: {repository.repository_name}
- Health score: {repository.health_score}/100
- Static risk score: {100 - repository.health_score}/100

## Execution Summary
- Status: {execution.status}
- Success: {execution.success}
- Exit code: {execution.exit_code}
- Execution time: {execution.execution_time:.2f}s

## Detected Metrics
| Metric | Actual |
|---|---:|
{metric_lines}

## Comparison Table
- Matched: {', '.join(verification.matched_metrics) or 'None'}
- Failed: {', '.join(verification.failed_metrics) or 'None'}
- Missing: {', '.join(verification.missing_metrics) or 'None'}
- Similarity: {verification.overall_similarity:.1f}%

## AI Verdict
- Verdict: **{verdict}**
- Final AI Confidence: {final_ai_confidence}/100
- Explanation: {verification.explanation}

## Repair Suggestions
{chr(10).join(f'- {item}' for item in repair_plan.manual_actions + repair_plan.suggested_commands) or '- None'}

## Execution Logs
{chr(10).join(f'- {html.escape(item)}' for item in execution.logs) or '- None'}

Generated: {datetime.now(timezone.utc).isoformat()}
"""

    def pdf_bytes(self, markdown: str) -> bytes:
        """Create a minimal valid PDF without executing code or adding dependencies."""
        text = markdown.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        lines = text.splitlines()[:70]
        content = (
            "BT /F1 9 Tf 36 760 Td "
            + " ".join(f"({line[:110]}) Tj 0 -11 Td" for line in lines)
            + " ET"
        )
        objects = [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
            f"<< /Length {len(content.encode())} >>\nstream\n{content}\nendstream",
        ]
        output = b"%PDF-1.4\n"
        offsets = [0]
        for index, obj in enumerate(objects, 1):
            offsets.append(len(output))
            output += f"{index} 0 obj\n{obj}\nendobj\n".encode()
        xref = len(output)
        output += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode()
        output += b"".join(
            f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]
        )
        output += f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
        return output
