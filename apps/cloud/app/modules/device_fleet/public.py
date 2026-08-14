"""Stable public DTOs exposed by the device fleet module."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.device_fleet.domain import Device


@dataclass(frozen=True, slots=True)
class DeviceControlSnapshot:
    """Minimal device facts needed to authorize a control action."""

    device_id: UUID
    organization_id: UUID
    lifecycle: str
    presence: str
    certificate_status: str

    @classmethod
    def from_device(cls, device: Device, *, presence: str) -> DeviceControlSnapshot:
        if device.organization_id is None:
            raise ValueError("device_organization_required")
        return cls(
            device_id=device.id,
            organization_id=device.organization_id,
            lifecycle=device.lifecycle.value,
            presence=presence,
            certificate_status=device.certificate_status.value,
        )


__all__ = ["DeviceControlSnapshot"]
