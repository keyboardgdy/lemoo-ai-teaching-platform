"""Stage 1A PostgreSQL metadata and migration invariants."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy import DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database.metadata import metadata

EXPECTED_TABLES = {
    "organizations",
    "sites",
    "device_models",
    "devices",
    "device_credentials",
    "device_shadows",
    "device_telemetry",
    "device_events",
    "alerts",
    "device_commands",
    "audit_events",
    "outbox_events",
}
TENANT_TABLES = EXPECTED_TABLES - {"device_models"}
MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"


def test_metadata_contains_only_the_stage_1a_core_tables() -> None:
    assert set(metadata.tables) == EXPECTED_TABLES


def test_identifiers_and_timestamps_use_postgresql_uuid_and_timestamptz() -> None:
    for table in metadata.tables.values():
        assert isinstance(table.c.id.type, UUID), table.name
        assert table.c.id.server_default is not None, table.name
        for column in table.columns:
            if column.name.endswith("_at"):
                assert isinstance(column.type, DateTime), (table.name, column.name)
                assert column.type.timezone is True, (table.name, column.name)


def test_every_tenant_fact_has_an_indexed_organization_boundary() -> None:
    for table_name in TENANT_TABLES - {"organizations"}:
        table = metadata.tables[table_name]
        assert "organization_id" in table.c, table_name
        assert any(
            "organization_id" in {column.name for column in index.columns}
            for index in table.indexes
        ), table_name


def test_command_idempotency_is_backed_by_a_database_unique_constraint() -> None:
    table = metadata.tables["device_commands"]
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("organization_id", "idempotency_key") in unique_columns


def test_telemetry_primary_key_includes_its_partition_key() -> None:
    table = metadata.tables["device_telemetry"]
    assert tuple(column.name for column in table.primary_key.columns) == (
        "id",
        "received_at",
    )


def test_initial_migration_enables_and_forces_rls_and_immutable_audit() -> None:
    migrations = sorted(MIGRATIONS.glob("*.py"))
    assert len(migrations) == 1
    source = migrations[0].read_text(encoding="utf-8")
    for table_name in sorted(TENANT_TABLES):
        assert f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY' in source
        assert f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY' in source
        assert f"tenant_isolation_{table_name}" in source
    assert "prevent_audit_mutation" in source
    assert "PARTITION BY RANGE (received_at)" in source
    assert "device_telemetry_default" in source


def test_control_plane_loads_the_complete_model_registry_in_a_fresh_process() -> None:
    command = (
        "from app.infrastructure.database.control_plane import registered_metadata; "
        f"assert {EXPECTED_TABLES!r} == set(registered_metadata.tables)"
    )
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source under test
        [sys.executable, "-c", command],
        cwd=Path(__file__).resolve().parents[3],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
