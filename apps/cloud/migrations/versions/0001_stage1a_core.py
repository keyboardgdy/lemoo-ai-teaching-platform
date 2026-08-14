"""Create the Stage 1A synthetic device-cloud facts.

Revision ID: 0001_stage1a_core
Revises: None
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001_stage1a_core"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CREATE_STATEMENTS = (
    """
    CREATE TABLE organizations (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      code text NOT NULL UNIQUE,
      name text NOT NULL,
      is_synthetic boolean NOT NULL DEFAULT true CHECK (is_synthetic),
      production_supported boolean NOT NULL DEFAULT false CHECK (NOT production_supported),
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE sites (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
      code text NOT NULL,
      name text NOT NULL,
      is_synthetic boolean NOT NULL DEFAULT true CHECK (is_synthetic),
      production_supported boolean NOT NULL DEFAULT false CHECK (NOT production_supported),
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT uq_sites_organization_id_code UNIQUE (organization_id, code)
    )
    """,
    "CREATE INDEX ix_sites_organization_id ON sites (organization_id)",
    "CREATE INDEX ix_sites_organization_id_code ON sites (organization_id, code)",
    """
    CREATE TABLE device_models (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      model_code text NOT NULL,
      hardware_revision text NOT NULL,
      capabilities jsonb NOT NULL DEFAULT '{}'::jsonb,
      is_synthetic boolean NOT NULL DEFAULT true CHECK (is_synthetic),
      production_supported boolean NOT NULL DEFAULT false CHECK (NOT production_supported),
      created_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT uq_device_models_model_code_hardware_revision UNIQUE (model_code, hardware_revision)
    )
    """,
    """
    CREATE TABLE devices (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid REFERENCES organizations(id) ON DELETE RESTRICT,
      site_id uuid REFERENCES sites(id) ON DELETE RESTRICT,
      model_id uuid NOT NULL REFERENCES device_models(id) ON DELETE RESTRICT,
      code text NOT NULL UNIQUE,
      serial_number text NOT NULL UNIQUE,
      lifecycle text NOT NULL CHECK (lifecycle IN ('manufactured','provisioned','inventory','assigned','active','maintenance','suspended','retired')),
      certificate_status text NOT NULL CHECK (certificate_status IN ('active','suspended','revoked','expired')),
      last_seen_at timestamptz,
      boot_id text,
      last_sequence bigint CHECK (last_sequence >= 0),
      is_synthetic boolean NOT NULL DEFAULT true CHECK (is_synthetic),
      is_physical_hardware boolean NOT NULL DEFAULT false CHECK (NOT is_physical_hardware),
      production_supported boolean NOT NULL DEFAULT false CHECK (NOT production_supported),
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_devices_organization_id ON devices (organization_id)",
    "CREATE INDEX ix_devices_model_id ON devices (model_id)",
    "CREATE INDEX ix_devices_organization_id_site_id_code ON devices (organization_id, site_id, code)",
    """
    CREATE TABLE device_credentials (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id),
      device_id uuid NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
      certificate_serial text NOT NULL UNIQUE,
      san_uri text NOT NULL UNIQUE,
      status text NOT NULL CHECK (status IN ('active','suspended','revoked','expired')),
      not_before timestamptz NOT NULL,
      not_after timestamptz NOT NULL CHECK (not_after > not_before),
      revoked_at timestamptz,
      revocation_reason text,
      created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_device_credentials_organization_id ON device_credentials (organization_id)",
    "CREATE INDEX ix_device_credentials_organization_id_device_id ON device_credentials (organization_id, device_id)",
    """
    CREATE TABLE device_shadows (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id),
      device_id uuid NOT NULL UNIQUE REFERENCES devices(id) ON DELETE CASCADE,
      reported_version bigint NOT NULL DEFAULT 0 CHECK (reported_version >= 0),
      reported jsonb NOT NULL DEFAULT '{}'::jsonb,
      desired_version bigint NOT NULL DEFAULT 0 CHECK (desired_version >= 0),
      desired jsonb NOT NULL DEFAULT '{}'::jsonb,
      reported_at timestamptz,
      updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_device_shadows_organization_id ON device_shadows (organization_id)",
    """
    CREATE TABLE device_telemetry (
      id uuid NOT NULL DEFAULT uuidv7(),
      received_at timestamptz NOT NULL,
      organization_id uuid NOT NULL REFERENCES organizations(id),
      device_id uuid NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
      message_id uuid NOT NULL,
      occurred_at timestamptz NOT NULL,
      boot_id text NOT NULL,
      sequence bigint NOT NULL CHECK (sequence >= 0),
      metrics jsonb NOT NULL,
      PRIMARY KEY (id, received_at),
      CONSTRAINT uq_device_telemetry_message UNIQUE (device_id, message_id, received_at)
    ) PARTITION BY RANGE (received_at)
    """,
    "CREATE TABLE device_telemetry_default PARTITION OF device_telemetry DEFAULT",
    "CREATE INDEX ix_device_telemetry_organization_id ON device_telemetry (organization_id)",
    "CREATE INDEX ix_device_telemetry_organization_id_received_at ON device_telemetry (organization_id, received_at)",
    "CREATE INDEX ix_device_telemetry_device_id_received_at ON device_telemetry (device_id, received_at)",
    """
    CREATE TABLE device_events (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id),
      device_id uuid NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
      message_id uuid NOT NULL,
      event_type text NOT NULL,
      severity text NOT NULL CHECK (severity IN ('info','warning','critical')),
      occurred_at timestamptz NOT NULL,
      received_at timestamptz NOT NULL,
      context jsonb NOT NULL DEFAULT '{}'::jsonb,
      CONSTRAINT uq_device_events_device_id_message_id UNIQUE (device_id, message_id)
    )
    """,
    "CREATE INDEX ix_device_events_organization_id ON device_events (organization_id)",
    "CREATE INDEX ix_device_events_organization_id_occurred_at ON device_events (organization_id, occurred_at)",
    """
    CREATE TABLE alerts (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id),
      device_id uuid NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
      event_id uuid NOT NULL REFERENCES device_events(id) ON DELETE CASCADE,
      fingerprint text NOT NULL,
      severity text NOT NULL CHECK (severity IN ('warning','critical')),
      state text NOT NULL CHECK (state IN ('open','acknowledged','resolved')),
      created_at timestamptz NOT NULL DEFAULT now(),
      acknowledged_at timestamptz,
      CONSTRAINT uq_alerts_organization_id_fingerprint UNIQUE (organization_id, fingerprint)
    )
    """,
    "CREATE INDEX ix_alerts_organization_id ON alerts (organization_id)",
    "CREATE INDEX ix_alerts_organization_id_state_created_at ON alerts (organization_id, state, created_at)",
    """
    CREATE TABLE device_commands (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id),
      device_id uuid NOT NULL REFERENCES devices(id) ON DELETE RESTRICT,
      command_type text NOT NULL CHECK (command_type = 'refresh_shadow'),
      parameters jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (parameters = '{}'::jsonb),
      idempotency_key uuid NOT NULL,
      request_fingerprint text NOT NULL,
      requested_by text NOT NULL,
      reason text NOT NULL CHECK (length(reason) BETWEEN 3 AND 240),
      expires_at timestamptz NOT NULL,
      state text NOT NULL CHECK (state IN ('created','approved','published','accepted','running','succeeded','failed','timed_out','expired','cancelled')),
      result_code text,
      safe_result jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT uq_device_commands_organization_id_idempotency_key UNIQUE (organization_id, idempotency_key)
    )
    """,
    "CREATE INDEX ix_device_commands_organization_id ON device_commands (organization_id)",
    "CREATE INDEX ix_device_commands_organization_id_created_at ON device_commands (organization_id, created_at)",
    "CREATE INDEX ix_device_commands_device_id_created_at ON device_commands (device_id, created_at)",
    """
    CREATE TABLE audit_events (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id),
      actor_id text NOT NULL,
      action text NOT NULL,
      target_type text NOT NULL,
      target_id text NOT NULL,
      reason text NOT NULL CHECK (length(reason) BETWEEN 3 AND 240),
      before_state jsonb,
      after_state jsonb,
      request_id uuid NOT NULL,
      trace_id text NOT NULL,
      occurred_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ix_audit_events_organization_id ON audit_events (organization_id)",
    "CREATE INDEX ix_audit_events_organization_id_occurred_at ON audit_events (organization_id, occurred_at)",
    "CREATE INDEX ix_audit_events_actor_id_occurred_at ON audit_events (actor_id, occurred_at)",
    """
    CREATE TABLE outbox_events (
      id uuid PRIMARY KEY DEFAULT uuidv7(),
      organization_id uuid NOT NULL REFERENCES organizations(id),
      event_type text NOT NULL,
      schema_version integer NOT NULL DEFAULT 1 CHECK (schema_version = 1),
      aggregate_type text NOT NULL,
      aggregate_id uuid NOT NULL,
      payload jsonb NOT NULL,
      occurred_at timestamptz NOT NULL DEFAULT now(),
      available_at timestamptz NOT NULL DEFAULT now(),
      attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 10),
      state text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','claimed','dispatched','dead_letter')),
      last_error_code text
    )
    """,
    "CREATE INDEX ix_outbox_events_organization_id ON outbox_events (organization_id)",
    "CREATE INDEX ix_outbox_events_state_available_at ON outbox_events (state, available_at)",
    "CREATE INDEX ix_outbox_events_organization_id_occurred_at ON outbox_events (organization_id, occurred_at)",
)

RLS_STATEMENTS = (
    'ALTER TABLE "organizations" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "organizations" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_organizations ON organizations USING (id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "sites" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "sites" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_sites ON sites USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "devices" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "devices" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_devices ON devices USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "device_credentials" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "device_credentials" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_device_credentials ON device_credentials USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "device_shadows" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "device_shadows" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_device_shadows ON device_shadows USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "device_telemetry" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "device_telemetry" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_device_telemetry ON device_telemetry USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "device_events" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "device_events" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_device_events ON device_events USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "alerts" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "alerts" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_alerts ON alerts USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "device_commands" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "device_commands" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_device_commands ON device_commands USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "audit_events" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "audit_events" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_audit_events ON audit_events USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
    'ALTER TABLE "outbox_events" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "outbox_events" FORCE ROW LEVEL SECURITY',
    "CREATE POLICY tenant_isolation_outbox_events ON outbox_events USING (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid) WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid)",
)

AUDIT_IMMUTABILITY_STATEMENTS = (
    """
    CREATE FUNCTION prevent_audit_mutation() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      RAISE EXCEPTION 'audit_events are append-only' USING ERRCODE = '55000';
    END
    $$
    """,
    """
    CREATE TRIGGER audit_events_immutable
    BEFORE UPDATE OR DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation()
    """,
)


def upgrade() -> None:
    for statement in CREATE_STATEMENTS:
        op.execute(statement)
    for statement in RLS_STATEMENTS:
        op.execute(statement)
    for statement in AUDIT_IMMUTABILITY_STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_events_immutable ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_mutation()")
    for table_name in (
        "outbox_events",
        "audit_events",
        "device_commands",
        "alerts",
        "device_events",
        "device_telemetry",
        "device_shadows",
        "device_credentials",
        "devices",
        "device_models",
        "sites",
        "organizations",
    ):
        op.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
