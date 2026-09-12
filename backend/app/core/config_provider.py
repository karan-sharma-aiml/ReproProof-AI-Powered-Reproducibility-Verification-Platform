from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


@dataclass(frozen=True)
class AppConfig:
    """Stable application settings wrapper for enterprise service composition."""

    app_name: str
    app_version: str
    app_env: str
    debug: bool
    host: str
    port: int
    cors_origins: list[str]
    upload_dir: str
    reports_dir: str
    max_upload_size_mb: int

    @classmethod
    def from_settings(cls) -> "AppConfig":
        settings = get_settings()
        return cls(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            app_env=settings.APP_ENV,
            debug=settings.DEBUG,
            host=settings.HOST,
            port=settings.PORT,
            cors_origins=settings.cors_origins_list,
            upload_dir=settings.UPLOAD_DIR,
            reports_dir=settings.REPORTS_DIR,
            max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        )


class ConfigProvider:
    """Provider for application configuration used by enterprise layers."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig.from_settings()

    @property
    def config(self) -> AppConfig:
        return self._config

    def get(self, key: str, default: Any | None = None) -> Any:
        mapping = {
            "app_name": self._config.app_name,
            "app_version": self._config.app_version,
            "app_env": self._config.app_env,
            "debug": self._config.debug,
            "host": self._config.host,
            "port": self._config.port,
            "cors_origins": self._config.cors_origins,
            "upload_dir": self._config.upload_dir,
            "reports_dir": self._config.reports_dir,
            "max_upload_size_mb": self._config.max_upload_size_mb,
        }
        return mapping.get(key, default)
