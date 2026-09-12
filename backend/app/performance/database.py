from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any


class ConnectionPool(ABC):
    @abstractmethod
    async def acquire(self) -> Any: ...

    @abstractmethod
    async def release(self, connection: Any) -> None: ...


class QueryOptimizer(ABC):
    @abstractmethod
    def optimize(
        self, query: str, parameters: Sequence[Any] = ()
    ) -> tuple[str, Sequence[Any]]: ...


class ReadReplicaRouter(ABC):
    @abstractmethod
    def route(self, *, write: bool = False) -> str: ...


class TransactionManager(ABC):
    @abstractmethod
    async def begin(self) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...


class BulkOperations(ABC):
    @abstractmethod
    async def insert_many(self, records: Sequence[dict[str, Any]]) -> int: ...


class Pagination(ABC):
    @abstractmethod
    async def page(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]: ...


class CursorPagination(Pagination):
    @abstractmethod
    async def cursor(
        self, *, limit: int = 50, after: str | None = None
    ) -> list[dict[str, Any]]: ...


@asynccontextmanager
async def transaction(manager: TransactionManager) -> AsyncIterator[None]:
    await manager.begin()
    try:
        yield
    except Exception:
        await manager.rollback()
        raise
    else:
        await manager.commit()
