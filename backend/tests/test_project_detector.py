"""Smoke tests for ProjectDetector."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.project_detector import ProjectDetector


class ProjectDetectorSmokeTest(unittest.TestCase):
    """Verify dependency and import signals are detected without execution."""

    def test_detects_fastapi_project_from_dependency_and_import(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "requirements.txt").write_text("fastapi==0.115.0\n")
            (repository / "app.py").write_text(
                "from fastapi import FastAPI\napp = FastAPI()\n"
            )

            result = ProjectDetector().detect_project(repository)

        self.assertEqual(result.project_type, "Web API")
        self.assertEqual(result.framework, "fastapi")
        self.assertGreaterEqual(result.confidence, 70)
        self.assertIn("declared", result.reason)

    def test_detects_notebook_project_from_notebook_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "analysis.ipynb").write_text("{}")

            result = ProjectDetector().detect_project(repository)

        self.assertEqual(result.project_type, "Notebook Project")
        self.assertEqual(result.framework, "Jupyter Notebook")


if __name__ == "__main__":
    unittest.main()
