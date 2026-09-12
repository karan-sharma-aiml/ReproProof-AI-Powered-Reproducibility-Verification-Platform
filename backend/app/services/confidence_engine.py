"""Centralized confidence scoring policies for backend services."""

from __future__ import annotations

from app.models.execution_result import ExecutionResult


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
        verification_confidence: float,
        execution_probability: float,
        risk_score: float,
    ) -> int:
        return cls._bounded(
            verification_confidence * 0.5
            + execution_probability * 0.3
            + (100 - risk_score) * 0.2
        )
