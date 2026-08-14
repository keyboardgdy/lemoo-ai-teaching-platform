"""FastAPI routes for the Stage 1A synthetic Web control plane."""

import secrets
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, Response
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.entrypoints.problems import ProblemException
from app.entrypoints.web_auth import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    SIMULATOR_IDENTITIES,
    SimulatorActorKey,
    actor_for_session,
)
from app.modules.control_plane.public import (
    AccessDenied,
    Actor,
    CommandInput,
    CommandView,
    ControlPlane,
    DevicePage,
    DeviceView,
    IdempotencyConflict,
    InvalidCursor,
    OperationRejected,
    ResourceNotFound,
)

SESSION_SECURITY = APIKeyCookie(name=SESSION_COOKIE, auto_error=False)


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str
    request_id: str


PROBLEM_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetail, "description": "Authentication required"},
    403: {"model": ProblemDetail, "description": "Operation denied"},
    404: {"model": ProblemDetail, "description": "Resource not found"},
    409: {"model": ProblemDetail, "description": "Request conflict"},
    422: {"model": ProblemDetail, "description": "Request validation failed"},
}


class SimulatorSessionRequest(BaseModel):
    actor: SimulatorActorKey


class SessionResponse(BaseModel):
    actor_id: str
    organization_id: UUID | None
    roles: list[str]
    simulator_only: Literal[True] = True
    production_supported: Literal[False] = False

    @classmethod
    def from_actor(cls, actor: Actor) -> SessionResponse:
        return cls(
            actor_id=actor.actor_id,
            organization_id=actor.organization_id,
            roles=sorted(role.value for role in actor.roles),
        )


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    organization_id: UUID
    site_id: UUID | None
    model_code: str
    hardware_revision: str
    lifecycle: str
    certificate_status: str
    presence: str
    last_seen_at: datetime | None
    reported_shadow_version: int
    reported_shadow: dict[str, object]
    is_synthetic: Literal[True]
    is_physical_hardware: Literal[False]
    production_supported: Literal[False]

    @classmethod
    def from_view(cls, device: DeviceView) -> DeviceResponse:
        return cls.model_validate(device)


class DevicePageResponse(BaseModel):
    items: list[DeviceResponse]
    next_cursor: str | None

    @classmethod
    def from_page(cls, page: DevicePage) -> DevicePageResponse:
        return cls(
            items=[DeviceResponse.from_view(item) for item in page.items],
            next_cursor=page.next_cursor,
        )


class CreateCommandRequest(BaseModel):
    device_id: UUID
    command_type: Literal["refresh_shadow"]
    reason: str = Field(min_length=3, max_length=240)
    expires_at: datetime
    parameters: dict[str, object] = Field(default_factory=dict)

    @field_validator("parameters")
    @classmethod
    def parameters_are_empty(cls, value: dict[str, object]) -> dict[str, object]:
        if value:
            raise ValueError("parameters_not_allowed")
        return value

    @field_validator("expires_at")
    @classmethod
    def expiry_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timezone_required")
        return value


class CommandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    device_id: UUID
    command_type: Literal["refresh_shadow"]
    idempotency_key: UUID
    requested_by: str
    reason: str
    expires_at: datetime
    state: str
    created_at: datetime
    updated_at: datetime
    production_supported: Literal[False]

    @classmethod
    def from_view(cls, command: CommandView) -> CommandResponse:
        return cls.model_validate(command)


def _not_found() -> ProblemException:
    return ProblemException(
        status=404,
        code="resource_not_found",
        title="Resource not found",
        detail="The requested resource is unavailable.",
    )


def _map_control_error(exception: Exception) -> ProblemException:
    if isinstance(exception, ResourceNotFound):
        return _not_found()
    if isinstance(exception, IdempotencyConflict):
        return ProblemException(
            status=409,
            code="idempotency_key_conflict",
            title="Idempotency conflict",
            detail="The idempotency key was already used for a different request.",
        )
    if isinstance(exception, InvalidCursor):
        return ProblemException(
            status=422,
            code="invalid_cursor",
            title="Invalid cursor",
            detail="The pagination cursor is invalid or expired.",
        )
    if isinstance(exception, AccessDenied):
        if str(exception) == "resource_not_available":
            return _not_found()
        return ProblemException(
            status=403,
            code="permission_denied",
            title="Permission denied",
            detail="The authenticated actor cannot perform this operation.",
        )
    if isinstance(exception, OperationRejected):
        conflict_codes = {
            "device_not_active",
            "device_not_online",
            "device_certificate_not_active",
        }
        status = 409 if exception.code in conflict_codes else 422
        return ProblemException(
            status=status,
            code=exception.code,
            title="Operation rejected",
            detail="The request violates the Stage 1A command policy.",
        )
    raise exception


