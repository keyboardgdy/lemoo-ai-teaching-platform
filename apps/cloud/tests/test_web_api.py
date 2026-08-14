"""Stage 1A Web API contract and boundary behavior."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.entrypoints.api import create_app
from app.modules.control_plane.public import (
    Actor,
    CommandCreation,
    CommandInput,
    CommandView,
    DevicePage,
    DeviceView,
    IdempotencyConflict,
    ResourceNotFound,
)

ORG_A = UUID("0198f001-6000-7000-8000-000000000001")
ORG_B = UUID("0198f001-6000-7000-8000-000000000002")
DEVICE_A = UUID("0198f001-6200-7000-8000-000000000001")
DEVICE_B = UUID("0198f001-6200-7000-8000-000000000002")
COMMAND_ID = UUID("0198f001-6500-7000-8000-000000000001")
IDEMPOTENCY_KEY = UUID("0198f001-5200-7000-8000-000000000001")
NOW = datetime(2026, 8, 14, 2, 0, tzinfo=UTC)


def device_view(*, device_id: UUID = DEVICE_A, organization_id: UUID = ORG_A) -> DeviceView:
    code = "SIM-A-001" if organization_id == ORG_A else "SIM-B-001"
    return DeviceView(
        id=device_id,
        code=code,
        organization_id=organization_id,
        site_id=UUID("0198f001-6100-7000-8000-000000000001"),
        model_code="SIM_EDU_ROBOT_V1",
        hardware_revision="sim-r1",
        lifecycle="active",
        certificate_status="active",
        presence="online",
        last_seen_at=NOW,
        reported_shadow_version=3,
        reported_shadow={"firmware_major": "sim-1"},
        is_synthetic=True,
        is_physical_hardware=False,
        production_supported=False,
    )


def command_view() -> CommandView:
    return CommandView(
        id=COMMAND_ID,
        organization_id=ORG_A,
        device_id=DEVICE_A,
        command_type="refresh_shadow",
        idempotency_key=IDEMPOTENCY_KEY,
        requested_by="USR-SIM-A-OPS-001",
        reason="Refresh the synthetic device shadow",
        expires_at=NOW + timedelta(minutes=2),
        state="approved",
        created_at=NOW,
        updated_at=NOW,
        production_supported=False,
    )


class FakeControlPlane:
    def __init__(self) -> None:
        self.devices = {
            DEVICE_A: device_view(),
            DEVICE_B: device_view(device_id=DEVICE_B, organization_id=ORG_B),
        }
        self.commands: dict[UUID, CommandView] = {}
        self.last_actor: Actor | None = None
        self.last_input: CommandInput | None = None

    async def list_devices(
        self,
        actor: Actor,
        *,
        target_organization_id: UUID | None,
        support_reason: str | None,
        cursor: str | None,
        limit: int,
        request_id: UUID,
        trace_id: str,
    ) -> DevicePage:
        del cursor, limit, support_reason, request_id, trace_id
        self.last_actor = actor
        organization_id = target_organization_id or actor.organization_id
        return DevicePage(
            items=tuple(
                device
                for device in self.devices.values()
                if device.organization_id == organization_id
            ),
            next_cursor=None,
        )

    async def get_device(
        self,
        actor: Actor,
        device_id: UUID,
        *,
        target_organization_id: UUID | None,
        support_reason: str | None,
        request_id: UUID,
        trace_id: str,
    ) -> DeviceView:
        del support_reason, request_id, trace_id
        self.last_actor = actor
        device = self.devices.get(device_id)
        organization_id = target_organization_id or actor.organization_id
        if device is None or device.organization_id != organization_id:
            raise ResourceNotFound("device_not_found")
        return device

    async def create_command(self, actor: Actor, command_input: CommandInput) -> CommandCreation:
        self.last_actor = actor
        self.last_input = command_input
        if self.commands and command_input.reason == "Different request":
            raise IdempotencyConflict("idempotency_key_conflict")
        existing = self.commands.get(command_input.idempotency_key)
        if existing is not None:
            return CommandCreation(command=existing, replayed=True)
        command = command_view()
        self.commands[command_input.idempotency_key] = command
        return CommandCreation(command=command, replayed=False)

    async def get_command(self, actor: Actor, command_id: UUID) -> CommandView:
        self.last_actor = actor
        command = next((value for value in self.commands.values() if value.id == command_id), None)
        if command is None or actor.organization_id != command.organization_id:
            raise ResourceNotFound("command_not_found")
        return command

    async def close(self) -> None:
        return None


@pytest.fixture
def control_plane() -> FakeControlPlane:
    return FakeControlPlane()


@pytest.fixture
async def client(control_plane: FakeControlPlane) -> AsyncGenerator[AsyncClient]:
    application = create_app(Settings(environment="test"), control_plane=control_plane)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


async def authenticate(client: AsyncClient, actor: str = "org_a_operator") -> str:
    response = await client.post("/api/v1/simulator/session", json={"actor": actor})
    assert response.status_code == 201
    csrf_token = client.cookies.get("lemoo_csrf")
    assert csrf_token
    return csrf_token


@pytest.mark.asyncio
async def test_unauthenticated_request_uses_rfc_9457_and_request_id(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/devices")

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert UUID(response.headers["x-request-id"])
    problem = cast(dict[str, object], response.json())
    assert problem["type"] == "https://errors.lemoo.invalid/authentication_required"
    assert problem["code"] == "authentication_required"
    assert problem["request_id"] == response.headers["x-request-id"]


@pytest.mark.asyncio
async def test_simulator_session_cookie_maps_to_fixed_synthetic_actor(
    client: AsyncClient, control_plane: FakeControlPlane
) -> None:
    await authenticate(client)
    session = await client.get("/api/v1/session")
    devices = await client.get("/api/v1/devices")

    assert session.status_code == 200
    assert session.json() == {
        "actor_id": "USR-SIM-A-OPS-001",
        "organization_id": str(ORG_A),
        "roles": ["device_operator"],
        "simulator_only": True,
        "production_supported": False,
    }
    assert [item["code"] for item in devices.json()["items"]] == ["SIM-A-001"]
    assert control_plane.last_actor is not None
    assert control_plane.last_actor.organization_id == ORG_A


@pytest.mark.asyncio
async def test_cross_tenant_and_unknown_devices_have_the_same_404_shape(
    client: AsyncClient,
) -> None:
    await authenticate(client)

    cross_tenant = await client.get(f"/api/v1/devices/{DEVICE_B}")
    unknown = await client.get("/api/v1/devices/0198f001-6200-7000-8000-000000000099")

    assert cross_tenant.status_code == unknown.status_code == 404
    assert cross_tenant.json()["code"] == unknown.json()["code"] == "resource_not_found"
    assert "SIM-B" not in cross_tenant.text


@pytest.mark.asyncio
async def test_command_requires_csrf_and_is_idempotent(client: AsyncClient) -> None:
    csrf_token = await authenticate(client)
    body: dict[str, object] = {
        "device_id": str(DEVICE_A),
        "command_type": "refresh_shadow",
        "reason": "Refresh the synthetic device shadow",
        "expires_at": (NOW + timedelta(minutes=2)).isoformat(),
        "parameters": {},
    }
    headers = {
        "Idempotency-Key": str(IDEMPOTENCY_KEY),
        "X-CSRF-Token": csrf_token,
    }

    rejected = await client.post(
        "/api/v1/device-commands", json=body, headers=headers | {"X-CSRF-Token": "wrong"}
    )
    first = await client.post("/api/v1/device-commands", json=body, headers=headers)
    replay = await client.post("/api/v1/device-commands", json=body, headers=headers)

    assert rejected.status_code == 403
    assert rejected.json()["code"] == "csrf_validation_failed"
    assert first.status_code == 202
    assert first.headers["location"] == f"/api/v1/device-commands/{COMMAND_ID}"
    assert first.json()["id"] == replay.json()["id"] == str(COMMAND_ID)
    assert replay.status_code == 200
    assert replay.headers["idempotency-replayed"] == "true"


@pytest.mark.asyncio
async def test_reused_idempotency_key_with_different_request_is_conflict(
    client: AsyncClient,
) -> None:
    csrf_token = await authenticate(client)
    headers = {
        "Idempotency-Key": str(IDEMPOTENCY_KEY),
        "X-CSRF-Token": csrf_token,
    }
    base: dict[str, object] = {
        "device_id": str(DEVICE_A),
        "command_type": "refresh_shadow",
        "expires_at": (NOW + timedelta(minutes=2)).isoformat(),
        "parameters": {},
    }
    await client.post(
        "/api/v1/device-commands",
        json=base | {"reason": "Refresh the synthetic device shadow"},
        headers=headers,
    )
    conflict = await client.post(
        "/api/v1/device-commands",
        json=base | {"reason": "Different request"},
        headers=headers,
    )

    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_key_conflict"


@pytest.mark.asyncio
async def test_validation_errors_are_problem_details(client: AsyncClient) -> None:
    await authenticate(client)
    response = await client.get("/api/v1/devices?limit=0")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "request_validation_failed"


def test_openapi_exposes_only_the_stage_1a_web_surface(
    control_plane: FakeControlPlane,
) -> None:
    schema = create_app(Settings(environment="test"), control_plane=control_plane).openapi()

    assert set(schema["paths"]) == {
        "/health/live",
        "/health/ready",
        "/api/v1/simulator/session",
        "/api/v1/session",
        "/api/v1/devices",
        "/api/v1/devices/{device_id}",
        "/api/v1/device-commands",
        "/api/v1/device-commands/{command_id}",
    }
    assert "/api/v1/ota-releases" not in schema["paths"]
    assert schema["info"]["description"].startswith("Stage 1A Simulator-only")
    error_responses = [
        response
        for path in schema["paths"].values()
        for operation in path.values()
        for status, response in operation.get("responses", {}).items()
        if int(status) >= 400
    ]
    assert error_responses
    assert all(
        set(response["content"]) == {"application/problem+json"} for response in error_responses
    )
