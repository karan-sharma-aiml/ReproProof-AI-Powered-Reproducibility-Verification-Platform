"""Object storage ports and local/S3-compatible implementations."""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    import boto3
except ImportError:
    boto3 = None


class StorageProvider(ABC):
    @abstractmethod
    def upload(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def download(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def list(self, prefix: str = "") -> list[dict[str, Any]]: ...

    @abstractmethod
    def signed_url(self, key: str, expires_seconds: int = 900) -> str: ...

    @abstractmethod
    def health(self) -> dict[str, Any]: ...


class LocalStorage(StorageProvider):
    def __init__(self, root: str = "uploads") -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("storage key escapes configured root")
        return path

    def upload(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return {
            "key": key,
            "size_bytes": len(content),
            "content_type": content_type,
            "version": hashlib.sha256(content).hexdigest()[:12],
            "metadata": metadata or {},
        }

    def download(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def list(self, prefix: str = "") -> list[dict[str, Any]]:
        return [
            {
                "key": str(path.relative_to(self.root)).replace("\\", "/"),
                "size_bytes": path.stat().st_size,
            }
            for path in self.root.rglob("*")
            if path.is_file()
            and str(path.relative_to(self.root)).replace("\\", "/").startswith(prefix)
        ]

    def signed_url(self, key: str, expires_seconds: int = 900) -> str:
        return f"local://{quote(key)}?expires={int(time.time()) + expires_seconds}"

    def health(self) -> dict[str, Any]:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            return {
                "status": "healthy",
                "provider": "local",
                "connected": True,
                "root": str(self.root),
            }
        except OSError as exc:
            return {
                "status": "degraded",
                "provider": "local",
                "connected": False,
                "reason": str(exc),
            }


class S3Storage(StorageProvider):
    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint: str = "",
        fallback: LocalStorage | None = None,
    ) -> None:
        self.bucket = bucket
        self.fallback = fallback or LocalStorage()
        self.client = (
            boto3.client(
                "s3",
                endpoint_url=endpoint or None,
                aws_access_key_id=access_key or None,
                aws_secret_access_key=secret_key or None,
            )
            if boto3
            else None
        )

    def _remote(self, operation: str, **kwargs: Any) -> Any:
        if self.client is None:
            raise RuntimeError("boto3 is not installed")
        return getattr(self.client, operation)(Bucket=self.bucket, **kwargs)

    def upload(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            self._remote(
                "put_object",
                Key=key,
                Body=content,
                ContentType=content_type,
                Metadata=metadata or {},
            )
            return {
                "key": key,
                "size_bytes": len(content),
                "content_type": content_type,
                "version": "remote",
                "metadata": metadata or {},
            }
        except Exception:
            return self.fallback.upload(key, content, content_type, metadata)

    def download(self, key: str) -> bytes:
        try:
            return self._remote("get_object", Key=key)["Body"].read()
        except Exception:
            return self.fallback.download(key)

    def delete(self, key: str) -> None:
        try:
            self._remote("delete_object", Key=key)
        except Exception:
            self.fallback.delete(key)

    def list(self, prefix: str = "") -> list[dict[str, Any]]:
        try:
            response = self._remote("list_objects_v2", Prefix=prefix)
            return [
                {"key": item["Key"], "size_bytes": item.get("Size", 0)}
                for item in response.get("Contents", [])
            ]
        except Exception:
            return self.fallback.list(prefix)

    def signed_url(self, key: str, expires_seconds: int = 900) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )
        except Exception:
            return self.fallback.signed_url(key, expires_seconds)

    def health(self) -> dict[str, Any]:
        try:
            self._remote("head_bucket")
            return {
                "status": "healthy",
                "provider": "s3",
                "connected": True,
                "bucket": self.bucket,
            }
        except Exception as exc:
            return {
                "status": "degraded",
                "provider": "s3",
                "connected": False,
                "fallback": True,
                "reason": str(exc),
            }


class MinIOStorage(S3Storage):
    pass
