from __future__ import annotations

from app.core.exceptions.base import AppException


class AIServiceError(AppException):
    def __init__(
        self, message: str, *, code: str = "AI_SERVICE_ERROR", status_code: int = 500
    ) -> None:
        super().__init__(message, code=code, status_code=status_code)
