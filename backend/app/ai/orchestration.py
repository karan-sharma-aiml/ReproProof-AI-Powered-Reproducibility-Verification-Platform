from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from .composition import (
    create_production_orchestrator,
    default_reproducibility_workflow,
)
from .framework import AgentContext, AgentMemory, Workflow, WorkflowStep
from .framework.contracts import AgentResult, AgentStatus
from .framework.events import AgentEvent, EventType
from app.knowledge_graph import (
    EntityType,
    GraphEntity,
    GraphRelationship,
    RelationshipType,
    knowledge_graph,
)


class ManagedWorkflowStatus:
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowRecord:
    workflow_id: str
    template: str
    status: str = ManagedWorkflowStatus.QUEUED
    repository_id: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    current_agent: str | None = None
    results: dict[str, AgentResult] = field(default_factory=dict)
    context: AgentContext = field(default_factory=AgentContext)
    memory: AgentMemory = field(default_factory=AgentMemory)
    events: list[AgentEvent] = field(default_factory=list)
    error: str | None = None
    approval_required: str | None = None
    pause_gate: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    task: asyncio.Task[None] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.pause_gate.set()


class WorkflowTemplates:
    @staticmethod
    def get(name: str, *, parallel: bool = True) -> Workflow:
        normalized = name.strip().lower()
        all_agents = (
            "repository",
            "research_paper",
            "dataset",
            "execution",
            "security",
            "repair",
            "reviewer",
            "judge",
        )
        templates = {
            "enterprise": all_agents,
            "research": ("repository", "research_paper", "dataset", "judge"),
            "judge": (
                "repository",
                "research_paper",
                "dataset",
                "execution",
                "reviewer",
                "judge",
            ),
            "security": ("repository", "security", "repair", "reviewer"),
            "repository": ("repository",),
            "publication": (
                "repository",
                "research_paper",
                "dataset",
                "reviewer",
                "judge",
            ),
        }
        if normalized not in templates:
            raise ValueError(f"Unknown workflow template: {name}")
        selected = templates[normalized]
        previous: str | None = None
        steps: list[WorkflowStep] = []
        for agent in selected:
            steps.append(
                WorkflowStep(
                    agent,
                    depends_on=(previous,) if previous else (),
                    retries=1,
                    timeout_seconds=120,
                )
            )
            previous = agent
        return Workflow(
            name=f"{normalized}-workflow", steps=tuple(steps), parallel=parallel
        )

    @classmethod
    def names(cls) -> tuple[str, ...]:
        return (
            "research",
            "judge",
            "security",
            "repository",
            "publication",
            "enterprise",
        )


