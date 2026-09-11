"""Compare expected metrics with captured execution output."""

from __future__ import annotations

import math
import re
from typing import Pattern

from app.core.logging import get_logger
from app.models.expected_result import ExpectedResult
from app.models.execution_result import ExecutionResult
from app.models.verification_report import VerificationReport

logger = get_logger("verification_engine")


class VerificationEngine:
    """Verify numeric research outcomes without rerunning or mutating results."""

    _NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"

    def verify(
        self,
        expected: ExpectedResult,
        execution_result: ExecutionResult,
        tolerance: float | None = None,
    ) -> VerificationReport:
        """Compare an expected metric with a numeric value in execution output."""
        comparison_tolerance = (
            expected.tolerance
            if tolerance is None
            else self._validate_tolerance(tolerance)
        )
        actual_value = self._extract_actual_value(
            expected.metric_name, execution_result
        )

        if actual_value is None:
            report = VerificationReport(
                expected_value=expected.expected_value,
                actual_value=None,
                metric_name=expected.metric_name,
                absolute_difference=None,
                relative_difference=None,
                tolerance=comparison_tolerance,
                reproduced=False,
                confidence=0,
                verdict="UNAVAILABLE",
                explanation=(
                    "The execution result does not contain a verifiable numeric "
                    f"value for metric '{expected.metric_name}'."
                ),
                missing_metrics=[expected.metric_name],
            )
            logger.warning("Metric value unavailable: %s", expected.metric_name)
            return report

        absolute_difference = abs(actual_value - expected.expected_value)
        relative_difference = self._relative_difference(
            absolute_difference, expected.expected_value
        )
        reproduced = absolute_difference <= comparison_tolerance
        verdict = "REPRODUCED" if reproduced else "NOT_REPRODUCED"
        confidence = self._confidence(
            absolute_difference, comparison_tolerance, execution_result
        )
        report = VerificationReport(
            expected_value=expected.expected_value,
            actual_value=actual_value,
            metric_name=expected.metric_name,
            absolute_difference=absolute_difference,
            relative_difference=relative_difference,
            tolerance=comparison_tolerance,
            reproduced=reproduced,
            confidence=confidence,
            verdict=verdict,
            explanation=self._explanation(
                expected, actual_value, absolute_difference, comparison_tolerance
            ),
            matched_metrics={expected.metric_name: actual_value} if reproduced else {},
            failed_metrics={} if reproduced else {expected.metric_name: actual_value},
            overall_similarity=(
                100.0 if reproduced else max(0.0, 100.0 - relative_difference * 100.0)
            ),
            overall_score=float(confidence),
        )
        logger.info(
            "Verification complete: metric=%s expected=%s actual=%s verdict=%s",
            report.metric_name,
            report.expected_value,
            report.actual_value,
            report.verdict,
        )
        return report

    def verify_metrics(
        self,
        expected_metrics: dict[str, float],
        actual_metrics: dict[str, float],
        absolute_tolerance: float = 0.0,
        percentage_tolerance: float | None = None,
        tolerances: dict[str, float] | None = None,
    ) -> VerificationReport:
        """Compare multiple extracted metrics without executing anything."""
        if absolute_tolerance < 0 or (
            percentage_tolerance is not None and percentage_tolerance < 0
        ):
            raise ValueError("tolerances must be non-negative")
        matched: dict[str, float] = {}
        failed: dict[str, float] = {}
        missing: list[str] = []
        differences: dict[str, float] = {}
        for name, expected in expected_metrics.items():
            if name not in actual_metrics:
                missing.append(name)
                continue
            actual = actual_metrics[name]
            difference = abs(actual - expected)
            tolerance = (tolerances or {}).get(name, absolute_tolerance)
            if percentage_tolerance is not None:
                tolerance = max(tolerance, abs(expected) * percentage_tolerance / 100)
            differences[name] = difference
            (matched if difference <= tolerance else failed)[name] = actual
        total = len(expected_metrics)
        similarity = 100.0 if not total else (len(matched) / total) * 100
        if failed:
            similarity *= len(matched) / max(1, len(matched) + len(failed))
        if not matched and missing and not failed:
            verdict = "UNAVAILABLE"
        elif len(matched) == total:
            verdict = "REPRODUCED"
        elif matched:
            verdict = "PARTIALLY_REPRODUCED"
        else:
            verdict = "NOT_REPRODUCED"
        expected_value = next(iter(expected_metrics.values()), 0.0)
        actual_value = next(iter(actual_metrics.values()), None)
        return VerificationReport(
            expected_value=expected_value,
            actual_value=actual_value,
            metric_name="multiple",
            absolute_difference=next(iter(differences.values()), None),
            relative_difference=None,
            tolerance=absolute_tolerance,
            reproduced=verdict == "REPRODUCED",
            confidence=round(similarity),
            verdict=verdict,
            explanation=f"Matched {len(matched)} of {total} expected metrics; missing {len(missing)}.",
            matched_metrics=matched,
            failed_metrics=failed,
            missing_metrics=missing,
            overall_similarity=similarity,
            overall_score=similarity,
        )

    def _extract_actual_value(
        self, metric_name: str, execution_result: ExecutionResult
    ) -> float | None:
        if not execution_result.success or execution_result.timed_out:
            return None
        output = "\n".join(
            part for part in (execution_result.stdout, execution_result.stderr) if part
        )
        metric_pattern = re.compile(
            rf"(?im)(?:^|[{{,\s])['\"]?{re.escape(metric_name)}['\"]?"
            rf"\s*(?:=|:)\s*({self._NUMBER})(?:\b|\s|[,}}])"
        )
        matches = metric_pattern.findall(output)
        if matches:
            return float(matches[-1])
        if metric_name == "custom_numeric":
            plain_numbers = re.findall(rf"(?<![\w.])({self._NUMBER})(?![\w.])", output)
            if plain_numbers:
                return float(plain_numbers[-1])
        return None

    @staticmethod
    def _relative_difference(absolute_difference: float, expected: float) -> float:
        if expected == 0:
            return 0.0 if absolute_difference == 0 else math.inf
        return absolute_difference / abs(expected)

    @staticmethod
    def _confidence(
        absolute_difference: float,
        tolerance: float,
        execution_result: ExecutionResult,
    ) -> int:
        if not execution_result.success or execution_result.timed_out:
            return 0
        if absolute_difference <= tolerance:
            return (
                100
                if tolerance == 0
                else max(80, round(100 - (absolute_difference / tolerance) * 20))
            )
        return max(
            1, round(100 - min(99, (absolute_difference / max(tolerance, 1e-12)) * 10))
        )

    @staticmethod
    def _explanation(
        expected: ExpectedResult,
        actual_value: float,
        absolute_difference: float,
        tolerance: float,
    ) -> str:
        if absolute_difference <= tolerance:
            return (
                f"{expected.metric_name} reproduced: expected {expected.expected_value}, "
                f"observed {actual_value}, difference {absolute_difference} is within "
                f"tolerance {tolerance}."
            )
        return (
            f"{expected.metric_name} did not reproduce: expected {expected.expected_value}, "
            f"observed {actual_value}, difference {absolute_difference} exceeds "
            f"tolerance {tolerance}."
        )

    @staticmethod
    def _validate_tolerance(tolerance: float) -> float:
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be a finite non-negative number")
        return tolerance
