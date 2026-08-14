# Local Compose runbook

The root `compose.yaml` defines the Stage 1A `core` profile: PostgreSQL, Redis, MinIO and
EMQX. Every published port binds to `127.0.0.1`; insecure MQTT is not published. The local
MQTT endpoint is `localhost:58883` and requires mutual TLS.

## First start

1. Run `task bootstrap`. This creates `.env` from `.env.example` only when it is absent and
   generates a local development CA under ignored `.data/pki/`.
2. Run `task infra:up`. Compose waits for all four service health checks and then completes an
   EMQX TLS handshake using the dedicated `lemoo-local-platform-smoke` client identity.
3. Run `task seed` before starting the Web/API device workspace.
4. Run `task dev` for the supported Windows/Linux development entrypoint.

The PKI generator reuses a complete bundle until a certificate is corrupt, incomplete or within
30 days of expiry. When it regenerates, it replaces the complete local bundle so leaf identities
cannot be paired with the wrong CA. The generated subject is marked `LOCAL DEVELOPMENT ONLY`;
these credentials are not device identities and are never valid for production.

## Operations

- `task infra:smoke` repeats the mTLS handshake without recreating containers.
- `task infra:down` stops services while preserving named data volumes.
- After a Docker Engine restart, run `task infra:up` again and require its health/TLS checks to
  pass before development.
- Do not run `down -v` unless deletion of the exact local development volumes is explicitly
  intended.
- Never copy `.data/pki/`, `.env`, database dumps or runtime logs into Git.

Application, observability and production profiles are introduced only by traced work packages.
