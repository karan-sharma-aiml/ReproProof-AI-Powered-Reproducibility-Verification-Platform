"""Named cache namespaces used by application services."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings

from .providers import CacheProvider, InMemoryCache, RedisCache


class CacheManager:
    def __init__(self, provider: CacheProvider | None = None) -> None:
        settings = get_settings()
        self.fallback = InMemoryCache()
        self.provider = provider or (
            RedisCache(settings.redis_url, self.fallback)
            if settings.REDIS_URL or settings.REDIS_ENABLED
            else self.fallback
        )

    async def get(self, namespace: str, key: str) -> Any | None:
        return await self.provider.get(f"{namespace}:{key}")

    async def set(
        self, namespace: str, key: str, value: Any, ttl_seconds: int | None = None
    ) -> None:
        await self.provider.set(f"{namespace}:{key}", value, ttl_seconds)

    async def delete(self, namespace: str, key: str) -> None:
        await self.provider.delete(f"{namespace}:{key}")

    async def health(self) -> dict[str, object]:
        healthy = await self.provider.health()
        return {
            "status": "healthy" if healthy else "degraded",
            "provider": type(self.provider).__name__,
            "fallback": self.fallback is not self.provider,
        }

    async def result(
        self, key: str, value: Any = None, ttl_seconds: int | None = None
    ) -> Any | None:
        return await self._get_or_set("result", key, value, ttl_seconds)

    async def session(
        self, key: str, value: Any = None, ttl_seconds: int | None = 3600
    ) -> Any | None:
        return await self._get_or_set("session", key, value, ttl_seconds)

    async def ai_response(
        self, key: str, value: Any = None, ttl_seconds: int | None = 3600
    ) -> Any | None:
        return await self._get_or_set("ai", key, value, ttl_seconds)

    async def rate_limit(
        self, key: str, value: Any = None, ttl_seconds: int | None = 60
    ) -> Any | None:
        return await self._get_or_set("rate-limit", key, value, ttl_seconds)

    async def job(
        self, key: str, value: Any = None, ttl_seconds: int | None = 3600
    ) -> Any | None:
        return await self._get_or_set("job", key, value, ttl_seconds)

    async def memory(
        self, key: str, value: Any = None, ttl_seconds: int | None = 3600
    ) -> Any | None:
        return await self._get_or_set("memory", key, value, ttl_seconds)

    async def provider(
        self, key: str, value: Any = None, ttl_seconds: int | None = 3600
    ) -> Any | None:
        return await self._get_or_set("provider", key, value, ttl_seconds)

    async def _get_or_set(
        self, namespace: str, key: str, value: Any, ttl_seconds: int | None
    ) -> Any | None:
        if value is None:
            return await self.get(namespace, key)
        await self.set(namespace, key, value, ttl_seconds)
        return value


cache_manager = CacheManager()
