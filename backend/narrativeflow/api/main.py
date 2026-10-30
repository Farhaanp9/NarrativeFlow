"""FastAPI application factory and configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from narrativeflow import __version__
from narrativeflow.config import get_settings
from narrativeflow.storage.database import fail_interrupted_simulations, init_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Initialize database on startup."""
    settings = get_settings()
    await init_db(settings.db_path)
    logger.info("database_initialized", db_path=str(settings.db_path))
    interrupted = await fail_interrupted_simulations(settings.db_path)
    if interrupted:
        logger.info("interrupted_simulations_failed", count=interrupted)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="NarrativeFlow",
        description="Multi-agent simulation engine for modeling misinformation spread",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from narrativeflow.api.routes.reports import router as reports_router
    from narrativeflow.api.routes.simulations import (
        router as simulations_router,
    )
    from narrativeflow.api.routes.ws import router as ws_router

    app.include_router(simulations_router)
    app.include_router(reports_router)
    app.include_router(ws_router)

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
