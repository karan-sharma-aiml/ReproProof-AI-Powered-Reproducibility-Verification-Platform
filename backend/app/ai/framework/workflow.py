from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkflowStep:
    agent_name: str
    depends_on: tuple[str, ...] = ()
    retries: int = 0
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class Workflow:
    name: str
    steps: tuple[WorkflowStep, ...] = field(default_factory=tuple)
    parallel: bool = False


class WorkflowEngine:
    """Validates configurable dependency graphs and returns executable order."""

    def order(self, workflow: Workflow) -> tuple[WorkflowStep, ...]:
        steps = {step.agent_name.strip().lower(): step for step in workflow.steps}
        if len(steps) != len(workflow.steps):
            raise ValueError("Workflow contains duplicate agent names")
        for step in steps.values():
            if step.retries < 0:
                raise ValueError(f"Retries cannot be negative: {step.agent_name}")
            if step.timeout_seconds is not None and step.timeout_seconds <= 0:
                raise ValueError(f"Timeout must be positive: {step.agent_name}")
            missing = set(dependency.lower() for dependency in step.depends_on) - set(
                steps
            )
            if missing:
                raise ValueError(f"Unknown workflow dependencies: {sorted(missing)}")

        ordered: list[WorkflowStep] = []
        remaining = dict(steps)
        while remaining:
            ready = [
                step
                for step in remaining.values()
                if all(
                    dependency.lower() in {item.agent_name.lower() for item in ordered}
                    for dependency in step.depends_on
                )
            ]
            if not ready:
                raise ValueError("Workflow contains a dependency cycle")
            ready.sort(key=lambda step: step.agent_name.lower())
            ordered.extend(ready)
            for step in ready:
                remaining.pop(step.agent_name.lower())
        return tuple(ordered)

    def batches(self, workflow: Workflow) -> tuple[tuple[WorkflowStep, ...], ...]:
        ordered = self.order(workflow)
        completed: set[str] = set()
        remaining = {step.agent_name.lower(): step for step in ordered}
        batches: list[tuple[WorkflowStep, ...]] = []
        while remaining:
            ready = tuple(
                step
                for step in remaining.values()
                if all(
                    dependency.lower() in completed for dependency in step.depends_on
                )
            )
            if not ready:
                raise ValueError("Workflow contains a dependency cycle")
            batches.append(ready)
            completed.update(step.agent_name.lower() for step in ready)
            for step in ready:
                remaining.pop(step.agent_name.lower())
        return tuple(batches)
