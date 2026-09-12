"""Tests for final verdict and report generation."""

from __future__ import annotations

import unittest

from app.models.execution_result import ExecutionResult
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.models.repair_plan import RepairPlan
from app.models.verification_report import VerificationReport
from app.services.verification_report_service import VerificationReportService


class VerificationReportServiceTest(unittest.TestCase):
    def test_builds_reproduced_verdict_and_pdf(self) -> None:
        repository = RepositoryMetadata(
            repository_name="demo",
            total_files=1,
            total_folders=0,
            python_files=1,
            notebooks=0,
            important_files=["README.md", "requirements.txt", "main.py"],
            source_directories=[],
            detected_languages=["Python"],
            repository_id="demo",
            health_score=90,
        )
        static = RepositoryAIAnalysis(
            repository_id="demo",
            repository_name="demo",
            issues=[],
            execution_probability=95,
            reproducibility_score=95,
            risk_score=5,
            summary="clean",
        )
        execution = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="accuracy=94.2",
            stderr="",
            execution_time=1,
            timed_out=False,
        )
        verification = VerificationReport(
            expected_value=94.2,
            actual_value=94.2,
            metric_name="accuracy",
            absolute_difference=0,
            relative_difference=0,
            tolerance=0.5,
            reproduced=True,
            verification_confidence=100,
            verdict="REPRODUCED",
            explanation="matched",
            matched_metrics={"accuracy": 94.2},
            overall_similarity=100,
            overall_score=100,
        )
        repair = RepairPlan(
            repair_type="NO_ACTION_REQUIRED",
            description="none",
            repair_plan_confidence=100,
            safe_to_apply=True,
            requires_human_review=False,
        )
        report = VerificationReportService().build(
            repository, static, execution, {"accuracy": 94.2}, verification, repair
        )
        pdf = VerificationReportService().pdf_bytes(report.markdown_report)

        self.assertEqual(report.verdict, "REPRODUCED")
        self.assertGreater(report.final_ai_confidence, 0)
        self.assertTrue(pdf.startswith(b"%PDF-1.4"))
        self.assertIn("ReproProof Verification Report", report.markdown_report)


if __name__ == "__main__":
    unittest.main()
