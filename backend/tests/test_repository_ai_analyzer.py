"""Smoke tests for static repository AI analysis."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.repository_ai_analyzer import RepositoryAIAnalyzer
from app.services.repository_analysis_service import RepositoryAnalysisService


class RepositoryAIAnalyzerTest(unittest.TestCase):
    def _analyze(self, files: dict[str, str]):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            metadata = RepositoryAnalysisService().analyze_repository(root, "demo")
            return RepositoryAIAnalyzer().analyze(root, metadata)

    def test_detects_frameworks_and_source_directories(self) -> None:
        report = self._analyze(
            {
                "requirements.txt": "fastapi\ntorch\nxgboost\n",
                "main.py": "from fastapi import FastAPI\nimport torch\nimport xgboost\n",
                "backend/service.py": "import streamlit\n",
                "pyproject.toml": "[project]\nrequires-python = '>=3.11'\n",
            }
        )
        self.assertFalse(
            any(issue.issue_type == "FRAMEWORK_UNDETECTED" for issue in report.issues)
        )
        self.assertIn("MISSING_README", {issue.issue_type for issue in report.issues})

    def test_detects_missing_dependency_and_dataset_loader(self) -> None:
        report = self._analyze(
            {
                "README.md": "# Demo\n## Installation\n## Usage\n## Dataset\n## License\n",
                "requirements.txt": "pandas\n",
                "main.py": "import pandas as pd\nimport torch\ndf = pd.read_csv('data/missing.csv')\n",
            }
        )
        types = {issue.issue_type for issue in report.issues}
        self.assertIn("MISSING_DATASET", types)
        self.assertIn("MISSING_DEPENDENCY", types)

    def test_detects_seed_and_hardcoded_network_path(self) -> None:
        report = self._analyze(
            {
                "README.md": "# Demo\n## Installation\n## Usage\n## Dataset\n## License\n",
                "requirements.txt": "numpy\n",
                "main.py": "import numpy as np\npath = r'\\\\server\\share\\data.csv'\n",
            }
        )
        types = {issue.issue_type for issue in report.issues}
        self.assertIn("HARDCODED_PATH", types)
        self.assertIn("RANDOM_SEED_MISSING", types)

    def test_detects_notebook_quality_and_issue_evidence(self) -> None:
        report = self._analyze(
            {
                "requirements.txt": "jupyter\n",
                "analysis.ipynb": '{"cells": [{"cell_type": "code", "source": ["print(1)"], "outputs": []}]}',
            }
        )
        notebook_issues = [
            issue for issue in report.issues if issue.issue_type.startswith("NOTEBOOK_")
        ]
        self.assertTrue(notebook_issues)
        self.assertTrue(
            all(issue.evidence and issue.affected_file for issue in notebook_issues)
        )

    def test_detects_reproducibility_issues_and_scores_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("# demo")
            (root / "requirements.txt").write_text("requests\n")
            (root / "main.py").write_text(
                "import pandas\n"
                "from pathlib import Path\n"
                "data = Path('/home/user/data.csv')\n"
                "print(data)\n"
            )
            metadata = RepositoryAnalysisService().analyze_repository(root, "demo")
            report = RepositoryAIAnalyzer().analyze(root, metadata)

        issue_types = {issue.issue_type for issue in report.issues}
        self.assertIn("MISSING_DEPENDENCY", issue_types)
        self.assertIn("HARDCODED_PATH", issue_types)
        self.assertIn("RANDOM_SEED_MISSING", issue_types)
        self.assertGreaterEqual(report.risk_score, 1)
        self.assertLess(report.execution_probability, 100)

    def test_detects_invalid_dataset_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("# demo")
            (root / "requirements.txt").write_text("")
            (root / "main.py").write_text("print('data.csv')\n")
            metadata = RepositoryAnalysisService().analyze_repository(root, "demo")
            report = RepositoryAIAnalyzer().analyze(root, metadata)

        self.assertIn(
            "INVALID_DATASET_PATH", {issue.issue_type for issue in report.issues}
        )


if __name__ == "__main__":
    unittest.main()
