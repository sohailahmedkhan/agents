"""FastAPI application factory and top-level wiring.

Creates the ASGI app, applies global middleware, registers common health/root
routes, and mounts feature routers from the API layer.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents.dependencies import get_agents_service
from app.api.agents.router import router as agents_router
from app.core.settings import AppSettings

logger = logging.getLogger(__name__)


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    resolved = settings or AppSettings.from_env()

    app = FastAPI(
        title=resolved.title,
        version=resolved.version,
        description=resolved.description,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Simple health endpoint for service liveness checks."""
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Agents API is running"}

    @app.on_event("startup")
    async def on_startup() -> None:
        service = get_agents_service()
        await service.startup()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        try:
            service = get_agents_service()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not resolve agents service on shutdown: %s", exc)
            return
        await service.shutdown()

    app.include_router(agents_router)
    return app


app = create_app()
