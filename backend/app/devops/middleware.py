from __future__ import annotations

import time
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger

from .metrics import metrics
from .observability import error_monitor, trace_provider
from .rate_limit import RateLimiter

request_id_context: ContextVar[str] = ContextVar("request_id", default="")


class DevOpsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self.limiter = limiter or RateLimiter(
            limit=settings.SECURITY_RATE_LIMIT_REQUESTS,
            window_seconds=settings.SECURITY_RATE_LIMIT_WINDOW_SECONDS,
        )
        self.logger = get_logger("http")

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        request_id_context.set(request_id)
        client = request.client.host if request.client else "unknown"
        if not self.limiter.allow(client):
            metrics.increment(
                "rate_limited_requests_total", labels={"path": request.url.path}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )
        started = time.perf_counter()
        status_code = 500
        with trace_provider.start_span(
            "http.request", {"request_id": request_id, "path": request.url.path}
        ):
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            except Exception as exc:
                metrics.increment(
                    "http_errors_total", labels={"path": request.url.path}
                )
                error_monitor.capture(
                    exc, {"request_id": request_id, "path": request.url.path}
                )
                self.logger.exception(
                    "request_failed request_id=%s error=%s", request_id, exc
                )
                raise
            finally:
                duration = time.perf_counter() - started
                labels = {
                    "method": request.method,
                    "path": request.url.path,
                    "status": str(status_code),
                }
                metrics.increment("http_requests_total", labels=labels)
                metrics.observe(
                    "http_request_duration_seconds",
                    duration,
                    labels={"method": request.method, "path": request.url.path},
                )
                self.logger.info(
                    "request_completed request_id=%s method=%s path=%s status=%s duration_seconds=%.4f",
                    request_id,
                    request.method,
                    request.url.path,
                    status_code,
                    duration,
                )
                request_id_context.set("")
                if "response" in locals():
                    response.headers["X-Request-ID"] = request_id


def install_devops_middleware(app) -> None:
    app.add_middleware(DevOpsMiddleware)
