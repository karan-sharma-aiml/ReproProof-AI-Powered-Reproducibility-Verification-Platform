"""Migration compatibility hooks.

The first additive migration uses SQLAlchemy metadata creation and can later be
replaced by Alembic revisions without changing callers.
"""

from __future__ import annotations

from app.database.database import init_database


async def run_migrations() -> str:
    await init_database()
    return "applied"


def migration_status() -> dict[str, str]:
    return {"status": "managed", "strategy": "sqlalchemy-metadata"}
