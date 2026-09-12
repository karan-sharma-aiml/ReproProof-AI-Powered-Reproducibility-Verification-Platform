from __future__ import annotations

from app.core.exceptions.base import AppException


class InfrastructureError(AppException):
    def __init__(
        self,
        message: str,
        *,
        code: str = "INFRASTRUCTURE_ERROR",
        status_code: int = 500,
    ) -> None:
        super().__init__(message, code=code, status_code=status_code)


class SandboxError(InfrastructureError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="SANDBOX_ERROR", status_code=500)


class PatchGenerationError(InfrastructureError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="PATCH_GENERATION_ERROR", status_code=500)
