from __future__ import annotations

import socket
import time
from abc import ABC, abstractmethod
from typing import Any

from .models import InfrastructureHealth, InfrastructureStatus, PostgresConfig


class Repository(ABC):
    @abstractmethod
    async def get(self, identifier: str) -> Any | None: ...

    @abstractmethod
    async def save(self, entity: Any) -> Any: ...


class DatabaseProvider(ABC):
    name = "database"

    @abstractmethod
    def health(self) -> InfrastructureHealth: ...

    @abstractmethod
    def connection_url(self) -> str: ...


class PostgreSQLProvider(DatabaseProvider):
    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def connection_url(self) -> str:
        return self.config.async_url

    def health(self) -> InfrastructureHealth:
        started = time.perf_counter()
        configured = bool(
            self.config.host and self.config.database and self.config.user
        )
        if not configured:
            return InfrastructureHealth(
                name=self.name,
                status=InfrastructureStatus.UNAVAILABLE,
                reason="postgres configuration incomplete",
            )
        try:
            with socket.create_connection(
                (self.config.host, self.config.port), timeout=0.25
            ):
                return InfrastructureHealth(
                    name=self.name,
                    status=InfrastructureStatus.HEALTHY,
                    configured=True,
                    connected=True,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    reason="tcp endpoint reachable",
                    metadata={
                        "pool_size": self.config.pool_size,
                        "max_overflow": self.config.max_overflow,
                    },
                )
        except OSError as exc:
            return InfrastructureHealth(
                name=self.name,
                status=InfrastructureStatus.DEGRADED,
                configured=True,
                connected=False,
                latency_ms=(time.perf_counter() - started) * 1000,
                reason=f"database unavailable: {exc}",
            )

    def sqlalchemy_engine_options(self) -> dict[str, Any]:
        return {
            "url": self.connection_url(),
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_pre_ping": True,
        }
