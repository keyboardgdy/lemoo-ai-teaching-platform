# Compose

The root `compose.yaml` currently defines only the W2 `core` profile: PostgreSQL, Redis, MinIO and EMQX. Host ports bind to `127.0.0.1`; insecure MQTT is not published to the host. Application and observability profiles are added only by their traced work packages.

Use `task infra:config`, `task infra:up` and `task infra:down`. Do not run `down -v` unless deletion of the exact local development volumes is explicitly intended.
