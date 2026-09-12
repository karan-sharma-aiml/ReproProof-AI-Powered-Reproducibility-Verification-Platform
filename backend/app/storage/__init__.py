"""Provider-neutral object storage with local fallback."""

from .manager import ObjectStorageManager, object_storage
from .providers import LocalStorage, MinIOStorage, S3Storage, StorageProvider

__all__ = [
    "LocalStorage",
    "MinIOStorage",
    "ObjectStorageManager",
    "S3Storage",
    "StorageProvider",
    "object_storage",
]
