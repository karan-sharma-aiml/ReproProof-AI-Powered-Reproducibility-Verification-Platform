"""Generic async repositories for the platform's durable record types."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select

from ..models import (
    DashboardAnalytic,
    ExecutionHistory,
    ExperimentTimeline,
    JudgeResult,
    Project,
    ProviderLog,
    RepositoryRecord,
    ResearchReport,
    User,
)
from ..session import session_scope

ModelT = TypeVar("ModelT")


class SQLAlchemyRepository(Generic[ModelT]):
    model: type[ModelT]

    async def get(self, identifier: str) -> ModelT | None:
        async with session_scope() as session:
            return await session.get(self.model, identifier)

    async def save(self, identifier: str, payload: dict[str, Any]) -> ModelT:
        async with session_scope() as session:
            entity = await session.get(self.model, identifier)
            if entity is None:
                entity = self.model(id=identifier, payload=payload)
                session.add(entity)
            else:
                entity.payload = payload
            await session.flush()
            return entity

    async def list(self, limit: int = 100) -> list[ModelT]:
        async with session_scope() as session:
            result = await session.execute(select(self.model).limit(limit))
            return list(result.scalars())


def _repository(name: str, model: type[Any]) -> type[SQLAlchemyRepository[Any]]:
    return type(name, (SQLAlchemyRepository,), {"model": model})


UserRepository = _repository("UserRepository", User)
RepositoryRepository = _repository("RepositoryRepository", RepositoryRecord)
ProjectRepository = _repository("ProjectRepository", Project)
ResearchReportRepository = _repository("ResearchReportRepository", ResearchReport)
ExecutionHistoryRepository = _repository("ExecutionHistoryRepository", ExecutionHistory)
JudgeResultRepository = _repository("JudgeResultRepository", JudgeResult)
ExperimentTimelineRepository = _repository(
    "ExperimentTimelineRepository", ExperimentTimeline
)
ProviderLogRepository = _repository("ProviderLogRepository", ProviderLog)
DashboardAnalyticsRepository = _repository(
    "DashboardAnalyticsRepository", DashboardAnalytic
)

__all__ = [name for name in globals() if name.endswith("Repository")]
