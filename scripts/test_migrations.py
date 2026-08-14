"""Run migration, RLS, partition, and immutable-audit checks on real PostgreSQL."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID, uuid4

from alembic import command
from alembic.config import Config
from app.config import get_settings
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[1]
SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]{1,62}$")
ORG_A = UUID("0198f001-6000-7000-8000-000000000001")
ORG_B = UUID("0198f001-6000-7000-8000-000000000002")
SITE_A = UUID("0198f001-6100-7000-8000-000000000001")
SITE_B = UUID("0198f001-6100-7000-8000-000000000002")
MODEL_ID = UUID("0198f001-6150-7000-8000-000000000001")
DEVICE_A = UUID("0198f001-6200-7000-8000-000000000001")
DEVICE_B = UUID("0198f001-6200-7000-8000-000000000002")


def identifier_statement(template: str, name: str) -> str:
    if SAFE_NAME.fullmatch(name) is None:
        raise ValueError("unsafe_generated_identifier")
    return template.format(name=name)


def alembic_config(database_url: str) -> Config:
    config = Config(str(ROOT / "apps" / "cloud" / "alembic.ini"))
    config.attributes["database_url"] = database_url
    return config


def seed_cross_tenant_facts(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO organizations (id, code, name) VALUES "
                "(:org_a, 'ORG-SIM-A', 'Synthetic Organization A'), "
                "(:org_b, 'ORG-SIM-B', 'Synthetic Organization B')"
            ),
            {"org_a": ORG_A, "org_b": ORG_B},
        )
        connection.execute(
            text(
                "INSERT INTO sites (id, organization_id, code, name) VALUES "
                "(:site_a, :org_a, 'SITE-SIM-A-01', 'Synthetic Site A'), "
                "(:site_b, :org_b, 'SITE-SIM-B-01', 'Synthetic Site B')"
            ),
            {"site_a": SITE_A, "site_b": SITE_B, "org_a": ORG_A, "org_b": ORG_B},
        )
        connection.execute(
            text(
                "INSERT INTO device_models "
                "(id, model_code, hardware_revision, capabilities) "
                "VALUES (:model_id, 'LEMO-SIM-V1', 'sim-r1', '{}')"
            ),
            {"model_id": MODEL_ID},
        )
        connection.execute(
            text(
                "INSERT INTO devices "
                "(id, organization_id, site_id, model_id, code, serial_number, "
                "lifecycle, certificate_status) VALUES "
                "(:device_a, :org_a, :site_a, :model, 'SIM-A-001', "
                "'LEMO-SIM-A-001', 'active', 'active'), "
                "(:device_b, :org_b, :site_b, :model, 'SIM-B-001', "
                "'LEMO-SIM-B-001', 'active', 'active')"
            ),
            {
                "device_a": DEVICE_A,
                "device_b": DEVICE_B,
                "org_a": ORG_A,
                "org_b": ORG_B,
                "site_a": SITE_A,
                "site_b": SITE_B,
                "model": MODEL_ID,
            },
        )


def set_test_role(
    connection: Connection, role_name: str, organization_id: UUID | None
) -> None:
    execute = connection.execute
    execute(text(identifier_statement('SET LOCAL ROLE "{name}"', role_name)))
    if organization_id is not None:
        execute(
            text("SELECT set_config('app.organization_id', :organization_id, true)"),
            {"organization_id": str(organization_id)},
        )


def verify_rls_and_audit(engine: Engine, role_name: str) -> None:
    with engine.begin() as connection:
        set_test_role(connection, role_name, ORG_A)
        codes = (
            connection.execute(text("SELECT code FROM devices ORDER BY code"))
            .scalars()
            .all()
        )
        if codes != ["SIM-A-001"]:
            raise AssertionError(f"RLS returned unexpected devices: {codes}")

    try:
        with engine.begin() as connection:
            set_test_role(connection, role_name, ORG_A)
            connection.execute(
                text(
                    "INSERT INTO sites (organization_id, code, name) "
                    "VALUES (:org_b, 'CROSS-TENANT', 'must fail')"
                ),
                {"org_b": ORG_B},
            )
    except DBAPIError:
        pass
    else:
        raise AssertionError("cross-tenant insert unexpectedly succeeded")

    audit_id = uuid4()
    with engine.begin() as connection:
        set_test_role(connection, role_name, ORG_A)
        connection.execute(
            text(
                "INSERT INTO audit_events "
                "(id, organization_id, actor_id, action, target_type, target_id, "
                "reason, request_id, trace_id) VALUES "
                "(:id, :org, 'USR-SIM-OPS-A', 'test', 'device', 'SIM-A-001', "
                "'Migration test', :request_id, 'migration-test')"
            ),
            {"id": audit_id, "org": ORG_A, "request_id": uuid4()},
        )
    try:
        with engine.begin() as connection:
            set_test_role(connection, role_name, ORG_A)
            connection.execute(
                text("UPDATE audit_events SET reason = 'tampered' WHERE id = :id"),
                {"id": audit_id},
            )
    except DBAPIError:
        pass
    else:
        raise AssertionError("append-only audit update unexpectedly succeeded")

    with engine.begin() as connection:
        set_test_role(connection, role_name, None)
        count = connection.execute(text("SELECT count(*) FROM devices")).scalar_one()
        if count != 0:
            raise AssertionError("missing tenant context did not fail closed")


def main() -> None:
    settings = get_settings()
    base_url = make_url(settings.database_url)
    admin_url = base_url.set(database="postgres")
    suffix = uuid4().hex[:10]
    database_name = f"lemoo_migration_{suffix}"
    role_name = f"lemoo_app_{suffix}"
    database_url = base_url.set(database=database_name).render_as_string(
        hide_password=False
    )
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    test_engine: Engine | None = None

    try:
        with admin_engine.connect() as connection:
            connection.exec_driver_sql(
                identifier_statement('CREATE DATABASE "{name}"', database_name)
            )
            connection.exec_driver_sql(
                identifier_statement(
                    'CREATE ROLE "{name}" NOLOGIN NOSUPERUSER NOBYPASSRLS', role_name
                )
            )

        config = alembic_config(database_url)
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        test_engine = create_engine(database_url)
        tables = set(inspect(test_engine).get_table_names())
        expected = {
            "organizations",
            "sites",
            "device_models",
            "devices",
            "device_credentials",
            "device_shadows",
            "device_telemetry",
            "device_telemetry_default",
            "device_events",
            "alerts",
            "device_commands",
            "audit_events",
            "outbox_events",
            "alembic_version",
        }
        if tables != expected:
            raise AssertionError(f"migration tables differ: {tables ^ expected}")

        with test_engine.begin() as connection:
            connection.exec_driver_sql(
                identifier_statement(
                    'GRANT USAGE ON SCHEMA public TO "{name}"', role_name
                )
            )
            connection.exec_driver_sql(
                identifier_statement(
                    'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{name}"',
                    role_name,
                )
            )
        seed_cross_tenant_facts(test_engine)
        verify_rls_and_audit(test_engine, role_name)

        command.downgrade(config, "base")
        remaining = set(inspect(test_engine).get_table_names())
        if remaining != {"alembic_version"}:
            raise AssertionError(f"downgrade left tables: {remaining}")
        command.upgrade(config, "head")
        print("migration_test=pass empty_upgrade=pass repeat=pass rls=pass audit=pass")
    finally:
        if test_engine is not None:
            test_engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.exec_driver_sql(
                identifier_statement('DROP DATABASE IF EXISTS "{name}"', database_name)
            )
            connection.exec_driver_sql(
                identifier_statement('DROP ROLE IF EXISTS "{name}"', role_name)
            )
        admin_engine.dispose()


if __name__ == "__main__":
    main()
