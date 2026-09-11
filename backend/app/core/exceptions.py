"""
Custom exception classes and FastAPI exception handlers.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger("exceptions")


# ── Custom Exceptions ────────────────────────────────────────────────────────


class ReproProofError(Exception):
    """Base exception for all application-specific errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InvalidFileTypeError(ReproProofError):
    """Raised when an uploaded file is not an allowed type."""

    def __init__(self, message: str = "Only ZIP files are accepted.") -> None:
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class FileTooLargeError(ReproProofError):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, message: str = "File exceeds the maximum allowed size.") -> None:
        super().__init__(message=message, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


class UploadError(ReproProofError):
    """Raised when the upload process fails for any I/O reason."""

    def __init__(self, message: str = "Failed to save uploaded file.") -> None:
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Handler Registration ────────────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    @app.exception_handler(ReproProofError)
    async def reproproof_error_handler(
        request: Request, exc: ReproProofError
    ) -> JSONResponse:
        logger.warning("Application error: %s (status=%d)", exc.message, exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled server error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "An unexpected internal error occurred.",
            },
        )
