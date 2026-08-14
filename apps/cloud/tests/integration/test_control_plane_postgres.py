"""End-to-end FastAPI behavior through a real NOBYPASSRLS PostgreSQL role."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url

from app.config import Settings
from app.entrypoints.api import create_app
from app.infrastructure.database.control_plane import PostgresControlPlane
from app.infrastructure.database.simulator_seed import seed_simulator_facts
from app.simulator.facts import ORG_A_ID, SYNTHETIC_DEVICES

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def identifier(statement: str, name: str) -> str:
    if SAFE_NAME.fullmatch(name) is None:
        raise ValueError("unsafe_test_identifier")
    return statement.format(name=name)


@pytest.fixture(scope="session")
def postgres_settings() -> Iterator[Settings]:
    base = Settings(environment="test")
    base_url = make_url(base.database_url)
    admin_engine = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    suffix = uuid4().hex[:10]
    database_name = f"lemoo_api_{suffix}"
    role_name = f"lemoo_api_{suffix}"
    password = uuid4().hex
    database_url = base_url.set(database=database_name).render_as_string(hide_password=False)
    test_engine: Engine | None = None
    try:
        with admin_engine.connect() as connection:
            connection.exec_driver_sql(identifier('CREATE DATABASE "{name}"', database_name))
            connection.exec_driver_sql(
                identifier(
                    f"CREATE ROLE \"{{name}}\" LOGIN PASSWORD '{password}' "
                    "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS",
                    role_name,
                )
            )
        alembic = Config(str(REPOSITORY_ROOT / "apps" / "cloud" / "alembic.ini"))
        alembic.attributes["database_url"] = database_url
        command.upgrade(alembic, "head")
        test_engine = create_engine(database_url)
        with test_engine.begin() as connection:
            connection.exec_driver_sql(
                identifier('GRANT USAGE ON SCHEMA public TO "{name}"', role_name)
            )
            connection.exec_driver_sql(
                identifier(
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
                    'IN SCHEMA public TO "{name}"',
                    role_name,
                )
            )
        seed_simulator_facts(test_engine)
        yield Settings(
            environment="test",
            postgres_host=base.postgres_host,
            postgres_port=base.postgres_port,
            postgres_user=role_name,
            postgres_password=password,
            postgres_db=database_name,
            postgres_role=role_name,
        )
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
                identifier('DROP DATABASE IF EXISTS "{name}"', database_name)
            )
            connection.exec_driver_sql(identifier('DROP ROLE IF EXISTS "{name}"', role_name))
        admin_engine.dispose()


async def authenticate(client: AsyncClient, actor: str = "org_a_operator") -> str:
    response = await client.post("/api/v1/simulator/session", json={"actor": actor})
    assert response.status_code == 201
    token = client.cookies.get("lemoo_csrf")
    assert token
    return token


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fastapi_uses_rls_role_and_commits_command_audit_outbox_atomically(
    postgres_settings: Settings,
) -> None:
    control_plane = PostgresControlPlane(postgres_settings)
    application = create_app(postgres_settings, control_plane=control_plane)
    transport = ASGITransport(app=application)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            csrf = await authenticate(client)
            page = await client.get("/api/v1/devices?limit=100")
            cross_tenant = await client.get(f"/api/v1/devices/{SYNTHETIC_DEVICES[4].id}")
            idempotency_key = uuid4()
            payload: dict[str, object] = {
                "device_id": str(SYNTHETIC_DEVICES[0].id),
                "command_type": "refresh_shadow",
                "reason": "Refresh the synthetic device shadow",
                "expires_at": (datetime.now(UTC) + timedelta(minutes=2)).isoformat(),
                "parameters": {},
            }
            headers = {
                "Idempotency-Key": str(idempotency_key),
                "X-CSRF-Token": csrf,
            }
            created = await client.post("/api/v1/device-commands", json=payload, headers=headers)
            replayed = await client.post("/api/v1/device-commands", json=payload, headers=headers)
            conflict = await client.post(
                "/api/v1/device-commands",
                json=payload | {"reason": "A different synthetic request"},
                headers=headers,
            )
            command_id = UUID(created.json()["id"])
            fetched = await client.get(f"/api/v1/device-commands/{command_id}")
            admin_csrf = await authenticate(client, "org_a_admin")
            admin_rejected = await client.post(
                "/api/v1/device-commands",
                json=payload,
                headers={
                    "Idempotency-Key": str(uuid4()),
                    "X-CSRF-Token": admin_csrf,
                },
            )
            org_b_csrf = await authenticate(client, "org_b_operator")
            suspended_rejected = await client.post(
                "/api/v1/device-commands",
                json=payload
                | {
                    "device_id": str(SYNTHETIC_DEVICES[5].id),
                    "expires_at": (datetime.now(UTC) + timedelta(minutes=2)).isoformat(),
                },
                headers={
                    "Idempotency-Key": str(uuid4()),
                    "X-CSRF-Token": org_b_csrf,
                },
            )
    finally:
        await control_plane.close()

    assert page.status_code == 200
    assert [item["code"] for item in page.json()["items"]] == [
        "SIM-A-001",
        "SIM-A-002",
        "SIM-A-003",
        "SIM-A-004",
    ]
    assert cross_tenant.status_code == 404
    assert created.status_code == 202
    assert created.json()["state"] == "approved"
    assert replayed.status_code == 200
    assert replayed.headers["idempotency-replayed"] == "true"
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_key_conflict"
    assert fetched.status_code == 200
    assert admin_rejected.status_code == 403
    assert suspended_rejected.status_code == 409
    assert suspended_rejected.json()["code"] == "device_not_active"

    engine = create_engine(postgres_settings.database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.organization_id', :organization_id, true)"),
                {"organization_id": str(ORG_A_ID)},
            )
            counts = cast(
                tuple[int, int, int],
                connection.execute(
                    text(
                        "SELECT "
                        "(SELECT count(*) FROM device_commands WHERE id = :id), "
                        "(SELECT count(*) FROM audit_events WHERE target_id = :target), "
                        "(SELECT count(*) FROM outbox_events WHERE aggregate_id = :id)"
                    ),
                    {"id": command_id, "target": str(command_id)},
                ).one(),
            )
    finally:
        engine.dispose()
    assert counts == (1, 1, 1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_support_requires_target_and_reason_and_is_audited(
    postgres_settings: Settings,
) -> None:
    control_plane = PostgresControlPlane(postgres_settings)
    application = create_app(postgres_settings, control_plane=control_plane)
    transport = ASGITransport(app=application)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            await authenticate(client, "platform_support")
            missing = await client.get("/api/v1/devices")
            short_reason = await client.get(
                f"/api/v1/devices?organization_id={ORG_A_ID}",
                headers={"X-Support-Reason": "short"},
            )
            allowed = await client.get(
                f"/api/v1/devices?organization_id={ORG_A_ID}",
                headers={"X-Support-Reason": "Investigate synthetic demo state"},
            )
    finally:
        await control_plane.close()

    assert missing.status_code == short_reason.status_code == 403
    assert allowed.status_code == 200
    assert len(allowed.json()["items"]) == 4

    engine = create_engine(postgres_settings.database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT set_config('app.organization_id', :organization_id, true)"),
                {"organization_id": str(ORG_A_ID)},
            )
            audit = connection.execute(
                text(
                    "SELECT reason, request_id::text, trace_id FROM audit_events "
                    "WHERE action = 'support.device.list' "
                    "ORDER BY occurred_at DESC LIMIT 1"
                )
            ).one()
    finally:
        engine.dispose()
    assert audit[0] == "Investigate synthetic demo state"
    assert UUID(audit[1])
    assert audit[2] == audit[1]
