"""Tests for phase-one archive extraction and repository analysis."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from app.services.repository_analysis_service import RepositoryAnalysisService


class RepositoryAnalysisServiceTest(unittest.TestCase):
    def test_extracts_and_analyzes_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            archive = root / "sample.zip"
            with ZipFile(archive, "w") as zip_file:
                zip_file.writestr("README.md", "# sample")
                zip_file.writestr("requirements.txt", "fastapi==0.115.0")
                zip_file.writestr("app/main.py", "from fastapi import FastAPI\n")
                zip_file.writestr("data.csv", "x\n1\n")
                zip_file.writestr("results.json", "{}")

            result = RepositoryAnalysisService().extract_and_analyze(archive, "demo")

            self.assertEqual(result.repository_path, "demo/repository")
            self.assertEqual(result.total_files, 5)
            self.assertEqual(result.total_folders, 1)
            self.assertEqual(result.datasets, ["data.csv", "results.json"])
            self.assertEqual(result.detected_frameworks, ["FastAPI"])
            self.assertEqual(result.health_score, 100)
            self.assertIn("app/main.py", result.tree)

    def test_rejects_archive_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            archive = root / "unsafe.zip"
            with ZipFile(archive, "w") as zip_file:
                zip_file.writestr("../outside.txt", "unsafe")

            with self.assertRaises(ValueError):
                RepositoryAnalysisService().extract_repository(archive, "unsafe")


if __name__ == "__main__":
    unittest.main()
