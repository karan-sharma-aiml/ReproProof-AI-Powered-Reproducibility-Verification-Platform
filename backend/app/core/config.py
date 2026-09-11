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
        env_file=".env",
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
    CORS_ORIGINS: str = (
        '["http://localhost:3000","http://localhost:5173","http://localhost:3001"]'
    )

    # ── Uploads / Reports ────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    REPORTS_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── Derived helpers ──────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the JSON-encoded CORS_ORIGINS string into a Python list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["*"]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR)

    @property
    def reports_path(self) -> Path:
        return Path(self.REPORTS_DIR)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
