"""Redis-backed cache with automatic in-process fallback."""

from .manager import CacheManager, cache_manager
from .providers import InMemoryCache, RedisCache

__all__ = ["CacheManager", "InMemoryCache", "RedisCache", "cache_manager"]
