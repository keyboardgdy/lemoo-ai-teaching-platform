"""Local-only PKI generation tests for the W7a Compose boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from ipaddress import IPv4Address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.oid import ExtendedKeyUsageOID
from scripts.generate_dev_pki import generate_development_pki


def test_generated_pki_has_separate_ca_server_and_smoke_client_identities(
    tmp_path: Path,
) -> None:
    result = generate_development_pki(
        tmp_path,
        now=datetime(2026, 8, 14, 3, 0, tzinfo=UTC),
    )

    assert result.created is True
    assert all(path.is_file() for path in result.files)
    assert result.root_key != result.server_key != result.client_key

    root = x509.load_pem_x509_certificate(result.root_certificate.read_bytes())
    server = x509.load_pem_x509_certificate(result.server_certificate.read_bytes())
    client = x509.load_pem_x509_certificate(result.client_certificate.read_bytes())
    assert root.extensions.get_extension_for_class(x509.BasicConstraints).value.ca is True
    assert server.issuer == client.issuer == root.subject
    assert "LOCAL DEVELOPMENT ONLY" in root.subject.rfc4514_string()

    server_names = server.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert "localhost" in server_names.get_values_for_type(x509.DNSName)
    assert IPv4Address("127.0.0.1") in server_names.get_values_for_type(x509.IPAddress)

    server_usage = server.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
    client_usage = client.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
    assert ExtendedKeyUsageOID.SERVER_AUTH in server_usage
    assert ExtendedKeyUsageOID.CLIENT_AUTH in client_usage

    for key_path in (result.root_key, result.server_key, result.client_key):
        assert load_pem_private_key(key_path.read_bytes(), password=None) is not None


def test_generation_is_idempotent_while_the_complete_bundle_is_valid(tmp_path: Path) -> None:
    now = datetime(2026, 8, 14, 3, 0, tzinfo=UTC)
    first = generate_development_pki(tmp_path, now=now)
    first_serial = x509.load_pem_x509_certificate(
        first.server_certificate.read_bytes()
    ).serial_number

    second = generate_development_pki(tmp_path, now=now)
    second_serial = x509.load_pem_x509_certificate(
        second.server_certificate.read_bytes()
    ).serial_number

    assert second.created is False
    assert second_serial == first_serial
