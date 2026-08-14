"""Pure role and organization authorization rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    """Roles enabled in the Stage 1A synthetic control plane."""

    ORGANIZATION_ADMIN = "organization_admin"
    DEVICE_OPERATOR = "device_operator"
    PLATFORM_SUPPORT = "platform_support"


class Permission(StrEnum):
    """Server-side permissions used by Stage 1A use cases."""

    DEVICE_READ = "device_read"
    DEVICE_MANAGE = "device_manage"
    COMMAND_CREATE = "command_create"
    AUDIT_READ = "audit_read"
    SUPPORT_READ = "support_read"


class AuthorizationDenied(Exception):
    """A stable, non-disclosing authorization rejection."""


@dataclass(frozen=True, slots=True)
class Actor:
    """Authenticated actor facts supplied by the trusted Web boundary."""

    actor_id: str
    organization_id: UUID | None
    roles: frozenset[Role]


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ORGANIZATION_ADMIN: frozenset(
        {Permission.DEVICE_READ, Permission.DEVICE_MANAGE, Permission.AUDIT_READ}
    ),
    Role.DEVICE_OPERATOR: frozenset({Permission.DEVICE_READ, Permission.COMMAND_CREATE}),
    Role.PLATFORM_SUPPORT: frozenset({Permission.SUPPORT_READ}),
}


def ensure_organization_access(
    actor: Actor,
    target_organization_id: UUID,
    permission: Permission,
    *,
    support_reason: str | None = None,
) -> None:
    """Fail closed unless the actor can perform this action for the target tenant."""

    if not actor.roles:
        raise AuthorizationDenied("permission_denied")

    is_support = Role.PLATFORM_SUPPORT in actor.roles
    if is_support and (len(actor.roles) != 1 or actor.organization_id is not None):
        raise AuthorizationDenied("conflicting_actor_context")

    if is_support:
        if permission is not Permission.SUPPORT_READ:
            raise AuthorizationDenied("permission_denied")
        if support_reason is None or len(support_reason.strip()) < 10:
            raise AuthorizationDenied("support_reason_required")
        return

    if actor.organization_id is None:
        raise AuthorizationDenied("organization_context_required")
    if actor.organization_id != target_organization_id:
        raise AuthorizationDenied("resource_not_available")

    granted: frozenset[Permission] = frozenset(
        granted_permission
        for role in actor.roles
        for granted_permission in ROLE_PERMISSIONS.get(role, frozenset())
    )
    if permission not in granted:
        raise AuthorizationDenied("permission_denied")
