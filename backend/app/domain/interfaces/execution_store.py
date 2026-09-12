from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ExecutionStore(ABC):
    """Execution-level persistence contract for runtime analysis and history."""

    @abstractmethod
    def save(self, execution_id: str, payload: Any) -> str: ...

    @abstractmethod
    def get(self, execution_id: str) -> Any: ...

    @abstractmethod
    def list(self) -> list[str]: ...
