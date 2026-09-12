from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import quote

from .models import (
    InfrastructureHealth,
    InfrastructureStatus,
    StorageConfig,
    StorageMetadata,
)


class ObjectStorage(ABC):
    @abstractmethod
    def upload(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> StorageMetadata: ...

    @abstractmethod
    def download(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def signed_url(self, key: str, expires_seconds: int = 900) -> str: ...

    @abstractmethod
    def health(self) -> InfrastructureHealth: ...


class LocalFilesystemStorage(ObjectStorage):
    def __init__(self, config: StorageConfig | None = None) -> None:
        self.config = config or StorageConfig()
        self.root = Path(self.config.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError("storage key escapes configured root")
        return path

    def upload(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> StorageMetadata:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StorageMetadata(
            key=key,
            size_bytes=len(content),
            content_type=content_type,
            version=hashlib.sha256(content).hexdigest()[:12],
            metadata=metadata or {},
        )

    def download(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def signed_url(self, key: str, expires_seconds: int = 900) -> str:
        return f"local://{quote(key)}?expires={int(time.time()) + expires_seconds}"

    def health(self) -> InfrastructureHealth:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            return InfrastructureHealth(
                name="storage",
                status=InfrastructureStatus.HEALTHY,
                configured=True,
                connected=True,
                reason="local filesystem writable",
                metadata={"provider": "local", "root": str(self.root)},
            )
        except OSError as exc:
            return InfrastructureHealth(
                name="storage",
                status=InfrastructureStatus.UNAVAILABLE,
                configured=True,
                reason=str(exc),
            )


class MinIOStorage(LocalFilesystemStorage):
    provider = "minio"


class S3Storage(LocalFilesystemStorage):
    provider = "s3"
