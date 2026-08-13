# EMQX boundary

W2 starts EMQX internally with anonymous access disabled and exposes only the loopback dashboard. MQTT TLS, mTLS identity mapping, ACLs and port 8883 are introduced by G2-Device work; port 1883 is never published to the host by this baseline.
