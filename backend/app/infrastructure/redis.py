from __future__ import annotations

import socket
import time
from abc import ABC, abstractmethod
from typing import Any

from app.devops.ports import RedisCache

from .models import InfrastructureHealth, InfrastructureStatus, RedisConfig


class DistributedLock(ABC):
    @abstractmethod
    async def acquire(self, key: str, ttl_seconds: int = 30) -> bool: ...

    @abstractmethod
    async def release(self, key: str) -> None: ...


class PubSub(ABC):
    @abstractmethod
    async def publish(self, channel: str, message: dict[str, Any]) -> None: ...

    @abstractmethod
    async def subscribe(self, channel: str) -> Any: ...


class SessionStore(ABC):
    @abstractmethod
    async def save(
        self, session_id: str, value: dict[str, Any], ttl_seconds: int = 3600
    ) -> None: ...

    @abstractmethod
    async def get(self, session_id: str) -> dict[str, Any] | None: ...


class OptionalRedisClient(RedisCache, DistributedLock, PubSub, SessionStore):
    def __init__(self, config: RedisConfig) -> None:
        self.config = config
        self._values: dict[str, Any] = {}
        self._locks: set[str] = set()

    async def get(self, key: str) -> Any | None:
        return self._values.get(key)

    async def set(
        self, key: str, value: Any, *, ttl_seconds: int | None = None
    ) -> None:
        self._values[key] = value

    async def delete(self, key: str) -> None:
        self._values.pop(key, None)

    async def acquire(self, key: str, ttl_seconds: int = 30) -> bool:
        if key in self._locks:
            return False
        self._locks.add(key)
        return True

    async def release(self, key: str) -> None:
        self._locks.discard(key)

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        return None

    async def subscribe(self, channel: str) -> Any:
        return None

    async def save(
        self, session_id: str, value: dict[str, Any], ttl_seconds: int = 3600
    ) -> None:
        await self.set(f"session:{session_id}", value, ttl_seconds=ttl_seconds)

    async def health(self) -> InfrastructureHealth:
        started = time.perf_counter()
        try:
            with socket.create_connection(
                (self.config.host, self.config.port), timeout=0.25
            ):
                return InfrastructureHealth(
                    name="redis",
                    status=InfrastructureStatus.HEALTHY,
                    configured=True,
                    connected=True,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    reason="tcp endpoint reachable",
                )
        except OSError as exc:
            return InfrastructureHealth(
                name="redis",
                status=InfrastructureStatus.DEGRADED,
                configured=True,
                connected=False,
                latency_ms=(time.perf_counter() - started) * 1000,
                reason=f"redis unavailable: {exc}",
            )
