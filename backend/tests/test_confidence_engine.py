"""Regression tests for evidence-based repository confidence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.confidence_engine import ConfidenceEngine
from app.services.repository_inspector import RepositoryInspector


class ConfidenceEngineTest(unittest.TestCase):
    def test_unknown_runtime_evidence_is_excluded_from_average(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("# Project\n## Usage\n")
            (root / "requirements.txt").write_text("fastapi==0.115.0\n")
            repository = RepositoryInspector().inspect_repository(root)

            score, factors = ConfidenceEngine.repository_quality_confidence(
                repository,
                execution_success=False,
                verification_confidence=None,
                static_analysis=None,
                execution=None,
            )

        self.assertGreater(score, 0)
        self.assertFalse(any("Execution success" in factor for factor in factors))
        self.assertFalse(any("Verification confidence" in factor for factor in factors))

    def test_quality_score_changes_with_repository_signals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sparse = RepositoryInspector().inspect_repository(root)
            sparse_score, _ = ConfidenceEngine.repository_quality_confidence(
                sparse, execution_success=False, verification_confidence=0
            )
            (root / "README.md").write_text("# Project\n## Usage\n")
            (root / "requirements.txt").write_text("fastapi==0.115.0\n")
            (root / "Dockerfile").write_text("FROM python:3.12\n")
            (root / "main.py").write_text("print('ok')\n")
            (root / "tests").mkdir()
            (root / "tests" / "test_main.py").write_text("def test_ok(): pass\n")
            rich = RepositoryInspector().inspect_repository(root)
            rich_score, factors = ConfidenceEngine.repository_quality_confidence(
                rich, execution_success=True, verification_confidence=100
            )

        self.assertLess(sparse_score, rich_score)
        self.assertNotEqual(sparse_score, 75)
        self.assertTrue(any("Tests detected" in factor for factor in factors))


if __name__ == "__main__":
    unittest.main()
