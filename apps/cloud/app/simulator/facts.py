"""Stable identifiers for the two synthetic tenants and six virtual devices."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

ORG_A_ID = UUID("0198f001-6000-7000-8000-000000000001")
ORG_B_ID = UUID("0198f001-6000-7000-8000-000000000002")
SITE_A_ID = UUID("0198f001-6100-7000-8000-000000000001")
SITE_B_ID = UUID("0198f001-6100-7000-8000-000000000002")
MODEL_ID = UUID("0198f001-6150-7000-8000-000000000001")


@dataclass(frozen=True, slots=True)
class SyntheticDeviceFact:
    id: UUID
    code: str
    organization_id: UUID
    site_id: UUID
    lifecycle: str = "active"
    certificate_status: str = "active"


SYNTHETIC_DEVICES = (
    SyntheticDeviceFact(
        UUID("0198f001-6200-7000-8000-000000000001"),
        "SIM-A-001",
        ORG_A_ID,
        SITE_A_ID,
    ),
    SyntheticDeviceFact(
        UUID("0198f001-6200-7000-8000-000000000002"),
        "SIM-A-002",
        ORG_A_ID,
        SITE_A_ID,
    ),
    SyntheticDeviceFact(
        UUID("0198f001-6200-7000-8000-000000000003"),
        "SIM-A-003",
        ORG_A_ID,
        SITE_A_ID,
    ),
    SyntheticDeviceFact(
        UUID("0198f001-6200-7000-8000-000000000004"),
        "SIM-A-004",
        ORG_A_ID,
        SITE_A_ID,
    ),
    SyntheticDeviceFact(
        UUID("0198f001-6200-7000-8000-000000000101"),
        "SIM-B-001",
        ORG_B_ID,
        SITE_B_ID,
    ),
    SyntheticDeviceFact(
        UUID("0198f001-6200-7000-8000-000000000102"),
        "SIM-B-002",
        ORG_B_ID,
        SITE_B_ID,
        lifecycle="suspended",
        certificate_status="suspended",
    ),
)
