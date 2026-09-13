"""Centralized confidence scoring policies for backend services."""

from __future__ import annotations

from typing import Optional

from app.models.execution_result import ExecutionResult
from app.core.logging import get_logger

logger = get_logger("confidence_engine")


class ConfidenceEngine:
    """Calculate every confidence score from named raw signals."""

    @staticmethod
    def _bounded(value: float, maximum: float = 100.0) -> int:
        return round(max(0.0, min(maximum, value)))

    @classmethod
    def issue_confidence(cls, evidence_strength: float) -> int:
        return cls._bounded(evidence_strength)

    @classmethod
    def classification_confidence(cls, evidence_strength: float) -> int:
        return cls._bounded(evidence_strength)

    @classmethod
    def detection_confidence(cls, match_strength: float) -> int:
        return cls._bounded(match_strength)

    @classmethod
    def finding_confidence(cls, evidence_strength: float) -> float:
        return max(0.0, min(1.0, evidence_strength))

    @classmethod
    def diagnostic_confidence(cls, evidence_strength: float) -> float:
        return cls.finding_confidence(evidence_strength)

    @classmethod
    def repair_plan_confidence(cls, classification_confidence: float) -> int:
        return cls._bounded(classification_confidence)

    @classmethod
    def patch_confidence(cls, patch_quality: float) -> float:
        return max(0.0, min(1.0, patch_quality))

    @staticmethod
    def verification_confidence(
        absolute_difference: float,
        tolerance: float,
        execution: ExecutionResult,
    ) -> int:
        if not execution.success or execution.timed_out:
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

    @classmethod
    def verification_confidence_from_similarity(cls, similarity: float) -> int:
        return cls._bounded(similarity)

    @classmethod
    def final_ai_confidence(
        cls,
        verification_confidence: Optional[float],
        execution_probability: float,
        risk_score: float,
    ) -> int:
        score = (
            verification_confidence * 0.5
            + execution_probability * 0.3
            + (100 - risk_score) * 0.2
        )
        return cls._bounded(score)

    @classmethod
    def repository_quality_confidence(
        cls,
        repository,
        execution_success: bool,
        verification_confidence: float,
        static_analysis=None,
        execution=None,
    ) -> tuple[int, list[str]]:
        """Score repository quality and live verification evidence with weights."""
        tree = {str(path).lower() for path in repository.tree}
        names = {str(path).replace("\\", "/").rsplit("/", 1)[-1] for path in tree}
        signals: list[tuple[str, float, float]] = [
            ("Repository health", repository.health_score, 14)
        ]
        if execution is not None:
            signals.append(("Execution success", 100 if execution_success else 0, 25))
        if verification_confidence is not None:
            signals.append(("Verification confidence", verification_confidence, 20))
        if static_analysis is not None:
            signals.extend(
                (
                    (
                        "Static execution probability",
                        static_analysis.execution_probability,
                        10,
                    ),
                    (
                        "Reproducibility score",
                        static_analysis.reproducibility_score,
                        10,
                    ),
                    (
                        "Security score (100 - risk)",
                        100 - static_analysis.risk_score,
                        10,
                    ),
                )
            )
        if "readme.md" in names or repository.readme_quality:
            signals.append(
                ("Documentation evidence", repository.readme_quality or 100, 4)
            )
        if {"requirements.txt", "pyproject.toml", "package.json"} & names:
            signals.append(("Dependency evidence", 100, 2))
        if (
            execution is not None
            and execution_success
            and (execution.stdout or execution.logs)
        ):
            signals.append(("Runtime evidence", 100, 2))
        if repository.test_frameworks or any("test" in path for path in tree):
            signals.append(("Tests detected", 100, 3))
        total_weight = sum(weight for _, _, weight in signals)
        score = round(
            sum(value * weight for _, value, weight in signals) / total_weight
        )
        factors = [
            f"{label}: {value:.0f}/100 x {weight:g}% = {value * weight / total_weight:.1f}"
            for label, value, weight in signals
        ]
        logger.info(
            "Confidence breakdown score=%d factors=%s", score, " | ".join(factors)
        )
        return cls._bounded(score), factors
