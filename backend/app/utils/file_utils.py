"""
File-system helper utilities.

Provides functions for safe filename generation, directory bootstrapping,
and file-type validation.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Allowed MIME types and extensions for uploads
ALLOWED_CONTENT_TYPES = frozenset(
    [
        "application/zip",
        "application/x-zip-compressed",
        "application/x-zip",
        "application/octet-stream",  # fallback some clients send for .zip
    ]
)
ALLOWED_EXTENSIONS = frozenset([".zip"])


def ensure_directory(path: Path) -> Path:
    """Create the directory (and parents) if it does not exist, then return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(filename: str) -> str:
    """Strip path separators and dangerous characters from a filename."""
    # Take only the final component (defence against path traversal)
    name = Path(filename).name
    # Replace anything that isn't alphanumeric, dash, underscore, or dot
    name = re.sub(r"[^\w.\-]", "_", name)
    return name


def generate_upload_filename(original_filename: str) -> tuple[str, str]:
    """
    Return ``(upload_id, safe_filename)`` where the safe filename is
    prefixed with a UUID to prevent collisions.
    """
    upload_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = sanitize_filename(original_filename)
    saved_name = f"{upload_id}_{timestamp}_{safe_name}"
    return upload_id, saved_name


def is_valid_zip(filename: str, content_type: str | None) -> bool:
    """Check that the file looks like a ZIP based on extension and MIME type."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    # If content_type was provided, validate it as well
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        return False
    return True
