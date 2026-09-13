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
        self.assertGreaterEqual(result.detection_confidence, 70)
        self.assertIn("declared", result.reason)

    def test_detects_notebook_project_from_notebook_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "analysis.ipynb").write_text("{}")

            result = ProjectDetector().detect_project(repository)

        self.assertEqual(result.project_type, "Notebook Project")
        self.assertEqual(result.framework, "Jupyter Notebook")

    def test_detects_nextjs_project_without_python_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "package.json").write_text(
                '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}'
            )
            (repository / "next.config.ts").write_text("export default {};\n")
            (repository / "app").mkdir()

            result = ProjectDetector().detect_project(repository)

        self.assertEqual(result.project_type, "Next.js")
        self.assertFalse(result.is_python_project)

    def test_detects_react_vite_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "package.json").write_text(
                '{"dependencies":{"react":"19.0.0","vite":"6.0.0"}}'
            )
            (repository / "vite.config.ts").write_text("export default {};\n")

            result = ProjectDetector().detect_project(repository)

        self.assertEqual(result.project_type, "React/Vite Project")
        self.assertFalse(result.is_python_project)

    def test_detects_next_frontend_and_nested_fastapi_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            (repository / "frontend" / "app").mkdir(parents=True)
            (repository / "frontend" / "package.json").write_text(
                '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}'
            )
            (repository / "backend" / "app").mkdir(parents=True)
            (repository / "backend" / "requirements.txt").write_text(
                "fastapi==0.115.0\n"
            )
            (repository / "backend" / "app" / "main.py").write_text(
                "from fastapi import FastAPI\napp = FastAPI()\n"
            )

            result = ProjectDetector().detect_project(repository)

        self.assertEqual(result.project_type, "Monorepo")
        self.assertEqual(result.frontend, "Next.js")
        self.assertEqual(result.backend, "fastapi (Python)")
        self.assertEqual(result.execution_target, "backend")
        self.assertTrue(result.is_python_project)


if __name__ == "__main__":
    unittest.main()
