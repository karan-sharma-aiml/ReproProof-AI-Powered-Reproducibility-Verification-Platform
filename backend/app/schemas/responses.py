"""
Pydantic response schemas used across API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ── Generic ──────────────────────────────────────────────────────────────────


class BaseResponse(BaseModel):
    """Envelope shared by every API response."""

    success: bool
    message: str


# ── Root / Health ────────────────────────────────────────────────────────────


class RootResponse(BaseResponse):
    app: str
    version: str
    docs: str


class HealthResponse(BaseResponse):
    status: str
    environment: str
    timestamp: str


# ── Upload ───────────────────────────────────────────────────────────────────


class UploadData(BaseModel):
    upload_id: str
    original_filename: str
    saved_filename: str
    size_bytes: int
    uploaded_at: str
    repository_path: str = ""


class UploadResponse(BaseResponse):
    data: UploadData


# ── Status ───────────────────────────────────────────────────────────────────


class UploadSummary(BaseModel):
    upload_id: str = ""
    filename: str
    size_bytes: int
    uploaded_at: str


class StatusResponse(BaseResponse):
    environment: str
    uploads_dir: str
    reports_dir: str
    total_uploads: int
    uploads: List[UploadSummary]


# ── Errors ───────────────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
