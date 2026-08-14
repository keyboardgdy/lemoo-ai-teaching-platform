# Lemoo Cloud

This Python project owns every cloud-side process entrypoint and the single
`uv.lock`. The Stage 1A slice now includes the pure device domain, PostgreSQL
migrations and forced tenant RLS, synthetic browser sessions, device
list/detail, and the allowlisted `refresh_shadow` command with atomic audit and
outbox facts.

Run from the repository root through `task` so local and CI commands remain
identical. Start PostgreSQL with `task infra:up`, then run `task seed` before the
API. Every capability remains Simulator-only, synthetic-only and
non-production.
