"""
ReproProof – FastAPI application factory.

Creates and configures the application instance including middleware,
exception handlers, routes, and startup tasks.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.utils.file_utils import ensure_directory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup / shutdown lifecycle hook."""
    # ── Startup ──────────────────────────────────────────────────────────
    logger = setup_logging()
    settings = get_settings()

    ensure_directory(settings.upload_path)
    ensure_directory(settings.reports_path)

    logger.info(
        "%s v%s starting  [env=%s, debug=%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
        settings.DEBUG,
    )
    logger.info("Upload dir : %s", settings.upload_path.resolve())
    logger.info("Reports dir: %s", settings.reports_path.resolve())

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory – builds and returns the configured FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "ReproProof backend API – upload and manage reproducibility artifacts."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS middleware ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ───────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routes ───────────────────────────────────────────────────────────
    app.include_router(router)

    return app


# The ASGI application object used by ``uvicorn app.main:app``
app = create_app()
