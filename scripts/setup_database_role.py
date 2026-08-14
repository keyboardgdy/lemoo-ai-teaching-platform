"""Provision the fixed local NOBYPASSRLS application role."""

from __future__ import annotations

import re

from app.config import get_settings
from sqlalchemy import create_engine, text

SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def identifier(name: str) -> str:
    if SAFE_NAME.fullmatch(name) is None:
        raise ValueError("unsafe_database_identifier")
    return f'"{name}"'


def main() -> None:
    settings = get_settings()
    role = settings.postgres_role
    quoted_role = identifier(role)
    quoted_database = identifier(settings.postgres_db)
    engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role)"),
            {"role": role},
        ).scalar_one()
        if not exists:
            connection.exec_driver_sql(
                f"CREATE ROLE {quoted_role} NOLOGIN NOSUPERUSER NOCREATEDB "
                "NOCREATEROLE NOINHERIT NOBYPASSRLS"
            )
        connection.exec_driver_sql(
            f"ALTER ROLE {quoted_role} NOLOGIN NOSUPERUSER NOCREATEDB "
            "NOCREATEROLE NOINHERIT NOBYPASSRLS"
        )
        connection.exec_driver_sql(
            f"GRANT CONNECT ON DATABASE {quoted_database} TO {quoted_role}"
        )
        connection.exec_driver_sql(f"GRANT USAGE ON SCHEMA public TO {quoted_role}")
        connection.exec_driver_sql(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
            f"IN SCHEMA public TO {quoted_role}"
        )
        connection.exec_driver_sql(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT "
            f"SELECT, INSERT, UPDATE, DELETE ON TABLES TO {quoted_role}"
        )
    engine.dispose()
    print(f"database_role_setup=pass role={role}")


if __name__ == "__main__":
    main()
