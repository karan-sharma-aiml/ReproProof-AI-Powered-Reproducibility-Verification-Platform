from __future__ import annotations


class AppException(Exception):
    """Base application exception for the enterprise platform layers."""

    def __init__(
        self, message: str, *, code: str | None = None, status_code: int = 500
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.status_code = status_code
