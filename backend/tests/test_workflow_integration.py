"""Complete service workflow integration test."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.api.routes import run_verification_workflow
from app.models.execution_result import ExecutionResult
from app.models.expected_result import ExpectedResult
from app.services.sandbox_execution_engine import SandboxExecutionEngine


class NonExecutingSandbox(SandboxExecutionEngine):
    """Test boundary that returns captured output without starting a process."""

    def execute(self, repository_path: Path, plan):  # type: ignore[no-untyped-def]
        return ExecutionResult(
            success=True,
            exit_code=0,
            stdout="accuracy=94.18\n",
            stderr="",
            execution_time=0.01,
            timed_out=False,
        )


class WorkflowIntegrationTest(unittest.TestCase):
    def test_connects_all_existing_modules_into_one_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "sample"
            (repository / "app").mkdir(parents=True)
            (repository / "README.md").write_text("# sample\n")
            (repository / "requirements.txt").write_text("")
            (repository / "app" / "main.py").write_text(
                "from fastapi import FastAPI\napp = FastAPI()\n"
            )

            report = run_verification_workflow(
                repository,
                ExpectedResult(
                    expected_value=94.2,
                    metric_name="accuracy",
                    tolerance=0.5,
                ),
                sandbox=NonExecutingSandbox(),
            )

        self.assertEqual(report["goal"], "Verify repository")
        self.assertEqual(report["observation"]["project"]["framework"], "fastapi")
        self.assertEqual(report["plan"]["execution_type"], "FastAPI")
        self.assertTrue(report["execution"]["success"])
        self.assertEqual(report["error_analysis"]["category"], "None")
        self.assertEqual(report["repair_plan"]["repair_type"], "NO_ACTION_REQUIRED")
        self.assertTrue(report["verification"]["reproduced"])

    def test_non_python_repository_skips_execution_and_generates_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "next-app"
            (repository / "app").mkdir(parents=True)
            (repository / "package.json").write_text(
                '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}'
            )
            (repository / "next.config.js").write_text("module.exports = {};\n")

            report = run_verification_workflow(
                repository,
                ExpectedResult(expected_value=0, metric_name="accuracy"),
            )

        self.assertEqual(report["observation"]["project"]["project_type"], "Next.js")
        self.assertEqual(report["execution"]["status"], "SKIPPED")
        self.assertEqual(
            report["execution"]["stdout"], "Execution skipped (non-Python project)"
        )
        self.assertEqual(report["final_report"]["verdict"], "EXECUTION_SKIPPED")


if __name__ == "__main__":
    unittest.main()