class EnterpriseOrchestrator:
    """Managed lifecycle facade over the existing agent orchestrator and registry."""

    def __init__(self) -> None:
        self._records: dict[str, WorkflowRecord] = {}
        self._lock = asyncio.Lock()
        self._custom_agents: dict[str, Any] = {}

    async def register_agent(self, name: str, factory: Any) -> None:
        async with self._lock:
            normalized = name.strip().lower()
            if not normalized:
                raise ValueError("Agent name cannot be empty")
            self._custom_agents[normalized] = factory

    async def start(
        self,
        template: str,
        context: AgentContext | None = None,
        repository_id: str | None = None,
        parallel: bool = True,
    ) -> WorkflowRecord:
        workflow_id = f"wf-{uuid4().hex[:12]}"
        record = WorkflowRecord(
            workflow_id,
            template,
            repository_id=repository_id,
            context=context or AgentContext(),
        )
        async with self._lock:
            self._records[workflow_id] = record
        record.task = asyncio.create_task(
            self._execute(record, WorkflowTemplates.get(template, parallel=parallel))
        )
        return record

    async def _execute(self, record: WorkflowRecord, workflow: Workflow) -> None:
        record.status = ManagedWorkflowStatus.RUNNING
        record.started_at = datetime.now(timezone.utc).isoformat()
        workflow_entity = knowledge_graph.upsert_entity(
            GraphEntity(
                id=f"workflow:{record.workflow_id}",
                type=EntityType.WORKFLOW,
                label=workflow.name,
                properties={
                    "template": record.template,
                    "repository_id": record.repository_id,
                },
            )
        )
        orchestrator = create_production_orchestrator()
        for event in orchestrator.message_bus.history:
            record.events.append(event)
        try:
            await self._publish(record, EventType.WORKFLOW_STARTED, workflow.name)
            batches = (
                orchestrator.scheduler.schedule_batches(workflow)
                if workflow.parallel
                else tuple(
                    (step,) for step in orchestrator.scheduler.schedule(workflow)
                )
            )
            for batch in batches:
                await record.pause_gate.wait()
                if record.status == ManagedWorkflowStatus.CANCELLED:
                    raise asyncio.CancelledError
                record.status = ManagedWorkflowStatus.RUNNING
                for step in batch:
                    record.current_agent = step.agent_name
                    agent_id = f"agent:{step.agent_name}"
                    knowledge_graph.upsert_entity(
                        GraphEntity(
                            id=agent_id, type=EntityType.AGENT, label=step.agent_name
                        )
                    )
                    knowledge_graph.relate(
                        GraphRelationship(
                            source=workflow_entity.id,
                            target=agent_id,
                            type=RelationshipType.EXECUTES,
                        )
                    )
                results = await asyncio.gather(
                    *(
                        orchestrator._run_with_timeout(
                            step, record.context, record.memory
                        )
                        for step in batch
                    )
                )
                for result in results:
                    record.results[result.agent_name] = result
                    if result.status is AgentStatus.FAILED:
                        raise RuntimeError(
                            result.error or f"Agent failed: {result.agent_name}"
                        )
            record.status = ManagedWorkflowStatus.COMPLETED
            await self._publish(
                record,
                EventType.WORKFLOW_COMPLETED,
                workflow.name,
                {"results": record.results},
            )
        except asyncio.CancelledError:
            record.status = ManagedWorkflowStatus.CANCELLED
            await self._publish(
                record, EventType.WORKFLOW_FAILED, workflow.name, {"error": "cancelled"}
            )
        except Exception as exc:
            record.status = ManagedWorkflowStatus.FAILED
            record.error = str(exc)
            await self._publish(
                record, EventType.WORKFLOW_FAILED, workflow.name, {"error": str(exc)}
            )
        finally:
            record.current_agent = None
            record.ended_at = datetime.now(timezone.utc).isoformat()

    async def _publish(
        self,
        record: WorkflowRecord,
        event_type: EventType,
        source: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event = AgentEvent(event_type, source, payload or {})
        record.events.append(event)

    async def pause(self, workflow_id: str) -> WorkflowRecord:
        record = self.get(workflow_id)
        if record.status in {
            ManagedWorkflowStatus.COMPLETED,
            ManagedWorkflowStatus.FAILED,
            ManagedWorkflowStatus.CANCELLED,
        }:
            return record
        record.pause_gate.clear()
        record.status = ManagedWorkflowStatus.PAUSED
        await self._publish(
            record, EventType.WORKFLOW_STARTED, workflow_id, {"action": "paused"}
        )
        return record

    async def resume(self, workflow_id: str) -> WorkflowRecord:
        record = self.get(workflow_id)
        if record.status != ManagedWorkflowStatus.PAUSED:
            return record
        record.pause_gate.set()
        if record.task and not record.task.done():
            record.status = ManagedWorkflowStatus.RUNNING
        await self._publish(
            record, EventType.WORKFLOW_STARTED, workflow_id, {"action": "resumed"}
        )
        return record

    async def cancel(self, workflow_id: str) -> WorkflowRecord:
        record = self.get(workflow_id)
        record.status = ManagedWorkflowStatus.CANCELLED
        if record.task and not record.task.done():
            record.task.cancel()
        return record

    def get(self, workflow_id: str) -> WorkflowRecord:
        try:
            return self._records[workflow_id]
        except KeyError as exc:
            raise ValueError(f"Workflow not found: {workflow_id}") from exc

    def records(self) -> list[WorkflowRecord]:
        return list(reversed(list(self._records.values())))

    def agents(self) -> list[str]:
        return list(create_production_orchestrator().factory.registry.names()) + sorted(
            self._custom_agents
        )

    def history(self, workflow_id: str) -> list[AgentEvent]:
        return self.get(workflow_id).events

    def status_payload(self, record: WorkflowRecord) -> dict[str, Any]:
        return {
            "workflow_id": record.workflow_id,
            "template": record.template,
            "status": record.status,
            "repository_id": record.repository_id,
            "started_at": record.started_at,
            "ended_at": record.ended_at,
            "current_agent": record.current_agent,
            "error": record.error,
            "approval_required": record.approval_required,
            "results": {
                name: jsonable_encoder(result)
                for name, result in record.results.items()
            },
            "context_keys": sorted(record.context.shared_memory),
            "memory_keys": sorted(record.memory.snapshot()),
            "event_count": len(record.events),
        }

    def graph(self, template: str) -> dict[str, Any]:
        workflow = WorkflowTemplates.get(template)
        nodes = [
            {"id": step.agent_name, "label": step.agent_name, "status": "pending"}
            for step in workflow.steps
        ]
        edges = [
            {"source": dependency, "target": step.agent_name}
            for step in workflow.steps
            for dependency in step.depends_on
        ]
        return {"workflow": workflow.name, "nodes": nodes, "edges": edges}


enterprise_orchestrator = EnterpriseOrchestrator()
