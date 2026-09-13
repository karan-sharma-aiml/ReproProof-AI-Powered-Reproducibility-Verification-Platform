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
from app.api.agent_routes import router as agent_router
from app.api.devops_routes import router as devops_router
from app.api.showcase_routes import router as showcase_router
from app.api.research_routes import router as research_router
from app.api.paper_routes import router as paper_router
from app.api.execution_routes import router as execution_engine_router
from app.api.judge_routes import router as judge_router
from app.api.memory_routes import router as memory_router
from app.api.observability_routes import router as observability_router
from app.api.deployment_routes import router as deployment_router
from app.api.provider_routes import router as provider_router
from app.api.orchestrator_routes import router as orchestrator_router
from app.api.knowledge_routes import router as knowledge_router
from app.api.rag_routes import router as rag_router
from app.api.performance_routes import router as performance_router
from app.api.demo_routes import router as demo_router
from app.api.infrastructure_routes import router as infrastructure_router
from app.api.monitoring_routes import router as monitoring_router
from app.api.github_routes import router as github_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.devops.middleware import install_devops_middleware
from app.security.middleware import install_security_middleware
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
    from app.integrations.composition import provider_manager

    provider_status = provider_manager.startup_status()
    logger.info(
        "AI provider default=%s configured=%s",
        provider_status["default_provider"],
        provider_status["configured"],
    )

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
    install_devops_middleware(app)
    install_security_middleware(app)

    # ── Exception handlers ───────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routes ───────────────────────────────────────────────────────────
    app.include_router(router)
    app.include_router(research_router)
    app.include_router(paper_router)
    app.include_router(execution_engine_router)
    app.include_router(judge_router)
    app.include_router(memory_router)
    app.include_router(agent_router)
    app.include_router(devops_router)
    app.include_router(showcase_router)
    app.include_router(observability_router)
    app.include_router(deployment_router)
    app.include_router(provider_router)
    app.include_router(orchestrator_router)
    app.include_router(knowledge_router)
    app.include_router(rag_router)
    app.include_router(performance_router)
    app.include_router(demo_router)
    app.include_router(infrastructure_router)
    app.include_router(monitoring_router)
    app.include_router(github_router)

    return app


# The ASGI application object used by ``uvicorn app.main:app``
app = create_app()
