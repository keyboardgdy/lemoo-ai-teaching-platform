"""Pure Stage 1A device lifecycle, freshness, sequence, and shadow rules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID


class DeviceLifecycle(StrEnum):
    MANUFACTURED = "manufactured"
    PROVISIONED = "provisioned"
    INVENTORY = "inventory"
    ASSIGNED = "assigned"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class CertificateStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PresenceStatus(StrEnum):
    ONLINE = "online"
    STALE = "stale"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
    SUSPENDED = "suspended"


class SequenceDecision(StrEnum):
    ACCEPT = "accept"
    DUPLICATE = "duplicate"
    OUT_OF_ORDER = "out_of_order"
    NEW_BOOT = "new_boot"


class IllegalDeviceTransition(Exception):
    """The requested lifecycle transition is not in the frozen state machine."""


class StaleShadowVersion(Exception):
    """An older reported shadow attempted to replace a newer fact."""


ALLOWED_TRANSITIONS: dict[DeviceLifecycle, frozenset[DeviceLifecycle]] = {
    DeviceLifecycle.MANUFACTURED: frozenset({DeviceLifecycle.PROVISIONED}),
    DeviceLifecycle.PROVISIONED: frozenset({DeviceLifecycle.INVENTORY}),
    DeviceLifecycle.INVENTORY: frozenset({DeviceLifecycle.ASSIGNED}),
    DeviceLifecycle.ASSIGNED: frozenset({DeviceLifecycle.ACTIVE}),
    DeviceLifecycle.ACTIVE: frozenset(
        {
            DeviceLifecycle.MAINTENANCE,
            DeviceLifecycle.SUSPENDED,
            DeviceLifecycle.RETIRED,
        }
    ),
    DeviceLifecycle.MAINTENANCE: frozenset(
        {DeviceLifecycle.ACTIVE, DeviceLifecycle.SUSPENDED, DeviceLifecycle.RETIRED}
    ),
    DeviceLifecycle.SUSPENDED: frozenset({DeviceLifecycle.ACTIVE, DeviceLifecycle.RETIRED}),
    DeviceLifecycle.RETIRED: frozenset(),
}


def classify_sequence(
    *,
    current_boot: str | None,
    current_sequence: int | None,
    incoming_boot: str,
    incoming_sequence: int,
) -> SequenceDecision:
    """Classify one message without allowing an old sequence to regress state."""

    if incoming_sequence < 0:
        raise ValueError("sequence_must_be_non_negative")
    if current_boot is None or current_sequence is None:
        return SequenceDecision.ACCEPT
    if incoming_boot != current_boot:
        return SequenceDecision.NEW_BOOT
    if incoming_sequence == current_sequence:
        return SequenceDecision.DUPLICATE
    if incoming_sequence < current_sequence:
        return SequenceDecision.OUT_OF_ORDER
    return SequenceDecision.ACCEPT


@dataclass(frozen=True, slots=True)
class Device:
    """Synthetic device aggregate; methods return a new immutable state."""

    id: UUID
    code: str
    serial_number: str
    model_code: str
    hardware_revision: str
    lifecycle: DeviceLifecycle
    certificate_status: CertificateStatus
    organization_id: UUID | None = None
    site_id: UUID | None = None
    last_seen_at: datetime | None = None
    boot_id: str | None = None
    last_sequence: int | None = None
    reported_shadow_version: int = 0
    reported_shadow: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    updated_at: datetime | None = None
    is_synthetic: bool = True
    is_physical_hardware: bool = False
    production_supported: bool = False

    def bind(self, *, organization_id: UUID, site_id: UUID, at: datetime) -> Device:
        """Assign an inventory device to exactly one synthetic tenant and site."""

        if self.lifecycle is not DeviceLifecycle.INVENTORY:
            raise IllegalDeviceTransition(
                f"{self.lifecycle.value}_to_{DeviceLifecycle.ASSIGNED.value}"
            )
        return replace(
            self,
            organization_id=organization_id,
            site_id=site_id,
            lifecycle=DeviceLifecycle.ASSIGNED,
            updated_at=at,
        )

    def transition(self, target: DeviceLifecycle, *, at: datetime) -> Device:
        """Apply a legal lifecycle transition without mutating the prior state."""

        if target is self.lifecycle:
            return self
        if target not in ALLOWED_TRANSITIONS[self.lifecycle]:
            raise IllegalDeviceTransition(f"{self.lifecycle.value}_to_{target.value}")
        if target is DeviceLifecycle.ACTIVE:
            if self.organization_id is None or self.site_id is None:
                raise IllegalDeviceTransition("active_requires_binding")
            if self.certificate_status is not CertificateStatus.ACTIVE:
                raise IllegalDeviceTransition("active_requires_certificate")
        certificate_status = self.certificate_status
        if target is DeviceLifecycle.RETIRED:
            certificate_status = CertificateStatus.REVOKED
        return replace(
            self,
            lifecycle=target,
            certificate_status=certificate_status,
            updated_at=at,
        )

    def mark_seen(
        self,
        *,
        boot_id: str,
        sequence: int,
        received_at: datetime,
    ) -> Device:
        """Advance last-seen facts only for a newer message or a new boot."""

        decision = classify_sequence(
            current_boot=self.boot_id,
            current_sequence=self.last_sequence,
            incoming_boot=boot_id,
            incoming_sequence=sequence,
        )
        if decision in {SequenceDecision.DUPLICATE, SequenceDecision.OUT_OF_ORDER}:
            return self
        return replace(
            self,
            boot_id=boot_id,
            last_sequence=sequence,
            last_seen_at=received_at,
            updated_at=received_at,
        )

    def apply_reported_shadow(
        self,
        *,
        version: int,
        reported: Mapping[str, Any],
        received_at: datetime,
    ) -> tuple[Device, bool]:
        """Apply a monotonic reported-shadow version; equal versions are idempotent."""

        if version < self.reported_shadow_version:
            raise StaleShadowVersion("shadow_version_regression")
        if version == self.reported_shadow_version:
            return self, False
        return (
            replace(
                self,
                reported_shadow_version=version,
                reported_shadow=MappingProxyType(dict(reported)),
                last_seen_at=received_at,
                updated_at=received_at,
            ),
            True,
        )

    def presence_at(
        self,
        now: datetime,
        *,
        stale_after: timedelta = timedelta(seconds=30),
        offline_after: timedelta = timedelta(seconds=90),
    ) -> PresenceStatus:
        """Calculate freshness from server receipt time rather than client clocks."""

        if self.lifecycle is DeviceLifecycle.SUSPENDED:
            return PresenceStatus.SUSPENDED
        if self.last_seen_at is None:
            return PresenceStatus.UNKNOWN
        age = now - self.last_seen_at
        if age <= stale_after:
            return PresenceStatus.ONLINE
        if age <= offline_after:
            return PresenceStatus.STALE
        return PresenceStatus.OFFLINE
