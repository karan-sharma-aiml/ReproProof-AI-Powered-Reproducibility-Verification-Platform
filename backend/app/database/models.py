"""SQLAlchemy 2.x models for durable infrastructure records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from sqlalchemy import DateTime, JSON, String, Text, func
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
except (
    ImportError
):  # Keep local startup usable before optional dependencies are installed.

    class Base:
        metadata = None

else:

    class Base(DeclarativeBase):
        pass

    class _Record(Base):
        __abstract__ = True
        id: Mapped[str] = mapped_column(String(128), primary_key=True)
        payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now()
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )

    class User(_Record):
        __tablename__ = "users"

    class RepositoryRecord(_Record):
        __tablename__ = "repositories"

    class Project(_Record):
        __tablename__ = "projects"

    class ResearchReport(_Record):
        __tablename__ = "research_reports"

    class ExecutionHistory(_Record):
        __tablename__ = "execution_history"

    class JudgeResult(_Record):
        __tablename__ = "judge_results"

    class ExperimentTimeline(_Record):
        __tablename__ = "experiment_timeline"

    class ProviderLog(_Record):
        __tablename__ = "provider_logs"

    class DashboardAnalytic(_Record):
        __tablename__ = "dashboard_analytics"


__all__ = [
    "Base",
    "User",
    "RepositoryRecord",
    "Project",
    "ResearchReport",
    "ExecutionHistory",
    "JudgeResult",
    "ExperimentTimeline",
    "ProviderLog",
    "DashboardAnalytic",
]
