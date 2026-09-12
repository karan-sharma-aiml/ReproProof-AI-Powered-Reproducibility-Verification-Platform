"""Troubleshooting agent facade with a deterministic local implementation."""

from __future__ import annotations

from app.services.troubleshooter.analyzer import RootCauseAnalyzer
from app.services.confidence_engine import ConfidenceEngine
from app.services.troubleshooter.models import ParsedExecution, TroubleshootingReport
from app.services.troubleshooter.prompts import build_troubleshooting_prompt


class TroubleshootingAgent:
    """Produce structured diagnoses while leaving repository files untouched."""

    def __init__(self, analyzer: RootCauseAnalyzer | None = None) -> None:
        self._analyzer = analyzer or RootCauseAnalyzer()

    def diagnose(self, evidence: ParsedExecution) -> TroubleshootingReport:
        findings = self._analyzer.analyze(evidence)
        if not findings:
            return TroubleshootingReport(
                execution_id=evidence.execution_id,
                root_cause="No execution failure detected.",
                diagnostic_confidence=ConfidenceEngine.diagnostic_confidence(1.0),
                severity="Info",
                explanation="The captured execution completed without stderr or traceback evidence.",
                possible_fixes=[],
                requires_manual_action=False,
                execution_log=evidence.execution_log,
            )
        primary = findings[0]
        categories = ", ".join(finding.category for finding in findings)
        explanation = (
            f"Detected {categories}. The diagnosis is based on captured execution evidence "
            "and static repository context; no project files were modified."
        )
        return TroubleshootingReport(
            execution_id=evidence.execution_id,
            root_cause=primary.category,
            diagnostic_confidence=ConfidenceEngine.diagnostic_confidence(
                primary.finding_confidence
            ),
            severity=primary.severity,
            explanation=explanation,
            possible_fixes=self._analyzer.fixes(findings),
            requires_manual_action=True,
            detected_error="; ".join(categories),
            execution_log=evidence.execution_log,
            findings=findings,
        )

    @staticmethod
    def prompt(evidence: ParsedExecution) -> str:
        """Expose the provider-neutral prompt for a future model adapter."""
        return build_troubleshooting_prompt(evidence.model_dump())
