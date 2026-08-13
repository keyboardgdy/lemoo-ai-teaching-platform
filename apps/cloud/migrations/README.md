# Migrations

Alembic is locked as a dependency, but no business schema exists in W2. W6a must initialize migrations, empty-database upgrade tests, Reset/Seed and restore evidence as separate concerns. API and worker processes must never run migrations automatically.
