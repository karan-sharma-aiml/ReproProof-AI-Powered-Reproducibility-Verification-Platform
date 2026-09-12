"""Smoke tests for ErrorAnalyzer."""

from __future__ import annotations

import unittest

from app.models.execution_result import ExecutionResult
from app.services.error_analyzer import ErrorAnalyzer


def failed_result(stderr: str, *, timed_out: bool = False) -> ExecutionResult:
    return ExecutionResult(
        success=False,
        exit_code=-1,
        stdout="",
        stderr=stderr,
        execution_time=0.1,
        timed_out=timed_out,
    )


class ErrorAnalyzerSmokeTest(unittest.TestCase):
    def test_classifies_required_error_categories(self) -> None:
        cases = {
            "ModuleNotFoundError: No module named 'pandas'": "ModuleNotFoundError",
            "ImportError: cannot import name 'app'": "ImportError",
            "FileNotFoundError: [Errno 2]": "FileNotFoundError",
            "SyntaxError: invalid syntax": "SyntaxError",
            "PermissionError: access denied": "PermissionError",
            "MemoryError": "MemoryError",
            "RuntimeError: worker failed": "RuntimeError",
            "AssertionError: expected 1": "AssertionError",
            "OSError: input/output error": "OSError",
        }
        analyzer = ErrorAnalyzer()

        for stderr, expected_category in cases.items():
            with self.subTest(expected_category=expected_category):
                analysis = analyzer.analyze(failed_result(stderr))
                self.assertEqual(analysis.category, expected_category)
                self.assertGreaterEqual(analysis.classification_confidence, 90)
                self.assertTrue(analysis.evidence)

    def test_classifies_timeout_from_result_state(self) -> None:
        analysis = ErrorAnalyzer().analyze(
            failed_result("Command timed out", timed_out=True)
        )

        self.assertEqual(analysis.category, "TimeoutExpired")
        self.assertEqual(analysis.severity, "high")
        self.assertTrue(analysis.repairable)
        self.assertIn("ExecutionResult.timed_out=True", analysis.evidence)

    def test_classifies_success_without_suggesting_repair(self) -> None:
        result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="done",
            stderr="",
            execution_time=0.2,
            timed_out=False,
        )

        analysis = ErrorAnalyzer().analyze(result)

        self.assertEqual(analysis.category, "None")
        self.assertEqual(analysis.severity, "none")
        self.assertFalse(analysis.repairable)
        self.assertEqual(analysis.suggested_repair_type, "None")


if __name__ == "__main__":
    unittest.main()
