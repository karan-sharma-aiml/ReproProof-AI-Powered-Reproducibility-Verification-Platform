from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.devops.ports import RedisCache
from app.observability.metrics.service import observability_metrics

from .models import CacheStatistics


@dataclass
class _Entry:
    value: Any
    expires_at: float | None
    size: int


class MemoryCache:
    def __init__(self, max_entries: int = 10_000) -> None:
        self.max_entries = max_entries
        self._entries: dict[str, _Entry] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    async def get(self, key: str) -> Any | None:
        entry = self._entries.get(key)
        if (
            entry is None
            or entry.expires_at is not None
            and entry.expires_at <= time.monotonic()
        ):
            if entry is not None:
                self._entries.pop(key, None)
            self._misses += 1
            observability_metrics.increment("cache_misses_total")
            return None
        self._hits += 1
        observability_metrics.increment("cache_hits_total")
        return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        if len(self._entries) >= self.max_entries and key not in self._entries:
            self._entries.pop(next(iter(self._entries)))
            self._evictions += 1
        self._entries[key] = _Entry(
            value,
            time.monotonic() + ttl_seconds if ttl_seconds else None,
            len(repr(value)),
        )

    async def delete(self, key: str) -> None:
        self._entries.pop(key, None)

    async def clear(self) -> None:
        self._entries.clear()

    def statistics(self) -> CacheStatistics:
        total = self._hits + self._misses
        return CacheStatistics(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            entries=len(self._entries),
            bytes_used=sum(entry.size for entry in self._entries.values()),
            hit_ratio=self._hits / total if total else 0,
        )


class HybridCache:
    def __init__(
        self, memory: MemoryCache | None = None, distributed: RedisCache | None = None
    ) -> None:
        self.memory = memory or MemoryCache()
        self.distributed = distributed

    async def get(self, key: str) -> Any | None:
        value = await self.memory.get(key)
        if value is not None:
            return value
        if self.distributed is None:
            return None
        value = await self.distributed.get(key)
        if value is not None:
            await self.memory.set(key, value)
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        await self.memory.set(key, value, ttl_seconds)
        if self.distributed is not None:
            await self.distributed.set(key, value, ttl_seconds=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self.memory.delete(key)
        if self.distributed is not None:
            await self.distributed.delete(key)

    async def clear(self) -> None:
        await self.memory.clear()

    def statistics(self) -> CacheStatistics:
        return self.memory.statistics()


class CacheManager:
    def __init__(self, cache: HybridCache | None = None) -> None:
        self.cache = cache or HybridCache()

    @staticmethod
    def key(namespace: str, *parts: object, version: str = "v1") -> str:
        normalized = ":".join(str(part).strip().lower() for part in parts)
        return f"reproproof:{namespace}:{version}:{normalized}"

    async def get_or_set(
        self, key: str, factory: Callable[[], Awaitable[Any]], ttl_seconds: int = 300
    ) -> Any:
        value = await self.cache.get(key)
        if value is not None:
            return value
        value = await factory()
        await self.cache.set(key, value, ttl_seconds)
        return value

    async def invalidate(self, *keys: str) -> None:
        await asyncio.gather(*(self.cache.delete(key) for key in keys))

    async def warm(self, values: dict[str, Any], ttl_seconds: int = 300) -> None:
        for key, value in values.items():
            await self.cache.set(key, value, ttl_seconds)


cache_manager = CacheManager()
