from __future__ import annotations

from .workflow import Workflow, WorkflowEngine, WorkflowStep


class AgentScheduler:
    """Determines execution order while leaving execution policy to the orchestrator."""

    def __init__(self, workflow_engine: WorkflowEngine | None = None) -> None:
        self.workflow_engine = workflow_engine or WorkflowEngine()

    def schedule(self, workflow: Workflow) -> tuple[WorkflowStep, ...]:
        return self.workflow_engine.order(workflow)

    def schedule_batches(
        self, workflow: Workflow
    ) -> tuple[tuple[WorkflowStep, ...], ...]:
        return self.workflow_engine.batches(workflow)
