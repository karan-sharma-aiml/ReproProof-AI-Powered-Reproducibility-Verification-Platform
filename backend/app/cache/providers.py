"""Cache provider ports and implementations."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = Any  # type: ignore[misc,assignment]


class CacheProvider(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None: ...

    @abstractmethod
    async def set(
        self, key: str, value: Any, ttl_seconds: int | None = None
    ) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def health(self) -> bool: ...


class InMemoryCache(CacheProvider):
    def __init__(self) -> None:
        self._values: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        item = self._values.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at is not None and expires_at <= time.monotonic():
            self._values.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds else None
        self._values[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._values.pop(key, None)

    async def health(self) -> bool:
        return True


class RedisCache(CacheProvider):
    def __init__(self, url: str, fallback: InMemoryCache | None = None) -> None:
        self.url = url
        self.fallback = fallback or InMemoryCache()
        self.client = (
            Redis.from_url(url, decode_responses=False)
            if hasattr(Redis, "from_url")
            else None
        )

    async def get(self, key: str) -> Any | None:
        try:
            value = await self.client.get(key)
            return value if value is not None else await self.fallback.get(key)
        except Exception:
            return await self.fallback.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        try:
            await self.client.set(key, value, ex=ttl_seconds)
        except Exception:
            await self.fallback.set(key, value, ttl_seconds)

    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception:
            pass
        await self.fallback.delete(key)

    async def health(self) -> bool:
        try:
            return bool(await self.client.ping())
        except Exception:
            return False
