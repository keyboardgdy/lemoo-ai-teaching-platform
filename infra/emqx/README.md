# EMQX local boundary

W7a exposes the EMQX Dashboard and MQTT TLS listener only on loopback. MQTT uses container port
8883 and host port 58883 by default. The listener verifies the local development CA and rejects a
TLS client that presents no certificate. Port 1883 is never published to the host.

The W7a smoke certificate proves only the local TLS platform path. It is deliberately named
`lemoo-local-platform-smoke`; it is not one of the six PILOT-001 devices and grants no topic
authorization. Per-device certificate mapping, Client ID binding, ACL tests, revocation and MQTT
application traffic remain W8a/W8b work.

Source material for the listener configuration is the EMQX 5 documentation on environment
variable mapping and two-way TLS. The Compose configuration keeps certificate paths immutable and
mounts the private key through a Compose secret rather than embedding it in YAML or environment
variables.
