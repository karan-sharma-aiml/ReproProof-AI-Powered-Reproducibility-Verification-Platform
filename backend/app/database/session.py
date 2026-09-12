"""Async session factory with a small dependency-injection boundary."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
except ImportError:
    AsyncSession = Any  # type: ignore[misc,assignment]
    async_sessionmaker = None

from .database import get_engine

_factory: Any | None = None


def get_session_factory() -> Any:
    global _factory
    if _factory is None:
        if async_sessionmaker is None:
            raise RuntimeError("SQLAlchemy dependencies are not installed")
        _factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _factory


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    session = get_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
