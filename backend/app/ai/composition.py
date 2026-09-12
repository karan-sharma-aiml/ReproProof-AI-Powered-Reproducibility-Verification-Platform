from __future__ import annotations

from .agents import PRODUCTION_AGENTS
from .framework import (
    AgentFactory,
    AgentOrchestrator,
    AgentRegistry,
    Workflow,
    WorkflowStep,
)


def create_production_orchestrator() -> AgentOrchestrator:
    """Build the production agent graph without coupling it to FastAPI startup."""
    registry = AgentRegistry()
    for agent_type in PRODUCTION_AGENTS:
        registry.register(agent_type.metadata.name, agent_type)
    return AgentOrchestrator(AgentFactory(registry))


def default_reproducibility_workflow(*, parallel: bool = False) -> Workflow:
    """Return the canonical ordered workflow; callers may supply another graph."""
    return Workflow(
        name="reproducibility-evaluation",
        parallel=parallel,
        steps=(
            WorkflowStep("repository"),
            WorkflowStep("research_paper", depends_on=("repository",)),
            WorkflowStep("dataset", depends_on=("research_paper",)),
            WorkflowStep("execution", depends_on=("dataset",)),
            WorkflowStep("security", depends_on=("execution",)),
            WorkflowStep("repair", depends_on=("security",)),
            WorkflowStep("reviewer", depends_on=("repair",)),
            WorkflowStep("judge", depends_on=("reviewer",)),
        ),
    )
