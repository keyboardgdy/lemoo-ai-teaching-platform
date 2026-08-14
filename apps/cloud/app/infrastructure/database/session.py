"""Async PostgreSQL session construction with transaction-scoped tenant context."""

from __future__ import annotations

import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings

SAFE_ROLE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def create_engine(settings: Settings) -> AsyncEngine:
    """Create an async engine without opening a connection at import time."""

    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def tenant_session(
    factory: async_sessionmaker[AsyncSession],
    organization_id: UUID,
    database_role: str,
) -> AsyncGenerator[AsyncSession]:
    """Open one transaction and set its PostgreSQL RLS organization context."""

    if SAFE_ROLE.fullmatch(database_role) is None:
        raise ValueError("unsafe_database_role")
    async with factory() as session, session.begin():
        await session.execute(text(f'SET LOCAL ROLE "{database_role}"'))
        await session.execute(
            text("SELECT set_config('app.organization_id', :organization_id, true)"),
            {"organization_id": str(organization_id)},
        )
        yield session
