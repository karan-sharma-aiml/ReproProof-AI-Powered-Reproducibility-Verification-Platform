"""Smoke tests for ObservationOrchestrator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.observation_orchestrator import ObservationOrchestrator


class ObservationOrchestratorSmokeTest(unittest.TestCase):
    """Verify that observation services are composed into one report."""

    def test_generates_ready_report_for_structured_fastapi_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "sample-project"
            (repository / "app").mkdir(parents=True)
            (repository / "README.md").write_text("# Sample project\n")
            (repository / "requirements.txt").write_text("fastapi==0.115.0\n")
            (repository / "app" / "main.py").write_text(
                "from fastapi import FastAPI\napp = FastAPI()\n"
            )

            report = ObservationOrchestrator().observe(repository)

        self.assertEqual(report.project.framework, "fastapi")
        self.assertEqual(report.health_score, 100)
        self.assertTrue(report.execution_ready)
        self.assertEqual(report.warnings, [])
        self.assertIn("ready for deeper verification", report.recommendations[0])

    def test_reports_missing_observation_prerequisites(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "analysis.py").write_text("print('not executed')\n")

            report = ObservationOrchestrator().observe(repository)

        self.assertEqual(report.health_score, 40)
        self.assertFalse(report.execution_ready)
        self.assertIn("README.md is missing", report.warnings)
        self.assertIn("requirements.txt is missing", report.warnings)


if __name__ == "__main__":
    unittest.main()
