"""Lightweight migration hooks kept additive to the existing deployment setup."""

from .runner import migration_status, run_migrations

__all__ = ["migration_status", "run_migrations"]
