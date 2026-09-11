"""Tests for real metric extraction and multi-metric verification."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.models.execution_result import ExecutionResult
from app.services.metric_extraction_service import MetricExtractionService
from app.services.verification_engine import VerificationEngine


class MetricExtractionTest(unittest.TestCase):
    def test_extracts_stdout_json_and_csv_metrics(self) -> None:
        result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout='accuracy=94.2\n{"loss": 0.21}\nmetric,score\nprecision,92.1\n',
            stderr="",
            execution_time=0.1,
            timed_out=False,
        )

        metrics = MetricExtractionService().extract(result)

        self.assertEqual(metrics["accuracy"], 94.2)
        self.assertEqual(metrics["loss"], 0.21)
        self.assertEqual(metrics["precision"], 92.1)

    def test_extracts_csv_metrics_from_all_rows_and_ignores_malformed_values(
        self,
    ) -> None:
        result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="some noisy prefix\nmetric,score\naccuracy,94.2\nprecision,92.1\nnoise,not-a-number,extra\n",
            stderr="",
            execution_time=0.1,
            timed_out=False,
        )

        metrics = MetricExtractionService().extract(result)

        self.assertEqual(metrics["accuracy"], 94.2)
        self.assertEqual(metrics["precision"], 92.1)

    def test_extracts_persisted_log_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "execution.log"
            log_path.write_text("recall=91.0\n")
            result = ExecutionResult(
                success=True,
                exit_code=0,
                stdout="",
                stderr="",
                execution_time=0.1,
                timed_out=False,
                log_path=str(log_path),
            )
            metrics = MetricExtractionService().extract(result)

        self.assertEqual(metrics, {"recall": 91.0})

    def test_verifies_multiple_metrics_and_missing_values(self) -> None:
        report = VerificationEngine().verify_metrics(
            {"accuracy": 94.2, "loss": 0.3, "recall": 91.0},
            {"accuracy": 94.0, "loss": 0.32},
            absolute_tolerance=0.5,
        )

        self.assertEqual(set(report.matched_metrics), {"accuracy", "loss"})
        self.assertEqual(report.missing_metrics, ["recall"])
        self.assertEqual(report.verdict, "PARTIALLY_REPRODUCED")


if __name__ == "__main__":
    unittest.main()
