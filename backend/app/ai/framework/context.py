from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass
class AgentContext:
    """Shared workflow state; agents exchange data only through this object."""

    repository_info: dict[str, Any] = field(default_factory=dict)
    execution_results: dict[str, Any] = field(default_factory=dict)
    logs: list[Any] = field(default_factory=list)
    repository_metadata: dict[str, Any] = field(default_factory=dict)
    security_findings: list[Any] = field(default_factory=list)
    risk_findings: list[Any] = field(default_factory=list)
    dataset_information: dict[str, Any] = field(default_factory=dict)
    research_paper_findings: dict[str, Any] = field(default_factory=dict)
    patch_suggestions: list[Any] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    intermediate_results: dict[str, Any] = field(default_factory=dict)
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    shared_memory: dict[str, Any] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock, repr=False, compare=False)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return getattr(self, key, self.shared_memory.get(key, default))

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if hasattr(self, key) and key != "_lock":
                setattr(self, key, value)
            else:
                self.shared_memory[key] = value

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self.set(key, value)
