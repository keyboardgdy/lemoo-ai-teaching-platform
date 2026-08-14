"""Pure `refresh_shadow` command policy, state, ACK, and idempotency rules."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID

from app.modules.device_fleet.public import DeviceControlSnapshot


class CommandState(StrEnum):
    CREATED = "created"
    APPROVED = "approved"
    PUBLISHED = "published"
    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class CommandPolicyViolation(Exception):
    """A request was rejected before creating or changing a command fact."""


class CommandTransitionRejected(Exception):
    """A command attempted a transition outside the frozen state machine."""


ALLOWED_TRANSITIONS: dict[CommandState, frozenset[CommandState]] = {
    CommandState.CREATED: frozenset(
        {CommandState.APPROVED, CommandState.CANCELLED, CommandState.EXPIRED}
    ),
    CommandState.APPROVED: frozenset(
        {CommandState.PUBLISHED, CommandState.CANCELLED, CommandState.EXPIRED}
    ),
    CommandState.PUBLISHED: frozenset(
        {CommandState.ACCEPTED, CommandState.EXPIRED, CommandState.TIMED_OUT}
    ),
    CommandState.ACCEPTED: frozenset(
        {CommandState.RUNNING, CommandState.FAILED, CommandState.TIMED_OUT}
    ),
    CommandState.RUNNING: frozenset(
        {CommandState.SUCCEEDED, CommandState.FAILED, CommandState.TIMED_OUT}
    ),
    CommandState.SUCCEEDED: frozenset(),
    CommandState.FAILED: frozenset(),
    CommandState.TIMED_OUT: frozenset(),
    CommandState.EXPIRED: frozenset(),
    CommandState.CANCELLED: frozenset(),
}
TERMINAL_STATES = frozenset(
    {
        CommandState.SUCCEEDED,
        CommandState.FAILED,
        CommandState.TIMED_OUT,
        CommandState.EXPIRED,
        CommandState.CANCELLED,
    }
)


@dataclass(frozen=True, slots=True)
class CommandRequest:
    organization_id: UUID
    device_id: UUID
    idempotency_key: UUID
    requested_by: str
    reason: str
    expires_at: datetime
    parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


def _request_fingerprint(request: CommandRequest) -> str:
    canonical = json.dumps(
        {
            "organization_id": str(request.organization_id),
            "device_id": str(request.device_id),
            "command_type": "refresh_shadow",
            "requested_by": request.requested_by,
            "reason": request.reason,
            "expires_at": request.expires_at.isoformat(),
            "parameters": dict(request.parameters),
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class DeviceCommand:
    id: UUID
    organization_id: UUID
    device_id: UUID
    command_type: str
    idempotency_key: UUID
    request_fingerprint: str
    requested_by: str
    reason: str
    parameters: Mapping[str, Any]
    expires_at: datetime
    state: CommandState
    created_at: datetime
    updated_at: datetime
    production_supported: bool = False

    def transition(self, target: CommandState, *, at: datetime) -> DeviceCommand:
        if target is self.state:
            return self
        if target not in ALLOWED_TRANSITIONS[self.state]:
            raise CommandTransitionRejected(f"{self.state.value}_to_{target.value}")
        return replace(self, state=target, updated_at=at)

    def observe_ack(self, target: CommandState, *, at: datetime) -> tuple[DeviceCommand, bool]:
        """Apply a legal ACK without allowing a late ACK to regress a terminal fact."""

        if self.state in TERMINAL_STATES:
            return self, False
        return self.transition(target, at=at), target is not self.state


def create_refresh_shadow(
    *,
    command_id: UUID,
    request: CommandRequest,
    device: DeviceControlSnapshot,
    now: datetime,
) -> DeviceCommand:
    """Validate every control invariant before a command fact can exist."""

    if request.device_id != device.device_id:
        raise CommandPolicyViolation("device_identity_mismatch")
    if request.organization_id != device.organization_id:
        raise CommandPolicyViolation("device_organization_mismatch")
    if device.lifecycle != "active":
        raise CommandPolicyViolation("device_not_active")
    if device.presence != "online":
        raise CommandPolicyViolation("device_not_online")
    if device.certificate_status != "active":
        raise CommandPolicyViolation("device_certificate_not_active")
    if request.expires_at <= now:
        raise CommandPolicyViolation("command_already_expired")
    if request.expires_at > now + timedelta(minutes=5):
        raise CommandPolicyViolation("command_expiry_too_far")
    reason = request.reason.strip()
    if len(reason) < 3 or len(reason) > 240:
        raise CommandPolicyViolation("reason_invalid")
    if request.parameters:
        raise CommandPolicyViolation("parameters_not_allowed")

    return DeviceCommand(
        id=command_id,
        organization_id=request.organization_id,
        device_id=request.device_id,
        command_type="refresh_shadow",
        idempotency_key=request.idempotency_key,
        request_fingerprint=_request_fingerprint(request),
        requested_by=request.requested_by,
        reason=reason,
        parameters=MappingProxyType({}),
        expires_at=request.expires_at,
        state=CommandState.CREATED,
        created_at=now,
        updated_at=now,
    )


def resolve_idempotent_request(existing: DeviceCommand, request: CommandRequest) -> DeviceCommand:
    """Return one existing fact only if a reused key represents the same request."""

    if existing.idempotency_key != request.idempotency_key:
        raise CommandPolicyViolation("idempotency_key_not_found")
    if existing.request_fingerprint != _request_fingerprint(request):
        raise CommandPolicyViolation("idempotency_key_conflict")
    return existing
