from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings

from .headers import SecurityHeaders


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, headers: SecurityHeaders | None = None) -> None:
        super().__init__(app)
        self.headers = headers or SecurityHeaders()

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for name, value in self.headers.as_dict().items():
            response.headers.setdefault(name, value)
        return response


def install_security_middleware(app) -> None:
    settings = get_settings()
    if settings.TRUSTED_HOSTS != "*":
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list
        )
    if settings.REQUIRE_HTTPS:
        app.add_middleware(HTTPSRedirectMiddleware)
    if settings.SECURITY_HEADERS_ENABLED:
        app.add_middleware(SecurityHeadersMiddleware)
