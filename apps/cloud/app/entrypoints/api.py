"""FastAPI composition root for the Stage 1A Simulator-only control plane."""

import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast
from uuid import uuid7

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app import __version__
from app.config import Settings, get_settings
from app.entrypoints.problems import (
    ProblemException,
    problem_exception_handler,
    validation_exception_handler,
)
from app.entrypoints.web import create_web_router
from app.infrastructure.database.control_plane import PostgresControlPlane
from app.modules.control_plane.public import ControlPlane


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
            mode="simulator-only",
        )

    async def ready() -> HealthResponse:
        return HealthResponse(
            status="ready",
            service=settings.service_name,
            version=settings.service_version,
            environment=settings.environment,
            mode="simulator-only",
        )

    router.add_api_route("/live", live, methods=["GET"], response_model=HealthResponse)
    router.add_api_route("/ready", ready, methods=["GET"], response_model=HealthResponse)
    return router


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach one server-issued request identifier to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = uuid7()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(request_id)
        return response


def _normalize_problem_contract(schema: dict[str, Any]) -> None:
    """Describe every HTTP error with the same RFC 9457 media type and schema."""

    paths = cast(dict[str, dict[str, dict[str, Any]]], schema.get("paths", {}))
    for path_item in paths.values():
        for operation in path_item.values():
            responses = cast(dict[str, dict[str, Any]], operation.get("responses", {}))
            for status, response in responses.items():
                if int(status) < 400:
                    continue
                response["content"] = {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/ProblemDetail"}
                    }
                }


def create_app(
    settings: Settings | None = None,
    *,
    control_plane: ControlPlane | None = None,
) -> FastAPI:
    """Create an isolated FastAPI application without infrastructure side effects."""

    effective_settings = settings or get_settings()
    if effective_settings.enabled_future_capabilities:
        enabled = ", ".join(effective_settings.enabled_future_capabilities)
        msg = f"Capabilities are not approved for W2: {enabled}"
        raise RuntimeError(msg)

    effective_control_plane = control_plane or PostgresControlPlane(effective_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        try:
            yield
        finally:
            await effective_control_plane.close()

    application = FastAPI(
        title="Lemoo Education Robot Cloud",
        description=(
            "Stage 1A Simulator-only synthetic device control plane; production unsupported."
        ),
        version=__version__,
        openapi_version="3.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=effective_settings.allowed_hosts,
    )
    application.add_middleware(RequestIdMiddleware)
    application.add_exception_handler(ProblemException, problem_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.include_router(_health_router(effective_settings))
    application.include_router(create_web_router(effective_control_plane))
    default_openapi = application.openapi

    def stage1a_openapi() -> dict[str, Any]:
        schema = default_openapi()
        _normalize_problem_contract(schema)
        return schema

    application.openapi = stage1a_openapi
    return application


app = create_app()


def run() -> None:
    """Run the local development API."""

    config = uvicorn.Config(
        "app.entrypoints.api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        access_log=False,
    )
    server = uvicorn.Server(config)
    if sys.platform == "win32":
        # Psycopg async explicitly does not support Windows' ProactorEventLoop.
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
        return
    server.run()
