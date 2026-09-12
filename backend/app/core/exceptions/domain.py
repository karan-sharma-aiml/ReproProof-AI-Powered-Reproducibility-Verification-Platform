from __future__ import annotations

from app.core.exceptions.base import AppException


class DomainError(AppException):
    def __init__(
        self, message: str, *, code: str = "DOMAIN_ERROR", status_code: int = 400
    ) -> None:
        super().__init__(message, code=code, status_code=status_code)


class RepositoryError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="REPOSITORY_ERROR", status_code=400)


class ExecutionError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="EXECUTION_ERROR", status_code=500)
