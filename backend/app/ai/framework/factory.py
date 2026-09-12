from __future__ import annotations

from .contracts import Agent
from .registry import AgentRegistry


class AgentFactory:
    """Creates fresh agent instances from registry entries for each workflow run."""

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    def create(self, name: str) -> Agent:
        agent = self.registry.resolve(name)()
        if not isinstance(agent, Agent):
            raise TypeError(f"Registered factory for '{name}' did not create an Agent")
        return agent
