"""SQLAlchemy engine, health, and migration entry points."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
except (
    ImportError
):  # Optional during local development until requirements are installed.
    AsyncEngine = Any  # type: ignore[misc,assignment]
    create_engine = None
    create_async_engine = None
    text = None

_engine: AsyncEngine | Any | None = None


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def get_engine() -> AsyncEngine | Any:
    """Return the lazily-created pooled async engine."""
    global _engine
    if _engine is None:
        if create_async_engine is None:
            raise RuntimeError("SQLAlchemy dependencies are not installed")
        settings = get_settings()
        url = _async_url(settings.database_url)
        options: dict[str, Any] = {"pool_pre_ping": True}
        if not url.startswith("sqlite"):
            options.update(
                pool_size=settings.POSTGRES_POOL_SIZE,
                max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            )
        _engine = create_async_engine(url, **options)
    return _engine


async def init_database() -> None:
    """Create the additive tables when the configured database is reachable."""
    from .models import Base

    engine = get_engine()
    if Base.metadata is None:
        raise RuntimeError("SQLAlchemy dependencies are not installed")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def database_health() -> dict[str, Any]:
    """Execute a real database ping without making startup depend on it."""
    if text is None:
        return {
            "status": "unavailable",
            "configured": False,
            "reason": "SQLAlchemy is not installed",
        }
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "configured": True,
            "connected": True,
            "migration_status": "available",
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "configured": True,
            "connected": False,
            "reason": str(exc),
            "migration_status": "unknown",
        }
