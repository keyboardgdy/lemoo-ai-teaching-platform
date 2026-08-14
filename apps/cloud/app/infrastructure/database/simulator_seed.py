"""Idempotent synthetic-only seed facts for the Stage 1A simulator."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import Engine, text

from app.simulator.facts import (
    MODEL_ID,
    ORG_A_ID,
    ORG_B_ID,
    SITE_A_ID,
    SITE_B_ID,
    SYNTHETIC_DEVICES,
)


def seed_simulator_facts(engine: Engine, *, now: datetime | None = None) -> None:
    """Upsert only the fixed synthetic facts from PILOT-001."""

    observed_at = now or datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO organizations (id, code, name) VALUES "
                "(:org_a, 'ORG-SIM-A', '模拟试点机构 A'), "
                "(:org_b, 'ORG-SIM-B', '模拟隔离机构 B') "
                "ON CONFLICT (id) DO UPDATE SET "
                "code = EXCLUDED.code, name = EXCLUDED.name, updated_at = now()"
            ),
            {"org_a": ORG_A_ID, "org_b": ORG_B_ID},
        )
        connection.execute(
            text(
                "INSERT INTO sites (id, organization_id, code, name) VALUES "
                "(:site_a, :org_a, 'SITE-SIM-A1', '模拟场地 A1'), "
                "(:site_b, :org_b, 'SITE-SIM-B1', '模拟场地 B1') "
                "ON CONFLICT (id) DO UPDATE SET "
                "organization_id = EXCLUDED.organization_id, code = EXCLUDED.code, "
                "name = EXCLUDED.name, updated_at = now()"
            ),
            {
                "site_a": SITE_A_ID,
                "site_b": SITE_B_ID,
                "org_a": ORG_A_ID,
                "org_b": ORG_B_ID,
            },
        )
        connection.execute(
            text(
                "INSERT INTO device_models "
                "(id, model_code, hardware_revision, capabilities) VALUES "
                "(:id, 'SIM_EDU_ROBOT_V1', 'sim-r1', CAST(:capabilities AS jsonb)) "
                "ON CONFLICT (id) DO UPDATE SET "
                "model_code = EXCLUDED.model_code, "
                "hardware_revision = EXCLUDED.hardware_revision, "
                "capabilities = EXCLUDED.capabilities"
            ),
            {
                "id": MODEL_ID,
                "capabilities": json.dumps(
                    {
                        "protocol_profile": "device-v1",
                        "capability_profile": "stage1-device-cloud-minimal",
                    }
                ),
            },
        )
        for index, device in enumerate(SYNTHETIC_DEVICES, start=1):
            last_seen_at = (
                None if device.code == "SIM-B-002" else observed_at - timedelta(seconds=5 + index)
            )
            connection.execute(
                text(
                    "INSERT INTO devices "
                    "(id, organization_id, site_id, model_id, code, serial_number, "
                    "lifecycle, certificate_status, last_seen_at, boot_id, last_sequence) "
                    "VALUES (:id, :organization_id, :site_id, :model_id, :code, "
                    ":serial_number, :lifecycle, :certificate_status, :last_seen_at, "
                    ":boot_id, :last_sequence) "
                    "ON CONFLICT (id) DO UPDATE SET "
                    "organization_id = EXCLUDED.organization_id, site_id = EXCLUDED.site_id, "
                    "model_id = EXCLUDED.model_id, code = EXCLUDED.code, "
                    "serial_number = EXCLUDED.serial_number, lifecycle = EXCLUDED.lifecycle, "
                    "certificate_status = EXCLUDED.certificate_status, "
                    "last_seen_at = EXCLUDED.last_seen_at, boot_id = EXCLUDED.boot_id, "
                    "last_sequence = EXCLUDED.last_sequence, updated_at = now()"
                ),
                {
                    "id": device.id,
                    "organization_id": device.organization_id,
                    "site_id": device.site_id,
                    "model_id": MODEL_ID,
                    "code": device.code,
                    "serial_number": f"LEMO-{device.code}",
                    "lifecycle": device.lifecycle,
                    "certificate_status": device.certificate_status,
                    "last_seen_at": last_seen_at,
                    "boot_id": f"boot-{device.code.lower()}",
                    "last_sequence": index,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO device_shadows "
                    "(id, organization_id, device_id, reported_version, reported, "
                    "desired_version, desired, reported_at) "
                    "VALUES (:id, :organization_id, :device_id, 1, "
                    "CAST(:reported AS jsonb), 0, '{}'::jsonb, :reported_at) "
                    "ON CONFLICT (device_id) DO UPDATE SET "
                    "reported_version = EXCLUDED.reported_version, "
                    "reported = EXCLUDED.reported, reported_at = EXCLUDED.reported_at, "
                    "updated_at = now()"
                ),
                {
                    "id": device.id,
                    "organization_id": device.organization_id,
                    "device_id": device.id,
                    "reported": json.dumps(
                        {
                            "firmware_major": "sim-1",
                            "bootloader_major": "sim-1",
                        }
                    ),
                    "reported_at": last_seen_at,
                },
            )
