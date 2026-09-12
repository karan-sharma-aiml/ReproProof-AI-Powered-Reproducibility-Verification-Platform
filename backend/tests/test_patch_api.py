"""API coverage for preview-only patch generation."""

from __future__ import annotations

import shutil
import asyncio
import unittest
import uuid
from pathlib import Path

from app.api import routes
from app.models.execution_result import ExecutionResult
from app.models.final_verification_report import FinalVerificationReport
from app.models.repository import RepositoryMetadata
from app.models.repository_ai_analysis import RepositoryAIAnalysis
from app.models.repair_plan import RepairPlan
from app.models.verification_report import VerificationReport
from app.services.troubleshooter.models import TroubleshootingReport
from app.services.patch_generator.models import GeneratePatchRequest
from app.services.self_healing.models import ApplyFixRequest, RollbackRequest


class PatchApiTest(unittest.TestCase):
    def test_generate_patch_returns_preview_and_updates_report(self) -> None:
        execution_id = f"patch-api-{uuid.uuid4().hex[:8]}"
        repository = Path("uploads") / execution_id / "repository"
        repository.mkdir(parents=True)
        (repository / "main.py").write_text(
            "import pandas as pd\ndf = df.append(row)\n", encoding="utf-8"
        )
        report = FinalVerificationReport(
            repository=RepositoryMetadata(
                repository_name="patch-api",
                repository_id=execution_id,
                repository_path=f"{execution_id}/repository",
                total_files=1,
                total_folders=0,
                python_files=1,
                notebooks=0,
                tree=["main.py"],
                health_score=80,
            ),
            static_analysis=RepositoryAIAnalysis(
                repository_id=execution_id,
                repository_name="patch-api",
                execution_probability=80,
                reproducibility_score=80,
                risk_score=20,
                summary="test",
            ),
            execution=ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="pandas append is deprecated",
                execution_time=0.1,
                timed_out=False,
            ),
            verification=VerificationReport(
                expected_value=1,
                actual_value=None,
                metric_name="accuracy",
                absolute_difference=None,
                relative_difference=None,
                tolerance=0,
                reproduced=False,
                verification_confidence=0,
                verdict="UNAVAILABLE",
                explanation="missing",
            ),
            verdict="EXECUTION_FAILED",
            final_ai_confidence=50,
            overall_score=40,
            explanation="failed",
            timestamp="2026-01-01T00:00:00Z",
            system_information="test",
            troubleshooting=TroubleshootingReport(
                execution_id=execution_id,
                root_cause="Deprecated API",
                diagnostic_confidence=0.9,
                severity="Medium",
                explanation="The pandas API is deprecated.",
                possible_fixes=["Use pandas.concat"],
                requires_manual_action=True,
                detected_error="pandas append",
            ),
        )
        routes._FINAL_REPORTS[execution_id] = report
        try:
            result = asyncio.run(
                routes.generate_patch(GeneratePatchRequest(execution_id=execution_id))
            )
            self.assertIn("--- a/main.py", result.git_unified_diff)
            self.assertEqual(
                routes._FINAL_REPORTS[execution_id].generated_patch.patch_id,
                result.patch_id,
            )
            applied = asyncio.run(
                routes.apply_fix(
                    ApplyFixRequest(execution_id=execution_id, patch_id=result.patch_id)
                )
            )
            self.assertEqual(applied.status, "APPLIED")
            self.assertIn(
                "pd.concat", (repository / "main.py").read_text(encoding="utf-8")
            )
            rolled_back = asyncio.run(
                routes.rollback(RollbackRequest(execution_id=execution_id))
            )
            self.assertEqual(rolled_back.status, "ROLLED_BACK")
            self.assertIn(
                "append", (repository / "main.py").read_text(encoding="utf-8")
            )
        finally:
            routes._FINAL_REPORTS.pop(execution_id, None)
            shutil.rmtree(Path("uploads") / execution_id, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
