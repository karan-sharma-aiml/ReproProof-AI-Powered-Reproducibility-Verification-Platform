from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ApiResponse:
    success: bool
    message: str
    data: Any | None = None
    error: str | None = None


@dataclass(frozen=True)
class SuccessResponse(ApiResponse):
    success: bool = True


@dataclass(frozen=True)
class ErrorResponse(ApiResponse):
    success: bool = False
    error: str | None = None


@dataclass(frozen=True)
class PaginatedResponse(Generic[T]):
    items: list[T] = field(default_factory=list)
    page: int = 1
    page_size: int = 20
    total: int = 0
    has_next: bool = False


@dataclass(frozen=True)
class HealthResponse(ApiResponse):
    status: str = "ok"
    environment: str = "development"
    timestamp: str | None = None


@dataclass(frozen=True)
class ExecutionResponse(ApiResponse):
    execution_id: str | None = None
    status: str | None = None
    progress: int = 0


@dataclass(frozen=True)
class AnalysisResponse(ApiResponse):
    repository_id: str | None = None
    summary: str | None = None


@dataclass(frozen=True)
class PatchResponse(ApiResponse):
    patch_id: str | None = None
    file_name: str | None = None
    confidence: float | None = None
