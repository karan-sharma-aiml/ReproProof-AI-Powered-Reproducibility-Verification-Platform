"""Smoke tests for VerificationEngine."""

from __future__ import annotations

import unittest

from app.models.expected_result import ExpectedResult
from app.models.execution_result import ExecutionResult
from app.services.verification_engine import VerificationEngine


def execution(
    stdout: str, *, success: bool = True, timed_out: bool = False
) -> ExecutionResult:
    return ExecutionResult(
        success=success,
        exit_code=0 if success else 1,
        stdout=stdout,
        stderr="",
        execution_time=0.1,
        timed_out=timed_out,
    )


class VerificationEngineSmokeTest(unittest.TestCase):
    def test_reproduces_accuracy_within_configured_tolerance(self) -> None:
        report = VerificationEngine().verify(
            ExpectedResult(expected_value=94.2, metric_name="accuracy", tolerance=0.5),
            execution("accuracy=94.18"),
        )

        self.assertTrue(report.reproduced)
        self.assertEqual(report.verdict, "REPRODUCED")
        self.assertEqual(report.actual_value, 94.18)
        self.assertAlmostEqual(report.absolute_difference, 0.02, places=2)

    def test_rejects_loss_outside_tolerance(self) -> None:
        report = VerificationEngine().verify(
            ExpectedResult(expected_value=0.30, metric_name="loss", tolerance=0.05),
            execution("loss: 0.95"),
        )

        self.assertFalse(report.reproduced)
        self.assertEqual(report.verdict, "NOT_REPRODUCED")
        self.assertGreater(report.absolute_difference or 0, report.tolerance)

    def test_supports_custom_numeric_and_zero_expected_value(self) -> None:
        report = VerificationEngine().verify(
            ExpectedResult(expected_value=0, metric_name="custom_numeric", tolerance=0),
            execution("observed output\n0"),
        )

        self.assertTrue(report.reproduced)
        self.assertEqual(report.relative_difference, 0)

    def test_returns_unavailable_when_execution_failed_or_metric_missing(self) -> None:
        engine = VerificationEngine()
        failed = engine.verify(
            ExpectedResult(expected_value=1, metric_name="mse", tolerance=0.1),
            execution("ModuleNotFoundError", success=False),
        )
        missing = engine.verify(
            ExpectedResult(expected_value=1, metric_name="mse", tolerance=0.1),
            execution("completed without metrics"),
        )

        self.assertEqual(failed.verdict, "UNAVAILABLE")
        self.assertEqual(missing.verdict, "UNAVAILABLE")
        self.assertIsNone(missing.actual_value)

    def test_supports_per_call_tolerance_override_without_mutation(self) -> None:
        expected = ExpectedResult(expected_value=10, metric_name="mae", tolerance=0.1)
        report = VerificationEngine().verify(
            expected, execution("mae=10.4"), tolerance=0.5
        )

        self.assertTrue(report.reproduced)
        self.assertEqual(expected.tolerance, 0.1)


if __name__ == "__main__":
    unittest.main()
