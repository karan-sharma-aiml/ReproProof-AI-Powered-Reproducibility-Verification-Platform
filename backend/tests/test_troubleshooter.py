"""Tests for non-mutating troubleshooting diagnosis."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.models.execution_result import ExecutionResult
from app.services.troubleshooter.service import TroubleshootingService


class TroubleshooterTest(unittest.TestCase):
    def test_detects_required_root_cause_categories(self) -> None:
        cases = (
            ("ImportError: cannot import name x", "ImportError"),
            ("FileNotFoundError: data.csv", "FileNotFoundError"),
            ("RuntimeError: worker stopped", "RuntimeError"),
            ("SyntaxError: invalid syntax", "SyntaxError"),
            ("dependency version conflict", "Package Version Conflict"),
            ("PermissionError: permission denied", "PermissionError"),
            ("missing dataset: train.parquet", "Dataset Missing"),
            (
                "KeyError: 'API_TOKEN' environment variable",
                "Missing Environment Variables",
            ),
        )
        for stderr, expected_root_cause in cases:
            with self.subTest(stderr=stderr):
                report = TroubleshootingService().troubleshoot(
                    "execution-category",
                    ExecutionResult(
                        success=False,
                        exit_code=1,
                        stdout="",
                        stderr=stderr,
                        execution_time=0.1,
                        timed_out=False,
                    ),
                    Path(tempfile.gettempdir()),
                    [],
                )
                self.assertEqual(report.root_cause, expected_root_cause)

    def test_detects_missing_dependency_from_execution_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            result = ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="ModuleNotFoundError: No module named 'pandas'",
                execution_time=0.4,
                timed_out=False,
            )
            report = TroubleshootingService().troubleshoot(
                "execution-1", result, repository, ["main.py", "requirements.txt"]
            )

        self.assertEqual(report.root_cause, "ModuleNotFoundError")
        self.assertEqual(report.severity, "High")
        self.assertGreaterEqual(report.diagnostic_confidence, 0.9)
        self.assertTrue(report.requires_manual_action)
        self.assertTrue(
            any("missing package" in fix.lower() for fix in report.possible_fixes)
        )

    def test_successful_execution_returns_info_without_fixes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = TroubleshootingService().troubleshoot(
                "execution-2",
                ExecutionResult(
                    success=True,
                    exit_code=0,
                    stdout="accuracy=94.2",
                    stderr="",
                    execution_time=0.1,
                    timed_out=False,
                ),
                Path(temporary_directory),
                [],
            )

        self.assertEqual(report.severity, "Info")
        self.assertFalse(report.requires_manual_action)
        self.assertEqual(report.possible_fixes, [])


if __name__ == "__main__":
    unittest.main()
