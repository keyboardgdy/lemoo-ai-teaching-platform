"""Tenant and role authorization rules for the synthetic control plane."""

from uuid import UUID

import pytest

from app.modules.identity.domain import (
    Actor,
    AuthorizationDenied,
    Permission,
    Role,
    ensure_organization_access,
)

ORG_A = UUID("0198f001-6000-7000-8000-000000000001")
ORG_B = UUID("0198f001-6000-7000-8000-000000000002")


def test_organization_actor_can_use_only_granted_permissions_in_own_tenant() -> None:
    operator = Actor(
        actor_id="USR-SIM-OPS-A",
        organization_id=ORG_A,
        roles=frozenset({Role.DEVICE_OPERATOR}),
    )

    ensure_organization_access(operator, ORG_A, Permission.DEVICE_READ)
    ensure_organization_access(operator, ORG_A, Permission.COMMAND_CREATE)

    with pytest.raises(AuthorizationDenied, match="permission_denied"):
        ensure_organization_access(operator, ORG_A, Permission.DEVICE_MANAGE)


def test_cross_tenant_access_is_rejected_without_existence_disclosure() -> None:
    actor = Actor(
        actor_id="USR-SIM-ADMIN-A",
        organization_id=ORG_A,
        roles=frozenset({Role.ORGANIZATION_ADMIN}),
    )

    with pytest.raises(AuthorizationDenied, match="resource_not_available"):
        ensure_organization_access(actor, ORG_B, Permission.DEVICE_READ)


def test_platform_support_requires_reason_and_remains_read_only() -> None:
    support = Actor(
        actor_id="USR-SIM-SUPPORT",
        organization_id=None,
        roles=frozenset({Role.PLATFORM_SUPPORT}),
    )

    ensure_organization_access(
        support,
        ORG_B,
        Permission.SUPPORT_READ,
        support_reason="Investigate simulator scenario SIM-AC-007",
    )
    with pytest.raises(AuthorizationDenied, match="support_reason_required"):
        ensure_organization_access(support, ORG_B, Permission.SUPPORT_READ)
    with pytest.raises(AuthorizationDenied, match="permission_denied"):
        ensure_organization_access(
            support,
            ORG_B,
            Permission.COMMAND_CREATE,
            support_reason="No write access",
        )


def test_missing_or_conflicting_actor_context_fails_closed() -> None:
    missing_tenant = Actor(
        actor_id="USR-SIM-OPS-UNKNOWN",
        organization_id=None,
        roles=frozenset({Role.DEVICE_OPERATOR}),
    )
    conflicting = Actor(
        actor_id="USR-SIM-CONFLICT",
        organization_id=ORG_A,
        roles=frozenset({Role.DEVICE_OPERATOR, Role.PLATFORM_SUPPORT}),
    )

    with pytest.raises(AuthorizationDenied, match="organization_context_required"):
        ensure_organization_access(missing_tenant, ORG_A, Permission.DEVICE_READ)
    with pytest.raises(AuthorizationDenied, match="conflicting_actor_context"):
        ensure_organization_access(conflicting, ORG_A, Permission.DEVICE_READ)
