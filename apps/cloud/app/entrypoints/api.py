"""FastAPI composition root for the W2 health-only skeleton."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel

from app import __version__
from app.config import Settings, get_settings


class HealthResponse(BaseModel):
    """Stable, non-sensitive process health response."""

    status: str
    service: str
    version: str
    environment: str
    mode: str


def _health_router(settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])

    async def live() -> HealthResponse:
        return HealthResponse(
            status="alive",
            service=settings.service_name,
            version=settings.service_version,
            environment=settings.environment,
            mode="skeleton",
        )

    async def ready() -> HealthResponse:
        return HealthResponse(
            status="ready",
            service=settings.service_name,
            version=settings.service_version,
            environment=settings.environment,
            mode="skeleton",
        )

    router.add_api_route("/live", live, methods=["GET"], response_model=HealthResponse)
    router.add_api_route("/ready", ready, methods=["GET"], response_model=HealthResponse)
    return router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an isolated FastAPI application without infrastructure side effects."""

    effective_settings = settings or get_settings()
    if effective_settings.enabled_future_capabilities:
        enabled = ", ".join(effective_settings.enabled_future_capabilities)
        msg = f"Capabilities are not approved for W2: {enabled}"
        raise RuntimeError(msg)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        yield

    application = FastAPI(
        title="Lemoo Education Robot Cloud",
        description="Stage 1A non-production skeleton; no business API is enabled.",
        version=__version__,
        openapi_version="3.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=effective_settings.allowed_hosts,
    )
    application.include_router(_health_router(effective_settings))
    return application


app = create_app()


def run() -> None:
    """Run the local development API."""

    uvicorn.run(
        "app.entrypoints.api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        access_log=False,
    )
