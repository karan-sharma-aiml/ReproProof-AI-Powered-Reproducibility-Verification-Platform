"""Rerun a repository through the existing observation and sandbox pipeline."""

from __future__ import annotations

from pathlib import Path

from app.services.reproproof_agent import ReproProofAgent
from app.services.sandbox_execution_engine import SandboxExecutionEngine
from app.models.execution_result import ExecutionResult


class RerunService:
    """Reuse existing planning and sandbox controls for patched reruns."""

    def __init__(
        self,
        agent: ReproProofAgent | None = None,
        engine: SandboxExecutionEngine | None = None,
    ) -> None:
        self._agent = agent or ReproProofAgent()
        self._engine = engine or SandboxExecutionEngine()

    def rerun(self, repository: Path) -> ExecutionResult:
        agent_result = self._agent.run(repository)
        if not agent_result.observation.execution_ready:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=agent_result.explanation,
                execution_time=0.0,
                timed_out=False,
                status="BLOCKED",
            )
        return self._engine.execute(repository, agent_result.plan)
