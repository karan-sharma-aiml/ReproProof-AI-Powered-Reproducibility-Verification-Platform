from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class RepositoryStore(ABC):
    """Repository storage abstraction for uploaded project artifacts."""

    @abstractmethod
    def save(self, repository_id: str, repository_path: Path) -> str: ...

    @abstractmethod
    def get(self, repository_id: str) -> Any: ...

    @abstractmethod
    def list(self) -> list[str]: ...
