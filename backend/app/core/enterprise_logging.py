from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


class StructuredLogger:
    """Thin structured logger for enterprise instrumentation and future telemetry."""

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

    def _emit(self, level: int, event: str, **fields: Any) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": logging.getLevelName(level),
            "event": event,
            "fields": fields,
        }
        self._logger.log(level, json.dumps(payload, default=str, sort_keys=True))

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._emit(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self._emit(logging.ERROR, event, **fields)

    def exception(self, event: str, **fields: Any) -> None:
        self._emit(logging.ERROR, event, **fields)


def get_enterprise_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
