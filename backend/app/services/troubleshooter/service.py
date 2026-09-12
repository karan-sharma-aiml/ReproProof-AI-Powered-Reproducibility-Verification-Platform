"""Application service for execution troubleshooting."""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.models.execution_result import ExecutionResult
from app.services.troubleshooter.ai_agent import TroubleshootingAgent
from app.services.troubleshooter.models import TroubleshootingReport
from app.services.troubleshooter.parser import ExecutionEvidenceParser

logger = get_logger("troubleshooter")


class TroubleshootingService:
    """Parse evidence and produce a non-mutating troubleshooting report."""

    def __init__(
        self,
        parser: ExecutionEvidenceParser | None = None,
        agent: TroubleshootingAgent | None = None,
    ) -> None:
        self._parser = parser or ExecutionEvidenceParser()
        self._agent = agent or TroubleshootingAgent()

    def troubleshoot(
        self,
        execution_id: str,
        execution: ExecutionResult,
        repository_path: Path,
        repository_tree: list[str],
    ) -> TroubleshootingReport:
        evidence = self._parser.parse(
            execution_id, execution, repository_path, repository_tree
        )
        report = self._agent.diagnose(evidence)
        logger.info(
            "Troubleshooting session complete: execution_id=%s root_cause=%s diagnostic_confidence=%.2f severity=%s",
            execution_id,
            report.root_cause,
            report.diagnostic_confidence,
            report.severity,
        )
        return report
