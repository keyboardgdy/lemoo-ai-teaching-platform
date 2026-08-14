"""Verify the local EMQX listener requires and accepts the development mTLS identity."""

from __future__ import annotations

import socket
import ssl
from pathlib import Path

from generate_dev_pki import DEFAULT_OUTPUT

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _env_value(name: str, default: str) -> str:
    env_file = REPOSITORY_ROOT / ".env"
    if not env_file.is_file():
        return default
    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == name:
            return value.strip()
    return default


def verify_emqx_mtls(*, port: int, pki_root: Path = DEFAULT_OUTPUT) -> str:
    ca_file = pki_root / "smoke-client" / "ca-cert.pem"
    anonymous_context = ssl.create_default_context(
        ssl.Purpose.SERVER_AUTH, cafile=str(ca_file)
    )
    anonymous_context.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        with (
            socket.create_connection(("127.0.0.1", port), timeout=5) as connection,
            anonymous_context.wrap_socket(
                connection, server_hostname="localhost"
            ) as anonymous,
        ):
            anonymous.settimeout(1)
            if anonymous.recv(1) == b"":
                raise ssl.SSLError("server closed the unauthenticated connection")
    except (ConnectionResetError, ssl.SSLError):
        pass
    except TimeoutError as exception:
        raise RuntimeError(
            "EMQX kept a TLS client without a certificate connected"
        ) from exception
    else:
        raise RuntimeError(
            "EMQX accepted a TLS client without the required certificate"
        )

    context = ssl.create_default_context(
        ssl.Purpose.SERVER_AUTH,
        cafile=str(ca_file),
    )
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(
        certfile=pki_root / "smoke-client" / "client-cert.pem",
        keyfile=pki_root / "smoke-client" / "client-key.pem",
    )
    with (
        socket.create_connection(("127.0.0.1", port), timeout=5) as connection,
        context.wrap_socket(connection, server_hostname="localhost") as secured,
    ):
        peer = secured.getpeercert()
        if not peer:
            raise RuntimeError("EMQX did not present a verified server certificate")
        return secured.version()


def main() -> None:
    port = int(_env_value("LEMOO_EMQX_MQTT_TLS_PORT", "58883"))
    version = verify_emqx_mtls(port=port)
    print(
        f"local_tls=pass service=emqx port={port} version={version} "
        "mutual_authentication=true production_supported=false"
    )


if __name__ == "__main__":
    main()
