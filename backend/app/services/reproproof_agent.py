"""Coordinate the ReproProof observation workflow without execution."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.logging import get_logger
from app.models.agent_result import AgentResult
from app.models.execution_plan import ExecutionPlan
from app.models.observation_report import ObservationReport
from app.services.execution_planner import ExecutionPlanner
from app.services.observation_orchestrator import ObservationOrchestrator

logger = get_logger("reproproof_agent")


class ObservationCoordinator(Protocol):
    """Minimal observation dependency required by the agent."""

    def observe(self, repo_path: Path) -> ObservationReport:
        """Return a repository observation report."""


class PlanGenerator(Protocol):
    """Minimal planning dependency required by the agent."""

    def create_plan(self, report: ObservationReport) -> ExecutionPlan:
        """Return a deterministic execution plan."""


class ReproProofAgent:
    """Coordinate observation and planning, never execution."""

    GOAL = "Verify repository"

    def __init__(
        self,
        observation_orchestrator: ObservationCoordinator | None = None,
        execution_planner: PlanGenerator | None = None,
    ) -> None:
        """Create an agent with injectable observation and planning services."""
        self._observation_orchestrator = (
            observation_orchestrator or ObservationOrchestrator()
        )
        self._execution_planner = execution_planner or ExecutionPlanner()

    def run(self, repo_path: Path) -> AgentResult:
        """Observe a repository and decide whether it may proceed to execution."""
        repository_path = Path(repo_path)
        logger.info("Agent workflow started for repository: %s", repository_path)

        observation = self._observation_orchestrator.observe(repository_path)
        plan = self._execution_planner.create_plan(observation)
        blocking_reasons = self._blocking_reasons(observation)
        is_ready = observation.execution_ready and not blocking_reasons

        if is_ready:
            result = AgentResult(
                goal=self.GOAL,
                observation=observation,
                plan=plan,
                status="READY",
                next_action="EXECUTE",
                explanation=(
                    "Repository observation passed readiness checks. "
                    "The execution plan is ready for the future execution engine."
                ),
            )
        else:
            result = AgentResult(
                goal=self.GOAL,
                observation=observation,
                plan=plan,
                status="BLOCKED",
                next_action="STOP",
                explanation=self._blocked_explanation(blocking_reasons),
                blocking_reasons=blocking_reasons,
            )

        logger.info(
            "Agent workflow complete for %s: status=%s next_action=%s",
            repository_path,
            result.status,
            result.next_action,
        )
        return result

    @staticmethod
    def _blocking_reasons(observation: ObservationReport) -> list[str]:
        """Convert readiness facts into stable reasons suitable for consumers."""
        reasons = list(observation.warnings)
        if not observation.execution_ready and not reasons:
            reasons.append("Observation report is not execution-ready")
        return list(dict.fromkeys(reason for reason in reasons if reason))

    @staticmethod
    def _blocked_explanation(reasons: list[str]) -> str:
        if not reasons:
            return "Workflow stopped because the repository is not execution-ready."
        return (
            "Workflow stopped because the repository is not execution-ready: "
            + "; ".join(reasons)
        )
