from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol


class RedisCache(ABC):
    """Provider-neutral cache port for Redis or another distributed cache."""

    @abstractmethod
    async def get(self, key: str) -> Any | None: ...

    @abstractmethod
    async def set(
        self, key: str, value: Any, *, ttl_seconds: int | None = None
    ) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class TraceProvider(ABC):
    @abstractmethod
    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> Any: ...


class ErrorMonitor(ABC):
    @abstractmethod
    def capture(
        self, error: BaseException, context: dict[str, Any] | None = None
    ) -> None: ...


class BackgroundTaskQueue(Protocol):
    async def enqueue(self, task_name: str, payload: dict[str, Any]) -> str: ...
