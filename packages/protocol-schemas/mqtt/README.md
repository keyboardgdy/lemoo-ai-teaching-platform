# Stage 1A MQTT v1 contract

Status: `frozen` for `stage-1a-simulator-first`.

This directory is the authoritative MQTT boundary for the six synthetic devices in PILOT-001. It defines observable payloads, topics, QoS/retain/session behavior, device ACLs, limits, compatibility, and executable accepted/rejected fixtures.

The contract does not assert compatibility with physical hardware. Every message must carry `is_physical_hardware=false` and `production_supported=false`. Only `refresh_shadow` is allowed; Content, Teaching, AI, Diagnostic, Bulk Command and OTA topics or commands are not enabled by this contract.

Identity is derived from the client certificate. EMQX must bind certificate identity and MQTT Client ID to exactly one `device_id`; the Gateway must additionally require certificate identity, Client ID, Topic device ID, and payload `device_id` to match.

Compatibility rules:

- Topic major `v1` and `*.v1` message schemas are accepted.
- Unknown topic or schema major is rejected and audited.
- Additive optional fields require a new compatible schema revision; this frozen schema uses `additionalProperties=false` so unreviewed fields fail closed.
- Breaking changes create `v2`; v1 files and fixtures are never rewritten to carry new semantics.
- A repeated message is acknowledged without applying its business effect twice. A lower sequence in the same boot may be retained as an observation but cannot regress current state; a new `boot_id` starts a new ordering stream.
- Commands whose `expires_at` is not later than server receipt time are rejected with an `expired` ACK. Packets over 65,536 bytes are rejected before schema validation and audited.

Run `task test:protocol` to validate all schemas, policies, and fixtures.
