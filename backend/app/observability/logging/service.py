from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from ..tracing.service import tracer

_log_context: ContextVar[dict[str, Any]] = ContextVar(
    "observability_log_context", default={}
)


class StructuredLogContext:
    def __init__(self, **fields: Any) -> None:
        self.fields = fields
        self.token = None

    def __enter__(self) -> "StructuredLogContext":
        self.token = _log_context.set({**_log_context.get(), **self.fields})
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.token is not None:
            _log_context.reset(self.token)


class JsonContextLogger:
    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.service = name

    def log(self, level: int, message: str, **fields: Any) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": logging.getLevelName(level),
            "severity": logging.getLevelName(level).lower(),
            "message": message,
            "request_id": "",
            "repository_id": "",
            "user": "",
            "service": self.service,
            "agent": "",
            "provider": "",
            "latency": 0,
            "status": "unknown",
            "trace_id": tracer.context().trace_id,
            **_log_context.get(),
            **fields,
        }
        self.logger.log(level, json.dumps(payload, default=str, sort_keys=True))

    def info(self, message: str, **fields: Any) -> None:
        self.log(logging.INFO, message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self.log(logging.WARNING, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self.log(logging.ERROR, message, **fields)


def get_observability_logger(name: str) -> JsonContextLogger:
    return JsonContextLogger(name)
