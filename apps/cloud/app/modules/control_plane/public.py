"""Framework-neutral application port and DTOs for the Stage 1A Web API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.identity.public import Actor


class ResourceNotFound(Exception):
    """A resource is absent or intentionally hidden from this actor."""


class AccessDenied(Exception):
    """The authenticated actor cannot perform an operation."""


class IdempotencyConflict(Exception):
    """An idempotency key was reused for a different request."""


class OperationRejected(Exception):
    """A request violated a stable control-plane policy."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class InvalidCursor(Exception):
    """A list cursor cannot be decoded or does not belong to this endpoint."""


@dataclass(frozen=True, slots=True)
class DeviceView:
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
    reported_shadow: Mapping[str, object]
    is_synthetic: bool
    is_physical_hardware: bool
    production_supported: bool


@dataclass(frozen=True, slots=True)
class DevicePage:
    items: tuple[DeviceView, ...]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class CommandInput:
    device_id: UUID
    command_type: str
    idempotency_key: UUID
    reason: str
    expires_at: datetime
    parameters: Mapping[str, object]
    request_id: UUID
    trace_id: str


@dataclass(frozen=True, slots=True)
class CommandView:
    id: UUID
    organization_id: UUID
    device_id: UUID
    command_type: str
    idempotency_key: UUID
    requested_by: str
    reason: str
    expires_at: datetime
    state: str
    created_at: datetime
    updated_at: datetime
    production_supported: bool


@dataclass(frozen=True, slots=True)
class CommandCreation:
    command: CommandView
    replayed: bool


class ControlPlane(Protocol):
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
    ) -> DevicePage: ...

    async def get_device(
        self,
        actor: Actor,
        device_id: UUID,
        *,
        target_organization_id: UUID | None,
        support_reason: str | None,
        request_id: UUID,
        trace_id: str,
    ) -> DeviceView: ...

    async def create_command(
        self, actor: Actor, command_input: CommandInput
    ) -> CommandCreation: ...

    async def get_command(self, actor: Actor, command_id: UUID) -> CommandView: ...

    async def close(self) -> None: ...


__all__ = [
    "AccessDenied",
    "Actor",
    "CommandCreation",
    "CommandInput",
    "CommandView",
    "ControlPlane",
    "DevicePage",
    "DeviceView",
    "IdempotencyConflict",
    "InvalidCursor",
    "OperationRejected",
    "ResourceNotFound",
]
