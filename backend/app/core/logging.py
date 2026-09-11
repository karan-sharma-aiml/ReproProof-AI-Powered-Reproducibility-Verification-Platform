"""
Structured logging configuration.

Provides a pre-configured logger for the application that writes
JSON-formatted entries in production and human-readable entries
in development.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the application root logger."""
    settings = get_settings()
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("reproproof")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under the ``reproproof`` namespace."""
    base = "reproproof"
    full_name = f"{base}.{name}" if name else base
    return logging.getLogger(full_name)
