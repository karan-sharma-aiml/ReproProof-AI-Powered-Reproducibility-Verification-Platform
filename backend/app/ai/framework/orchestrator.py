from __future__ import annotations

import asyncio
import time
from typing import Any

from .context import AgentContext
from .contracts import AgentResult, AgentStatus
from .events import AgentEvent, EventType
from .factory import AgentFactory
from .memory import AgentMemory
from .message_bus import MessageBus
from .scheduler import AgentScheduler
from .workflow import Workflow


class AgentOrchestrator:
    """Runs agents through their lifecycle and coordinates all shared state."""

    def __init__(
        self,
        factory: AgentFactory,
        scheduler: AgentScheduler | None = None,
        message_bus: MessageBus | None = None,
    ) -> None:
        self.factory = factory
        self.scheduler = scheduler or AgentScheduler()
        self.message_bus = message_bus or MessageBus()

    async def run(
        self,
        workflow: Workflow,
        context: AgentContext | None = None,
        memory: AgentMemory | None = None,
    ) -> dict[str, AgentResult]:
        context = context or AgentContext()
        memory = memory or AgentMemory()
        results: dict[str, AgentResult] = {}
        await self._publish(EventType.WORKFLOW_STARTED, workflow.name)
        try:
            batches = (
                self.scheduler.schedule_batches(workflow)
                if workflow.parallel
                else tuple((step,) for step in self.scheduler.schedule(workflow))
            )
            for batch in batches:
                batch_results = await asyncio.gather(
                    *(self._run_with_timeout(step, context, memory) for step in batch)
                )
                for result in batch_results:
                    results[result.agent_name] = result
                    if result.status is AgentStatus.FAILED:
                        raise RuntimeError(
                            result.error or f"Agent failed: {result.agent_name}"
                        )
            await self._publish(
                EventType.WORKFLOW_COMPLETED, workflow.name, {"results": results}
            )
            return results
        except asyncio.CancelledError:
            await self._publish(
                EventType.WORKFLOW_FAILED, workflow.name, {"error": "cancelled"}
            )
            raise
        except Exception as exc:
            await self._publish(
                EventType.WORKFLOW_FAILED, workflow.name, {"error": str(exc)}
            )
            raise

    async def _run_with_timeout(
        self, step, context: AgentContext, memory: AgentMemory
    ) -> AgentResult:
        operation = self._run_step(step.agent_name, step.retries, context, memory)
        if step.timeout_seconds is None:
            return await operation
        try:
            return await asyncio.wait_for(operation, timeout=step.timeout_seconds)
        except asyncio.TimeoutError:
            await self._publish(
                EventType.AGENT_FAILED, step.agent_name, {"error": "timeout"}
            )
            return AgentResult(
                step.agent_name,
                AgentStatus.FAILED,
                error=f"Agent timed out after {step.timeout_seconds} seconds",
            )

    async def _run_step(
        self, name: str, retries: int, context: AgentContext, memory: AgentMemory
    ) -> AgentResult:
        started = time.perf_counter()
        attempts = 0
        await self._publish(EventType.AGENT_STARTED, name)
        while attempts <= retries:
            attempts += 1
            agent = self.factory.create(name)
            attach_runtime = getattr(agent, "attach_runtime", None)
            if attach_runtime is not None:
                attach_runtime(self.message_bus, memory)
            try:
                await agent.initialize(context)
                await agent.validate(context)
                await agent.plan(context)
                await agent.analyze(context)
                output = await agent.execute(context)
                confidence = await agent.evaluate(context)
                summary = await agent.summarize(context)
                if summary is not None:
                    output = summary
                metrics = {
                    "duration_seconds": time.perf_counter() - started,
                    "cpu_time_seconds": time.process_time(),
                    "attempts": float(attempts),
                }
                context.confidence_scores[name] = (
                    confidence if confidence is not None else 0.0
                )
                result = AgentResult(
                    name,
                    AgentStatus.COMPLETED,
                    output,
                    confidence=confidence,
                    metrics=metrics,
                )
                await self._publish(EventType.AGENT_COMPLETED, name, {"result": result})
                await agent.cleanup(context)
                return result
            except Exception as exc:
                try:
                    await agent.cleanup(context)
                except Exception:
                    pass
                if attempts > retries:
                    result = AgentResult(
                        name,
                        AgentStatus.FAILED,
                        error=str(exc),
                        metrics={
                            "duration_seconds": time.perf_counter() - started,
                            "attempts": float(attempts),
                        },
                    )
                    await self._publish(
                        EventType.AGENT_FAILED,
                        name,
                        {"error": str(exc), "attempts": attempts},
                    )
                    return result

        raise RuntimeError(f"Agent execution ended unexpectedly: {name}")

    async def _publish(
        self, event_type: EventType, source: str, payload: dict[str, Any] | None = None
    ) -> None:
        await self.message_bus.publish(AgentEvent(event_type, source, payload or {}))
