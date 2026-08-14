# OpenAPI status

Status: `stage_1a_web_frozen`

The exported OpenAPI 3.1 document is authoritative for the Stage 1A
Simulator-only browser boundary: synthetic sessions, device list/detail and the
single-device `refresh_shadow` command. Device mTLS remains a separate contract
under `packages/protocol-schemas/device-api`. Content, teaching, AI,
diagnostics, bulk commands, OTA and production surfaces remain absent.