def create_web_router(control_plane: ControlPlane) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    async def authenticated_actor(
        session_id: Annotated[str | None, Depends(SESSION_SECURITY)],
    ) -> Actor:
        actor = actor_for_session(session_id)
        if actor is None:
            raise ProblemException(
                status=401,
                code="authentication_required",
                title="Authentication required",
                detail="A valid synthetic simulator session is required.",
            )
        return actor

    async def csrf_protected(
        csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_COOKIE)] = None,
        csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
    ) -> None:
        if (
            csrf_cookie is None
            or csrf_header is None
            or not secrets.compare_digest(csrf_cookie, csrf_header)
        ):
            raise ProblemException(
                status=403,
                code="csrf_validation_failed",
                title="CSRF validation failed",
                detail="The CSRF token is missing or invalid.",
            )

    @router.post(
        "/simulator/session",
        response_model=SessionResponse,
        status_code=201,
        tags=["simulator-session"],
        responses={422: PROBLEM_RESPONSES[422]},
    )
    async def create_simulator_session(  # pyright: ignore[reportUnusedFunction]
        payload: SimulatorSessionRequest, response: Response
    ) -> SessionResponse:
        identity = SIMULATOR_IDENTITIES[payload.actor]
        csrf_token = secrets.token_urlsafe(32)
        response.set_cookie(
            SESSION_COOKIE,
            identity.session_id,
            httponly=True,
            secure=False,
            samesite="strict",
            max_age=8 * 60 * 60,
            path="/",
        )
        response.set_cookie(
            CSRF_COOKIE,
            csrf_token,
            httponly=False,
            secure=False,
            samesite="strict",
            max_age=8 * 60 * 60,
            path="/",
        )
        return SessionResponse.from_actor(identity.actor)

    @router.get(
        "/session",
        response_model=SessionResponse,
        tags=["session"],
        responses={401: PROBLEM_RESPONSES[401]},
    )
    async def get_session(  # pyright: ignore[reportUnusedFunction]
        actor: Annotated[Actor, Depends(authenticated_actor)],
    ) -> SessionResponse:
        return SessionResponse.from_actor(actor)

    @router.delete(
        "/session",
        status_code=204,
        tags=["session"],
        responses={401: PROBLEM_RESPONSES[401], 403: PROBLEM_RESPONSES[403]},
    )
    async def delete_session(  # pyright: ignore[reportUnusedFunction]
        response: Response,
        _: Annotated[Actor, Depends(authenticated_actor)],
        __: Annotated[None, Depends(csrf_protected)],
    ) -> None:
        response.delete_cookie(SESSION_COOKIE, path="/")
        response.delete_cookie(CSRF_COOKIE, path="/")

    @router.get(
        "/devices",
        response_model=DevicePageResponse,
        tags=["devices"],
        responses=PROBLEM_RESPONSES,
    )
    async def list_devices(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        actor: Annotated[Actor, Depends(authenticated_actor)],
        organization_id: Annotated[UUID | None, Query()] = None,
        support_reason: Annotated[str | None, Header(alias="X-Support-Reason")] = None,
        cursor: Annotated[str | None, Query(max_length=512)] = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
    ) -> DevicePageResponse:
        try:
            page = await control_plane.list_devices(
                actor,
                target_organization_id=organization_id,
                support_reason=support_reason,
                cursor=cursor,
                limit=limit,
                request_id=request.state.request_id,
                trace_id=str(request.state.request_id),
            )
        except (AccessDenied, InvalidCursor) as exception:
            raise _map_control_error(exception) from exception
        return DevicePageResponse.from_page(page)

    @router.get(
        "/devices/{device_id}",
        response_model=DeviceResponse,
        tags=["devices"],
        responses=PROBLEM_RESPONSES,
    )
    async def get_device(  # pyright: ignore[reportUnusedFunction]
        device_id: UUID,
        request: Request,
        actor: Annotated[Actor, Depends(authenticated_actor)],
        organization_id: Annotated[UUID | None, Query()] = None,
        support_reason: Annotated[str | None, Header(alias="X-Support-Reason")] = None,
    ) -> DeviceResponse:
        try:
            device = await control_plane.get_device(
                actor,
                device_id,
                target_organization_id=organization_id,
                support_reason=support_reason,
                request_id=request.state.request_id,
                trace_id=str(request.state.request_id),
            )
        except (AccessDenied, ResourceNotFound) as exception:
            raise _map_control_error(exception) from exception
        return DeviceResponse.from_view(device)

    @router.post(
        "/device-commands",
        response_model=CommandResponse,
        status_code=202,
        tags=["device-commands"],
        responses=PROBLEM_RESPONSES,
    )
    async def create_command(  # pyright: ignore[reportUnusedFunction]
        payload: CreateCommandRequest,
        request: Request,
        response: Response,
        actor: Annotated[Actor, Depends(authenticated_actor)],
        _: Annotated[None, Depends(csrf_protected)],
        idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    ) -> CommandResponse:
        command_input = CommandInput(
            device_id=payload.device_id,
            command_type=payload.command_type,
            idempotency_key=idempotency_key,
            reason=payload.reason,
            expires_at=payload.expires_at,
            parameters=payload.parameters,
            request_id=request.state.request_id,
            trace_id=str(request.state.request_id),
        )
        try:
            creation = await control_plane.create_command(actor, command_input)
        except (
            AccessDenied,
            IdempotencyConflict,
            OperationRejected,
            ResourceNotFound,
        ) as exception:
            raise _map_control_error(exception) from exception
        response.headers["Location"] = f"/api/v1/device-commands/{creation.command.id}"
        if creation.replayed:
            response.status_code = 200
            response.headers["Idempotency-Replayed"] = "true"
        return CommandResponse.from_view(creation.command)

    @router.get(
        "/device-commands/{command_id}",
        response_model=CommandResponse,
        tags=["device-commands"],
        responses=PROBLEM_RESPONSES,
    )
    async def get_command(  # pyright: ignore[reportUnusedFunction]
        command_id: UUID,
        actor: Annotated[Actor, Depends(authenticated_actor)],
    ) -> CommandResponse:
        try:
            command = await control_plane.get_command(actor, command_id)
        except (AccessDenied, ResourceNotFound) as exception:
            raise _map_control_error(exception) from exception
        return CommandResponse.from_view(command)

    return router
