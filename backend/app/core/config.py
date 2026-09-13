"""
Application configuration management.

Loads settings from environment variables and .env file using pydantic-settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.production"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "ReproProof"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Server ───────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ─────────────────────────────────────────────────────────────
    # Development: localhost and loopback origins used by local Next/Vite servers.
    # Production: https://your-frontend-domain.vercel.app
    CORS_ORIGINS: str = (
        '["http://localhost:3000","http://127.0.0.1:3000",'
        '"http://localhost:5173","http://127.0.0.1:5173",'
        '"http://localhost:3001","http://127.0.0.1:3001"]'
    )

    # ── Uploads / Reports ────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    REPORTS_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = 50
    GITHUB_CLONE_TIMEOUT_SECONDS: float = 120.0

    # Optional infrastructure services. Local filesystem and in-process
    # fallbacks keep developer startup independent of external services.
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "reproproof"
    POSTGRES_USER: str = "reproproof"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_POOL_SIZE: int = 5
    POSTGRES_MAX_OVERFLOW: int = 10
    POSTGRES_ENABLED: bool = False
    DATABASE_URL: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False
    REDIS_URL: str = ""
    STORAGE_PROVIDER: str = "local"
    STORAGE_ROOT: str = "uploads"
    S3_BUCKET: str = "reproproof"
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    OBJECT_STORAGE_PROVIDER: str = ""
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    @property
    def database_url(self) -> str:
        """Return the configured database URL, or the local SQLite default."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite+aiosqlite:///./reproproof.db"

    @property
    def redis_url(self) -> str:
        """Return the configured Redis URL, or the legacy host-based URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        password = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def object_storage_provider(self) -> str:
        return (
            self.OBJECT_STORAGE_PROVIDER or self.STORAGE_PROVIDER or "local"
        ).lower()

    @property
    def object_storage_bucket(self) -> str:
        return self.MINIO_BUCKET or self.S3_BUCKET

    # AI provider configuration remains optional for local development.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_TOKENS: int = 8192
    DEFAULT_LLM_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    LLM_TIMEOUT: float = 30.0
    LLM_MAX_RETRIES: int = 2

    # Security is opt-in for backward-compatible local development.
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECURITY_HEADERS_ENABLED: bool = True
    REQUIRE_HTTPS: bool = False
    TRUSTED_HOSTS: str = "*"
    SECURITY_RATE_LIMIT_REQUESTS: int = 120
    SECURITY_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Derived helpers ──────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the JSON-encoded CORS_ORIGINS string into a Python list."""
        try:
            origins = json.loads(self.CORS_ORIGINS)
            if isinstance(origins, list) and all(
                isinstance(origin, str) and origin for origin in origins
            ):
                return origins
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR)

    @property
    def reports_path(self) -> Path:
        return Path(self.REPORTS_DIR)

    @property
    def trusted_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.TRUSTED_HOSTS.split(",") if host.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
