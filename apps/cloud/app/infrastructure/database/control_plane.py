"""PostgreSQL adapter for the Stage 1A Web control-plane port."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid7

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.infrastructure.database.metadata import metadata as registered_metadata
from app.infrastructure.database.session import (
    create_engine,
    create_session_factory,
    tenant_session,
)
from app.modules.audit.models import AuditEventModel
from app.modules.control_plane.public import (
    AccessDenied,
    CommandCreation,
    CommandInput,
    CommandView,
    DevicePage,
    DeviceView,
    IdempotencyConflict,
    InvalidCursor,
    OperationRejected,
    ResourceNotFound,
)
from app.modules.device_fleet.domain import CertificateStatus, Device, DeviceLifecycle
from app.modules.device_fleet.models import (
    DeviceModelModel,
    DeviceRecord,
    DeviceShadowModel,
)
from app.modules.device_fleet.public import DeviceControlSnapshot
from app.modules.device_operations.domain import (
    CommandPolicyViolation,
    CommandRequest,
    CommandState,
    DeviceCommand,
    create_refresh_shadow,
    resolve_idempotent_request,
)
from app.modules.device_operations.models import DeviceCommandModel
from app.modules.identity.public import (
    Actor,
    AuthorizationDenied,
    Permission,
    Role,
    ensure_organization_access,
)
from app.modules.jobs.models import OutboxEventModel

_CONTROL_PLANE_TABLES = {
    "organizations",
    "devices",
    "device_commands",
    "audit_events",
    "outbox_events",
}
_missing_tables = _CONTROL_PLANE_TABLES.difference(registered_metadata.tables)
if _missing_tables:
    missing = ", ".join(sorted(_missing_tables))
    raise RuntimeError(f"Incomplete SQLAlchemy model registry: {missing}")


def _encode_cursor(code: str, device_id: UUID) -> str:
    payload = json.dumps([code, str(device_id)], separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def _decode_cursor(cursor: str) -> tuple[str, UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        value = cast(object, json.loads(base64.urlsafe_b64decode(padded).decode()))
        if not isinstance(value, list):
            raise ValueError
        parts = cast(list[object], value)
        if len(parts) != 2 or not isinstance(parts[0], str) or not isinstance(parts[1], str):
            raise ValueError
        return parts[0], UUID(parts[1])
    except (ValueError, TypeError, json.JSONDecodeError) as exception:
        raise InvalidCursor("invalid_cursor") from exception


def _authorized_organization(
    actor: Actor,
    *,
    target_organization_id: UUID | None,
    permission: Permission,
    support_reason: str | None = None,
) -> UUID:
    is_support = Role.PLATFORM_SUPPORT in actor.roles
    target = target_organization_id or actor.organization_id
    if target is None:
        raise AccessDenied("target_organization_required")
    requested_permission = Permission.SUPPORT_READ if is_support else permission
    try:
        ensure_organization_access(
            actor,
            target,
            requested_permission,
            support_reason=support_reason,
        )
    except AuthorizationDenied as exception:
        raise AccessDenied(str(exception)) from exception
    return target


def _as_domain_command(record: DeviceCommandModel) -> DeviceCommand:
    return DeviceCommand(
        id=record.id,
        organization_id=record.organization_id,
        device_id=record.device_id,
        command_type=record.command_type,
        idempotency_key=record.idempotency_key,
        request_fingerprint=record.request_fingerprint,
        requested_by=record.requested_by,
        reason=record.reason,
        parameters=record.parameters,
        expires_at=record.expires_at,
        state=CommandState(record.state),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _command_view(command: DeviceCommand) -> CommandView:
    return CommandView(
        id=command.id,
        organization_id=command.organization_id,
        device_id=command.device_id,
        command_type=command.command_type,
        idempotency_key=command.idempotency_key,
        requested_by=command.requested_by,
        reason=command.reason,
        expires_at=command.expires_at,
        state=command.state.value,
        created_at=command.created_at,
        updated_at=command.updated_at,
        production_supported=False,
    )


def _device_view(
    record: DeviceRecord,
    model: DeviceModelModel,
    shadow: DeviceShadowModel | None,
    *,
    now: datetime,
) -> DeviceView:
    if record.organization_id is None:
        raise ResourceNotFound("device_not_found")
    domain_device = Device(
        id=record.id,
        code=record.code,
        serial_number=record.serial_number,
        model_code=model.model_code,
        hardware_revision=model.hardware_revision,
        lifecycle=DeviceLifecycle(record.lifecycle),
        certificate_status=CertificateStatus(record.certificate_status),
        organization_id=record.organization_id,
        site_id=record.site_id,
        last_seen_at=record.last_seen_at,
    )
    return DeviceView(
        id=record.id,
        code=record.code,
        organization_id=record.organization_id,
        site_id=record.site_id,
        model_code=model.model_code,
        hardware_revision=model.hardware_revision,
        lifecycle=record.lifecycle,
        certificate_status=record.certificate_status,
        presence=domain_device.presence_at(now).value,
        last_seen_at=record.last_seen_at,
        reported_shadow_version=shadow.reported_version if shadow is not None else 0,
        reported_shadow=shadow.reported if shadow is not None else {},
        is_synthetic=record.is_synthetic,
        is_physical_hardware=record.is_physical_hardware,
        production_supported=record.production_supported,
    )


class PostgresControlPlane:
    """Translate Web use cases into RLS-scoped PostgreSQL transactions."""

    def __init__(self, settings: Settings) -> None:
        self._engine = create_engine(settings)
        self._sessions = create_session_factory(self._engine)
        self._database_role = settings.postgres_role

    async def close(self) -> None:
        await self._engine.dispose()

    async def list_devices(
        self,
        actor: Actor,
        *,
        target_organization_id: UUID | None,
        support_reason: str | None,
        cursor: str | None,
        limit: int,
        request_id: UUID,
        trace_id: str,
    ) -> DevicePage:
        organization_id = _authorized_organization(
            actor,
            target_organization_id=target_organization_id,
            permission=Permission.DEVICE_READ,
            support_reason=support_reason,
        )
        statement = (
            select(DeviceRecord, DeviceModelModel, DeviceShadowModel)
            .join(DeviceModelModel, DeviceModelModel.id == DeviceRecord.model_id)
            .outerjoin(DeviceShadowModel, DeviceShadowModel.device_id == DeviceRecord.id)
            .where(DeviceRecord.organization_id == organization_id)
            .order_by(DeviceRecord.code, DeviceRecord.id)
            .limit(limit + 1)
        )
        if cursor is not None:
            code, device_id = _decode_cursor(cursor)
            statement = statement.where(
                or_(
                    DeviceRecord.code > code,
                    and_(DeviceRecord.code == code, DeviceRecord.id > device_id),
                )
            )
        now = datetime.now(UTC)
        async with tenant_session(self._sessions, organization_id, self._database_role) as session:
            rows = (await session.execute(statement)).all()
            if Role.PLATFORM_SUPPORT in actor.roles:
                session.add(
                    AuditEventModel(
                        organization_id=organization_id,
                        actor_id=actor.actor_id,
                        action="support.device.list",
                        target_type="organization",
                        target_id=str(organization_id),
                        reason=(support_reason or "").strip(),
                        request_id=request_id,
                        trace_id=trace_id,
                    )
                )
        visible = rows[:limit]
        items = tuple(
            _device_view(record, model, shadow, now=now) for record, model, shadow in visible
        )
        next_cursor = None
        if len(rows) > limit and visible:
            next_cursor = _encode_cursor(visible[-1][0].code, visible[-1][0].id)
        return DevicePage(items=items, next_cursor=next_cursor)

    async def get_device(
        self,
        actor: Actor,
        device_id: UUID,
        *,
        target_organization_id: UUID | None,
        support_reason: str | None,
        request_id: UUID,
        trace_id: str,
    ) -> DeviceView:
        organization_id = _authorized_organization(
            actor,
            target_organization_id=target_organization_id,
            permission=Permission.DEVICE_READ,
            support_reason=support_reason,
        )
        statement = (
            select(DeviceRecord, DeviceModelModel, DeviceShadowModel)
            .join(DeviceModelModel, DeviceModelModel.id == DeviceRecord.model_id)
            .outerjoin(DeviceShadowModel, DeviceShadowModel.device_id == DeviceRecord.id)
            .where(
                DeviceRecord.id == device_id,
                DeviceRecord.organization_id == organization_id,
            )
        )
        async with tenant_session(self._sessions, organization_id, self._database_role) as session:
            row = (await session.execute(statement)).one_or_none()
            if row is None:
                raise ResourceNotFound("device_not_found")
            if Role.PLATFORM_SUPPORT in actor.roles:
                session.add(
                    AuditEventModel(
                        organization_id=organization_id,
                        actor_id=actor.actor_id,
                        action="support.device.read",
                        target_type="device",
                        target_id=str(device_id),
                        reason=(support_reason or "").strip(),
                        request_id=request_id,
                        trace_id=trace_id,
                    )
                )
        record, model, shadow = row
        return _device_view(record, model, shadow, now=datetime.now(UTC))

    async def create_command(self, actor: Actor, command_input: CommandInput) -> CommandCreation:
        organization_id = _authorized_organization(
            actor,
            target_organization_id=None,
            permission=Permission.COMMAND_CREATE,
        )
        if command_input.command_type != "refresh_shadow":
            raise OperationRejected("command_type_not_allowed")
        request = CommandRequest(
            organization_id=organization_id,
            device_id=command_input.device_id,
            idempotency_key=command_input.idempotency_key,
            requested_by=actor.actor_id,
            reason=command_input.reason,
            expires_at=command_input.expires_at,
            parameters=command_input.parameters,
        )
        try:
            async with tenant_session(
                self._sessions, organization_id, self._database_role
            ) as session:
                existing = await self._find_idempotent(session, organization_id, request)
                if existing is not None:
                    return CommandCreation(command=_command_view(existing), replayed=True)
                record = await session.scalar(
                    select(DeviceRecord)
                    .where(
                        DeviceRecord.id == command_input.device_id,
                        DeviceRecord.organization_id == organization_id,
                    )
                    .with_for_update()
                )
                if record is None or record.organization_id is None:
                    raise ResourceNotFound("device_not_found")
                domain_device = Device(
                    id=record.id,
                    code=record.code,
                    serial_number=record.serial_number,
                    model_code="not-required-for-control",
                    hardware_revision="not-required-for-control",
                    lifecycle=DeviceLifecycle(record.lifecycle),
                    certificate_status=CertificateStatus(record.certificate_status),
                    organization_id=record.organization_id,
                    site_id=record.site_id,
                    last_seen_at=record.last_seen_at,
                )
                snapshot = DeviceControlSnapshot.from_device(
                    domain_device,
                    presence=domain_device.presence_at(datetime.now(UTC)).value,
                )
                now = datetime.now(UTC)
                try:
                    command = create_refresh_shadow(
                        command_id=uuid7(),
                        request=request,
                        device=snapshot,
                        now=now,
                    ).transition(CommandState.APPROVED, at=now)
                except CommandPolicyViolation as exception:
                    raise OperationRejected(str(exception)) from exception
                self._stage_command_facts(
                    session,
                    command=command,
                    device_code=record.code,
                    command_input=command_input,
                )
            return CommandCreation(command=_command_view(command), replayed=False)
        except IntegrityError:
            async with tenant_session(
                self._sessions, organization_id, self._database_role
            ) as session:
                existing = await self._find_idempotent(session, organization_id, request)
                if existing is None:
                    raise
                return CommandCreation(command=_command_view(existing), replayed=True)

    async def _find_idempotent(
        self,
        session: AsyncSession,
        organization_id: UUID,
        request: CommandRequest,
    ) -> DeviceCommand | None:
        record = await session.scalar(
            select(DeviceCommandModel).where(
                DeviceCommandModel.organization_id == organization_id,
                DeviceCommandModel.idempotency_key == request.idempotency_key,
            )
        )
        if record is None:
            return None
        try:
            return resolve_idempotent_request(_as_domain_command(record), request)
        except CommandPolicyViolation as exception:
            raise IdempotencyConflict("idempotency_key_conflict") from exception

    @staticmethod
    def _stage_command_facts(
        session: AsyncSession,
        *,
        command: DeviceCommand,
        device_code: str,
        command_input: CommandInput,
    ) -> None:
        session.add(
            DeviceCommandModel(
                id=command.id,
                organization_id=command.organization_id,
                device_id=command.device_id,
                command_type=command.command_type,
                parameters=dict(command.parameters),
                idempotency_key=command.idempotency_key,
                request_fingerprint=command.request_fingerprint,
                requested_by=command.requested_by,
                reason=command.reason,
                expires_at=command.expires_at,
                state=command.state.value,
                safe_result={},
                created_at=command.created_at,
                updated_at=command.updated_at,
            )
        )
        session.add(
            AuditEventModel(
                organization_id=command.organization_id,
                actor_id=command.requested_by,
                action="device.command.create",
                target_type="device_command",
                target_id=str(command.id),
                reason=command.reason,
                after_state={
                    "command_type": command.command_type,
                    "device_id": device_code,
                    "state": command.state.value,
                },
                request_id=command_input.request_id,
                trace_id=command_input.trace_id,
            )
        )
        session.add(
            OutboxEventModel(
                organization_id=command.organization_id,
                event_type="device.command.created",
                schema_version=1,
                aggregate_type="device_command",
                aggregate_id=command.id,
                payload={"command_id": str(command.id), "device_id": device_code},
                occurred_at=command.created_at,
                available_at=command.created_at,
                attempt_count=0,
                state="pending",
            )
        )

    async def get_command(self, actor: Actor, command_id: UUID) -> CommandView:
        organization_id = _authorized_organization(
            actor,
            target_organization_id=None,
            permission=Permission.DEVICE_READ,
        )
        async with tenant_session(self._sessions, organization_id, self._database_role) as session:
            record = await session.scalar(
                select(DeviceCommandModel).where(
                    DeviceCommandModel.id == command_id,
                    DeviceCommandModel.organization_id == organization_id,
                )
            )
            if record is None:
                raise ResourceNotFound("command_not_found")
            return _command_view(_as_domain_command(record))
