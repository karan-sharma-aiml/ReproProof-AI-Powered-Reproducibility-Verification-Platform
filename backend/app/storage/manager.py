"""Configuration-driven object storage composition root."""

from __future__ import annotations

from app.core.config import get_settings

from .providers import LocalStorage, MinIOStorage, S3Storage, StorageProvider


class ObjectStorageManager:
    def __init__(self, provider: StorageProvider | None = None) -> None:
        settings = get_settings()
        local = LocalStorage(settings.STORAGE_ROOT or settings.UPLOAD_DIR)
        if provider is not None:
            self.provider = provider
        elif settings.object_storage_provider == "s3":
            self.provider = S3Storage(
                settings.object_storage_bucket,
                settings.AWS_ACCESS_KEY_ID or settings.S3_ACCESS_KEY,
                settings.AWS_SECRET_ACCESS_KEY or settings.S3_SECRET_KEY,
                fallback=local,
            )
        elif settings.object_storage_provider == "minio":
            self.provider = MinIOStorage(
                settings.object_storage_bucket,
                settings.MINIO_ACCESS_KEY or settings.S3_ACCESS_KEY,
                settings.MINIO_SECRET_KEY or settings.S3_SECRET_KEY,
                settings.MINIO_ENDPOINT or settings.S3_ENDPOINT,
                fallback=local,
            )
        else:
            self.provider = local

    def upload(self, *args, **kwargs):
        return self.provider.upload(*args, **kwargs)

    def download(self, *args, **kwargs):
        return self.provider.download(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.provider.delete(*args, **kwargs)

    def list(self, *args, **kwargs):
        return self.provider.list(*args, **kwargs)

    def signed_url(self, *args, **kwargs):
        return self.provider.signed_url(*args, **kwargs)

    def health(self):
        return self.provider.health()


object_storage = ObjectStorageManager()
