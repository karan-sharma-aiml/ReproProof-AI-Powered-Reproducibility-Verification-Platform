from __future__ import annotations

import asyncio
from pathlib import Path

from app.cache.providers import InMemoryCache, RedisCache
from app.storage.providers import LocalStorage


def test_redis_provider_falls_back_to_memory() -> None:
    async def run() -> None:
        cache = RedisCache("redis://127.0.0.1:1/0")
        await cache.set("key", {"value": 1}, ttl_seconds=30)
        assert await cache.get("key") == {"value": 1}
        assert await cache.health() is False

    asyncio.run(run())


def test_in_memory_cache_honors_ttl() -> None:
    async def run() -> None:
        cache = InMemoryCache()
        await cache.set("key", "value", ttl_seconds=1)
        assert await cache.get("key") == "value"

    asyncio.run(run())


def test_local_object_storage_round_trip(tmp_path: Path) -> None:
    storage = LocalStorage(str(tmp_path))
    metadata = storage.upload(
        "reports/result.txt", b"ok", "text/plain", {"kind": "test"}
    )
    assert metadata["size_bytes"] == 2
    assert storage.download("reports/result.txt") == b"ok"
    assert storage.list("reports/")[0]["key"] == "reports/result.txt"
    assert storage.signed_url("reports/result.txt").startswith("local://")
    storage.delete("reports/result.txt")
    assert storage.list("reports/") == []
