# Stage 1A Device API v1 contract

Status: `frozen` for `stage-1a-simulator-first`.

`openapi.v1.json` is the authoritative OpenAPI 3.1 contract for the synthetic device HTTPS boundary. `identity-policy.v1.json` freezes certificate identity, binding, rotation and revocation decisions. The auth fixtures are synthetic certificate observations, not keys or production PKI material; W8 generates ephemeral test certificates at runtime.

The boundary never accepts a Web Cookie, Bearer Token or MQTT credential. Provisioning uses a separate simulator bootstrap trust domain; all other routes require a per-device mTLS certificate whose verified SAN URI and status map to the path `device_id`.

Upload and download URL shapes are included so future clients cannot invent them independently, but both capabilities and every transfer purpose are disabled in Stage 1A. The contract does not enable Content, Diagnostics, Firmware/OTA or student audio transfer.

Run `task test:protocol` to validate the contract and negative identity matrix.
