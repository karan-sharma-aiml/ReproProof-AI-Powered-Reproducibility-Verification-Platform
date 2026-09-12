from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .ports import ErrorMonitor, TraceProvider


class LoggingErrorMonitor(ErrorMonitor):
    def __init__(self) -> None:
        self.logger = logging.getLogger("reproproof.errors")

    def capture(
        self, error: BaseException, context: dict[str, Any] | None = None
    ) -> None:
        self.logger.exception(
            "error_monitor_capture error=%s context=%s", error, context or {}
        )


class RequestTraceProvider(TraceProvider):
    """Minimal local trace provider; replace with OpenTelemetry at deployment time."""

    @contextmanager
    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        span = {
            "name": name,
            "attributes": attributes or {},
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            yield span
        finally:
            span["ended_at"] = datetime.now(timezone.utc).isoformat()


error_monitor = LoggingErrorMonitor()
trace_provider = RequestTraceProvider()
