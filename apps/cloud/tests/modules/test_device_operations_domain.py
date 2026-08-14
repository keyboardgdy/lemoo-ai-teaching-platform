"""Pure refresh-shadow creation, idempotency, expiry, and ACK rules."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.modules.device_fleet.public import DeviceControlSnapshot
from app.modules.device_operations.domain import (
    CommandPolicyViolation,
    CommandRequest,
    CommandState,
    CommandTransitionRejected,
    create_refresh_shadow,
    resolve_idempotent_request,
)

ORG_A = UUID("0198f001-6000-7000-8000-000000000001")
ORG_B = UUID("0198f001-6000-7000-8000-000000000002")
DEVICE_ID = UUID("0198f001-6200-7000-8000-000000000001")
COMMAND_ID = UUID("0198f001-6300-7000-8000-000000000001")
KEY = UUID("0198f001-6400-7000-8000-000000000001")
NOW = datetime(2026, 8, 14, 1, 0, tzinfo=UTC)


def online_device() -> DeviceControlSnapshot:
    return DeviceControlSnapshot(
        device_id=DEVICE_ID,
        organization_id=ORG_A,
        lifecycle="active",
        presence="online",
        certificate_status="active",
    )


def request(**overrides: object) -> CommandRequest:
    values: dict[str, object] = {
        "organization_id": ORG_A,
        "device_id": DEVICE_ID,
        "idempotency_key": KEY,
        "requested_by": "USR-SIM-OPS-A",
        "reason": "Refresh the reported simulator shadow",
        "expires_at": NOW + timedelta(seconds=30),
        "parameters": {},
    }
    values.update(overrides)
    return CommandRequest(**values)  # type: ignore[arg-type]


def test_valid_request_creates_only_the_allowlisted_command() -> None:
    command = create_refresh_shadow(
        command_id=COMMAND_ID,
        request=request(),
        device=online_device(),
        now=NOW,
    )

    assert command.command_type == "refresh_shadow"
    assert command.state is CommandState.CREATED
    assert command.parameters == {}
    assert command.production_supported is False


@pytest.mark.parametrize(
    ("device", "request_overrides", "error"),
    [
        (
            DeviceControlSnapshot(
                device_id=DEVICE_ID,
                organization_id=ORG_A,
                lifecycle="active",
                presence="offline",
                certificate_status="active",
            ),
            {},
            "device_not_online",
        ),
        (online_device(), {"expires_at": NOW}, "command_already_expired"),
        (online_device(), {"organization_id": ORG_B}, "device_organization_mismatch"),
        (online_device(), {"parameters": {"shell": "no"}}, "parameters_not_allowed"),
    ],
)
def test_invalid_request_is_rejected_before_any_command_exists(
    device: DeviceControlSnapshot,
    request_overrides: dict[str, object],
    error: str,
) -> None:
    with pytest.raises(CommandPolicyViolation, match=error):
        create_refresh_shadow(
            command_id=COMMAND_ID,
            request=request(**request_overrides),
            device=device,
            now=NOW,
        )


def test_command_transitions_are_explicit_and_terminal_states_do_not_regress() -> None:
    created = create_refresh_shadow(
        command_id=COMMAND_ID,
        request=request(),
        device=online_device(),
        now=NOW,
    )
    approved = created.transition(CommandState.APPROVED, at=NOW)
    published = approved.transition(CommandState.PUBLISHED, at=NOW)
    accepted, applied = published.observe_ack(CommandState.ACCEPTED, at=NOW)
    running, _ = accepted.observe_ack(CommandState.RUNNING, at=NOW)
    succeeded, _ = running.observe_ack(CommandState.SUCCEEDED, at=NOW)
    unchanged, late_applied = succeeded.observe_ack(CommandState.RUNNING, at=NOW)

    assert applied is True
    assert succeeded.state is CommandState.SUCCEEDED
    assert unchanged is succeeded
    assert late_applied is False
    with pytest.raises(CommandTransitionRejected, match="created_to_succeeded"):
        created.transition(CommandState.SUCCEEDED, at=NOW)


def test_same_idempotency_key_reuses_only_an_identical_request() -> None:
    original_request = request()
    existing = create_refresh_shadow(
        command_id=COMMAND_ID,
        request=original_request,
        device=online_device(),
        now=NOW,
    )

    assert resolve_idempotent_request(existing, original_request) is existing
    with pytest.raises(CommandPolicyViolation, match="idempotency_key_conflict"):
        resolve_idempotent_request(
            existing,
            request(reason="A different business request"),
        )
