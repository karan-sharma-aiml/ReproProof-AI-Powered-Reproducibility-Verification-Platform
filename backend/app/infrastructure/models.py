from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InfrastructureStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class InfrastructureHealth(BaseModel):
    name: str
    status: InfrastructureStatus
    configured: bool = False
    connected: bool = False
    latency_ms: float = 0
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class InfrastructureOverview(BaseModel):
    application: InfrastructureHealth
    database: InfrastructureHealth
    cache: InfrastructureHealth
    storage: InfrastructureHealth
    monitoring: InfrastructureHealth
    containers: InfrastructureHealth
    providers: list[InfrastructureHealth] = Field(default_factory=list)
    migration_status: dict[str, str] = Field(default_factory=dict)


class StorageMetadata(BaseModel):
    key: str
    size_bytes: int = 0
    content_type: str = "application/octet-stream"
    version: str = "local"
    metadata: dict[str, str] = Field(default_factory=dict)


class PostgresConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "reproproof"
    user: str = "reproproof"
    password: str = ""
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class StorageConfig(BaseModel):
    provider: str = "local"
    root: str = "uploads"
    bucket: str = "reproproof"
    endpoint: str = ""
    access_key: str = ""
    secret_key: str = ""
