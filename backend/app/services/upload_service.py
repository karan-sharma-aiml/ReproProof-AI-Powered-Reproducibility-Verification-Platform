"""
Upload service – business logic for receiving and persisting ZIP uploads.

Keeps I/O concerns out of the API layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError, UploadError
from app.core.logging import get_logger
from app.schemas.responses import UploadData
from app.services.repository_analysis_service import RepositoryAnalysisService
from app.utils.file_utils import (
    ensure_directory,
    generate_upload_filename,
    is_valid_zip,
)

logger = get_logger("upload_service")


async def handle_upload(file: UploadFile) -> UploadData:
    """
    Validate, save, and return metadata for an uploaded ZIP file.

    Raises
    ------
    InvalidFileTypeError
        If the file is not a ZIP archive.
    FileTooLargeError
        If the file exceeds ``MAX_UPLOAD_SIZE_MB``.
    UploadError
        If an I/O error prevents saving.
    """
    settings = get_settings()

    # ── Validate file type ───────────────────────────────────────────────
    original_filename = file.filename or "unknown.zip"
    if not is_valid_zip(original_filename, file.content_type):
        logger.warning(
            "Rejected upload: filename=%s content_type=%s",
            original_filename,
            file.content_type,
        )
        raise InvalidFileTypeError(
            f"Invalid file type. Only .zip files are accepted. "
            f"Received: {original_filename}"
        )

    # ── Read file content and validate size ──────────────────────────────
    try:
        content = await file.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded file")
        raise UploadError("Could not read the uploaded file.") from exc

    if len(content) > settings.max_upload_bytes:
        raise FileTooLargeError(
            f"File size ({len(content) / (1024 * 1024):.1f} MB) exceeds "
            f"the {settings.MAX_UPLOAD_SIZE_MB} MB limit."
        )

    if len(content) == 0:
        raise InvalidFileTypeError("Uploaded file is empty.")

    # ── Persist to disk ──────────────────────────────────────────────────
    upload_id, saved_filename = generate_upload_filename(original_filename)
    upload_dir = ensure_directory(settings.upload_path)
    dest = upload_dir / saved_filename

    try:
        dest.write_bytes(content)
    except OSError as exc:
        logger.exception("Failed to write file to %s", dest)
        raise UploadError("Could not save the uploaded file to disk.") from exc

    try:
        RepositoryAnalysisService().extract_and_analyze(dest, upload_id)
    except ValueError as exc:
        logger.exception("Failed to analyze uploaded repository: %s", upload_id)
        raise InvalidFileTypeError(str(exc)) from exc

    logger.info(
        "Upload saved: id=%s file=%s size=%d bytes",
        upload_id,
        saved_filename,
        len(content),
    )

    return UploadData(
        upload_id=upload_id,
        original_filename=original_filename,
        saved_filename=saved_filename,
        size_bytes=len(content),
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        repository_path=f"{upload_id}/repository",
    )
