from __future__ import annotations

from app.core.exceptions.base import AppException


class ValidationError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)
