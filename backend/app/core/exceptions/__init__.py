from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

from .ai import AIServiceError
from .base import AppException
from .domain import DomainError, ExecutionError, RepositoryError
from .infrastructure import InfrastructureError, PatchGenerationError, SandboxError
from .validation import ValidationError

logger = get_logger("exceptions")


class ReproProofError(AppException):
    """Backward-compatible legacy base exception used by the active app."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message, code="REPROPROOF_ERROR", status_code=status_code)


class InvalidFileTypeError(ReproProofError):
    def __init__(self, message: str = "Only ZIP files are accepted.") -> None:
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class FileTooLargeError(ReproProofError):
    def __init__(self, message: str = "File exceeds the maximum allowed size.") -> None:
        super().__init__(
            message=message, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )


class UploadError(ReproProofError):
    def __init__(self, message: str = "Failed to save uploaded file.") -> None:
        super().__init__(
            message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers needed by the active API runtime."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        logger.warning(
            "Application error: %s (status=%d)", exc.message, exc.status_code
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message},
        )

    @app.exception_handler(ReproProofError)
    async def reproproof_error_handler(
        request: Request, exc: ReproProofError
    ) -> JSONResponse:
        logger.warning(
            "Application error: %s (status=%d)", exc.message, exc.status_code
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "An unexpected internal error occurred.",
            },
        )


__all__ = [
    "AppException",
    "ReproProofError",
    "InvalidFileTypeError",
    "FileTooLargeError",
    "UploadError",
    "ValidationError",
    "DomainError",
    "RepositoryError",
    "ExecutionError",
    "InfrastructureError",
    "SandboxError",
    "PatchGenerationError",
    "AIServiceError",
    "register_exception_handlers",
]
