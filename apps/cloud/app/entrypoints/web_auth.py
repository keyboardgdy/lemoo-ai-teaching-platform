"""Synthetic browser-session boundary for the non-production simulator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.modules.identity.public import Actor, Role
from app.simulator.facts import ORG_A_ID, ORG_B_ID

SESSION_COOKIE = "lemoo_session"
CSRF_COOKIE = "lemoo_csrf"

SimulatorActorKey = Literal[
    "org_a_admin",
    "org_a_operator",
    "org_b_admin",
    "org_b_operator",
    "platform_support",
]


@dataclass(frozen=True, slots=True)
class SimulatorIdentity:
    session_id: str
    actor: Actor


SIMULATOR_IDENTITIES: dict[SimulatorActorKey, SimulatorIdentity] = {
    "org_a_admin": SimulatorIdentity(
        session_id="sim-org-a-admin",
        actor=Actor(
            actor_id="USR-SIM-A-ORG-001",
            organization_id=ORG_A_ID,
            roles=frozenset({Role.ORGANIZATION_ADMIN}),
        ),
    ),
    "org_a_operator": SimulatorIdentity(
        session_id="sim-org-a-operator",
        actor=Actor(
            actor_id="USR-SIM-A-OPS-001",
            organization_id=ORG_A_ID,
            roles=frozenset({Role.DEVICE_OPERATOR}),
        ),
    ),
    "org_b_admin": SimulatorIdentity(
        session_id="sim-org-b-admin",
        actor=Actor(
            actor_id="USR-SIM-B-ORG-001",
            organization_id=ORG_B_ID,
            roles=frozenset({Role.ORGANIZATION_ADMIN}),
        ),
    ),
    "org_b_operator": SimulatorIdentity(
        session_id="sim-org-b-operator",
        actor=Actor(
            actor_id="USR-SIM-B-OPS-001",
            organization_id=ORG_B_ID,
            roles=frozenset({Role.DEVICE_OPERATOR}),
        ),
    ),
    "platform_support": SimulatorIdentity(
        session_id="sim-platform-support",
        actor=Actor(
            actor_id="USR-SIM-PLT-001",
            organization_id=None,
            roles=frozenset({Role.PLATFORM_SUPPORT}),
        ),
    ),
}
IDENTITIES_BY_SESSION = {
    identity.session_id: identity for identity in SIMULATOR_IDENTITIES.values()
}


def actor_for_session(session_id: str | None) -> Actor | None:
    if session_id is None:
        return None
    identity = IDENTITIES_BY_SESSION.get(session_id)
    return identity.actor if identity is not None else None
