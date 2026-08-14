# Migrations

Stage 1A owns one Alembic history rooted at `0001_stage1a_core`. It creates the
12 Simulator-only control-plane tables, a default telemetry partition, forced
tenant RLS policies, and the append-only audit trigger.

Run migrations explicitly from the repository root:

```shell
task migrate
```

For the local application, provision the constrained runtime role and seed the
fixed synthetic pilot facts:

```shell
task database:setup
task seed
```

Exercise the migration lifecycle against a real local PostgreSQL instance:

```shell
task infra:up
task migrate:test
```

The test creates an isolated temporary database and role, then verifies empty
upgrade, repeat upgrade, tenant isolation, fail-closed tenant context,
append-only audit enforcement, downgrade, and re-upgrade. It removes only those
generated test resources afterward. API and worker processes never run
migrations automatically.
