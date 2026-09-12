from __future__ import annotations

from app.core.config import get_settings
from app.cache import cache_manager
from app.database.database import database_health
from app.database.migrations import migration_status
from app.storage import object_storage
from app.integrations.composition import provider_manager

from .database import PostgreSQLProvider
from .models import (
    InfrastructureHealth,
    InfrastructureOverview,
    InfrastructureStatus,
    PostgresConfig,
    RedisConfig,
    StorageConfig,
)
from .monitoring import monitoring_artifacts
from .redis import OptionalRedisClient
from .storage import LocalFilesystemStorage, MinIOStorage, ObjectStorage, S3Storage


class InfrastructureService:
    def __init__(self) -> None:
        settings = get_settings()
        self.database = PostgreSQLProvider(
            PostgresConfig(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                pool_size=settings.POSTGRES_POOL_SIZE,
                max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            )
        )
        self.redis = OptionalRedisClient(
            RedisConfig(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
            )
        )
        storage_config = StorageConfig(
            provider=settings.STORAGE_PROVIDER,
            root=settings.STORAGE_ROOT,
            bucket=settings.S3_BUCKET,
            endpoint=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
        )
        storage_types = {
            "local": LocalFilesystemStorage,
            "minio": MinIOStorage,
            "s3": S3Storage,
        }
        self.storage: ObjectStorage = storage_types.get(
            settings.STORAGE_PROVIDER, LocalFilesystemStorage
        )(storage_config)
        self.database_enabled = settings.POSTGRES_ENABLED
        self.redis_enabled = settings.REDIS_ENABLED
        self.production_storage = object_storage

    def database_health(self) -> InfrastructureHealth:
        if not self.database_enabled:
            return InfrastructureHealth(
                name="database",
                status=InfrastructureStatus.UNAVAILABLE,
                configured=False,
                reason="PostgreSQL is optional and disabled",
            )
        return self.database.health()

    async def cache_health(self) -> InfrastructureHealth:
        result = await cache_manager.health()
        return InfrastructureHealth(
            name="cache",
            status=(
                InfrastructureStatus.HEALTHY
                if result["status"] == "healthy"
                else InfrastructureStatus.DEGRADED
            ),
            configured=True,
            connected=result["status"] == "healthy",
            reason=(
                "cache provider available"
                if result["status"] == "healthy"
                else "Redis unavailable; using in-memory fallback"
            ),
            metadata=result,
        )

    def overview(self) -> InfrastructureOverview:
        database = self.database_health()
        storage = self.storage.health()
        monitoring = InfrastructureHealth(
            name="monitoring",
            status=InfrastructureStatus.HEALTHY,
            configured=True,
            connected=True,
            reason="Prometheus-compatible metrics and Grafana artifacts available",
        )
        application = InfrastructureHealth(
            name="application",
            status=InfrastructureStatus.HEALTHY,
            configured=True,
            connected=True,
            reason="application process available",
        )
        containers = InfrastructureHealth(
            name="containers",
            status=InfrastructureStatus.DEGRADED,
            configured=False,
            connected=False,
            reason="container runtime is deployment-managed",
        )
        return InfrastructureOverview(
            application=application,
            database=database,
            cache=InfrastructureHealth(
                name="cache",
                status=InfrastructureStatus.UNAVAILABLE,
                configured=False,
                reason="Redis health is asynchronous; use /infrastructure/cache",
            ),
            storage=storage,
            monitoring=monitoring,
            containers=containers,
            providers=[],
            migration_status=migration_status(),
        )

    async def overview_async(self) -> InfrastructureOverview:
        overview = self.overview()
        database_result = await database_health()
        overview.database = InfrastructureHealth(
            name="database",
            status=(
                InfrastructureStatus.HEALTHY
                if database_result.get("status") == "healthy"
                else InfrastructureStatus.DEGRADED
            ),
            configured=bool(database_result.get("configured")),
            connected=bool(database_result.get("connected")),
            reason=str(database_result.get("reason", "database check complete")),
            metadata=database_result,
        )
        overview.cache = await self.cache_health()
        storage_result = self.production_storage.health()
        overview.storage = InfrastructureHealth(
            name="storage",
            status=(
                InfrastructureStatus.HEALTHY
                if storage_result.get("status") == "healthy"
                else InfrastructureStatus.DEGRADED
            ),
            configured=True,
            connected=bool(storage_result.get("connected")),
            reason=str(storage_result.get("reason", "storage check complete")),
            metadata=storage_result,
        )
        overview.providers = [
            InfrastructureHealth(
                name=item.provider,
                status=(
                    InfrastructureStatus.HEALTHY
                    if item.healthy
                    else InfrastructureStatus.DEGRADED
                ),
                configured=item.configured,
                connected=item.connected,
                latency_ms=item.latency_ms,
                reason=item.reason,
                metadata={
                    "available_models": list(item.available_models),
                    "default_provider": item.default_provider,
                },
            )
            for item in await provider_manager.health()
        ]
        return overview


infrastructure_service = InfrastructureService()
