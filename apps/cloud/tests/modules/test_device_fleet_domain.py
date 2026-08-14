"""Pure lifecycle, presence, ordering, and reported-shadow rules."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.modules.device_fleet.domain import (
    CertificateStatus,
    Device,
    DeviceLifecycle,
    IllegalDeviceTransition,
    PresenceStatus,
    SequenceDecision,
    StaleShadowVersion,
    classify_sequence,
)

ORG_A = UUID("0198f001-6000-7000-8000-000000000001")
SITE_A = UUID("0198f001-6100-7000-8000-000000000001")
DEVICE_ID = UUID("0198f001-6200-7000-8000-000000000001")
NOW = datetime(2026, 8, 14, 1, 0, tzinfo=UTC)


def inventory_device() -> Device:
    return Device(
        id=DEVICE_ID,
        code="SIM-A-001",
        serial_number="LEMO-SIM-A-001",
        model_code="LEMO-SIM-V1",
        hardware_revision="sim-r1",
        lifecycle=DeviceLifecycle.INVENTORY,
        certificate_status=CertificateStatus.ACTIVE,
    )


def test_binding_and_activation_follow_the_only_legal_path() -> None:
    device = inventory_device()

    assigned = device.bind(organization_id=ORG_A, site_id=SITE_A, at=NOW)
    active = assigned.transition(DeviceLifecycle.ACTIVE, at=NOW)

    assert assigned.lifecycle is DeviceLifecycle.ASSIGNED
    assert active.lifecycle is DeviceLifecycle.ACTIVE
    assert active.organization_id == ORG_A
    assert active.site_id == SITE_A
    assert active.is_synthetic is True
    assert active.is_physical_hardware is False
    assert active.production_supported is False


def test_illegal_lifecycle_transition_preserves_the_original_device() -> None:
    device = inventory_device()

    with pytest.raises(IllegalDeviceTransition, match="inventory_to_active"):
        device.transition(DeviceLifecycle.ACTIVE, at=NOW)

    assert device.lifecycle is DeviceLifecycle.INVENTORY
    assert device.organization_id is None


@pytest.mark.parametrize(
    ("current_boot", "current_sequence", "incoming_boot", "incoming_sequence", "expected"),
    [
        (None, None, "boot-0001", 0, SequenceDecision.ACCEPT),
        ("boot-0001", 4, "boot-0001", 5, SequenceDecision.ACCEPT),
        ("boot-0001", 5, "boot-0001", 5, SequenceDecision.DUPLICATE),
        ("boot-0001", 5, "boot-0001", 4, SequenceDecision.OUT_OF_ORDER),
        ("boot-0001", 100, "boot-0002", 0, SequenceDecision.NEW_BOOT),
    ],
)
def test_sequence_decisions_are_deterministic(
    current_boot: str | None,
    current_sequence: int | None,
    incoming_boot: str,
    incoming_sequence: int,
    expected: SequenceDecision,
) -> None:
    assert (
        classify_sequence(
            current_boot=current_boot,
            current_sequence=current_sequence,
            incoming_boot=incoming_boot,
            incoming_sequence=incoming_sequence,
        )
        is expected
    )


def test_reported_shadow_is_monotonic_and_duplicate_is_idempotent() -> None:
    device = inventory_device().bind(organization_id=ORG_A, site_id=SITE_A, at=NOW)
    device = device.transition(DeviceLifecycle.ACTIVE, at=NOW)

    version_one, applied = device.apply_reported_shadow(
        version=1,
        reported={"battery_percent": 84, "app_version": "sim-1"},
        received_at=NOW,
    )
    duplicate, duplicate_applied = version_one.apply_reported_shadow(
        version=1,
        reported={"battery_percent": 1},
        received_at=NOW + timedelta(seconds=1),
    )

    assert applied is True
    assert duplicate_applied is False
    assert duplicate.reported_shadow == version_one.reported_shadow
    with pytest.raises(StaleShadowVersion, match="shadow_version_regression"):
        version_one.apply_reported_shadow(
            version=0,
            reported={},
            received_at=NOW + timedelta(seconds=2),
        )


def test_presence_exposes_freshness_instead_of_claiming_stale_data_is_online() -> None:
    device = inventory_device().bind(organization_id=ORG_A, site_id=SITE_A, at=NOW)
    device = device.transition(DeviceLifecycle.ACTIVE, at=NOW).mark_seen(
        boot_id="boot-0001",
        sequence=1,
        received_at=NOW,
    )

    assert device.presence_at(NOW + timedelta(seconds=20)) is PresenceStatus.ONLINE
    assert device.presence_at(NOW + timedelta(seconds=60)) is PresenceStatus.STALE
    assert device.presence_at(NOW + timedelta(seconds=120)) is PresenceStatus.OFFLINE
    suspended = device.transition(DeviceLifecycle.SUSPENDED, at=NOW)
    assert suspended.presence_at(NOW) is PresenceStatus.SUSPENDED
