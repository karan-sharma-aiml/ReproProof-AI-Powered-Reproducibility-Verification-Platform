from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ReportStore(ABC):
    """Persistence abstraction for reports and final verification output."""

    @abstractmethod
    def save(self, report_id: str, payload: Any) -> str: ...

    @abstractmethod
    def get(self, report_id: str) -> Any: ...

    @abstractmethod
    def list(self) -> list[str]: ...
