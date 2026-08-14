"""Generate a local-only CA and mTLS identities for the Compose stack."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from ipaddress import IPv4Address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID, ObjectIdentifier

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / ".data" / "pki"
LOCAL_ORGANIZATION = "Lemoo LOCAL DEVELOPMENT ONLY"


@dataclass(frozen=True, slots=True)
class DevelopmentPki:
    """Paths to a complete local development trust bundle."""

    root_certificate: Path
    root_key: Path
    server_ca: Path
    server_certificate: Path
    server_key: Path
    client_ca: Path
    client_certificate: Path
    client_key: Path
    created: bool

    @property
    def files(self) -> tuple[Path, ...]:
        return (
            self.root_certificate,
            self.root_key,
            self.server_ca,
            self.server_certificate,
            self.server_key,
            self.client_ca,
            self.client_certificate,
            self.client_key,
        )


def _paths(output: Path, *, created: bool) -> DevelopmentPki:
    return DevelopmentPki(
        root_certificate=output / "dev-root-ca-cert.pem",
        root_key=output / "dev-root-ca-key.pem",
        server_ca=output / "emqx" / "ca-cert.pem",
        server_certificate=output / "emqx" / "server-cert.pem",
        server_key=output / "emqx" / "server-key.pem",
        client_ca=output / "smoke-client" / "ca-cert.pem",
        client_certificate=output / "smoke-client" / "client-cert.pem",
        client_key=output / "smoke-client" / "client-key.pem",
        created=created,
    )


def _certificate_is_current(path: Path, *, now: datetime) -> bool:
    certificate = x509.load_pem_x509_certificate(path.read_bytes())
    return (
        certificate.not_valid_before_utc
        <= now
        < certificate.not_valid_after_utc - timedelta(days=30)
    )


def _bundle_is_current(bundle: DevelopmentPki, *, now: datetime) -> bool:
    try:
        if not all(path.is_file() for path in bundle.files):
            return False
        if not all(
            _certificate_is_current(path, now=now)
            for path in (
                bundle.root_certificate,
                bundle.server_certificate,
                bundle.client_certificate,
            )
        ):
            return False
        root = x509.load_pem_x509_certificate(bundle.root_certificate.read_bytes())
        server = x509.load_pem_x509_certificate(bundle.server_certificate.read_bytes())
        client = x509.load_pem_x509_certificate(bundle.client_certificate.read_bytes())
        if server.issuer != root.subject or client.issuer != root.subject:
            return False
        for key_path in (bundle.root_key, bundle.server_key, bundle.client_key):
            serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    except (OSError, TypeError, ValueError, x509.ExtensionNotFound):
        return False
    return True


def _name(common_name: str) -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, LOCAL_ORGANIZATION),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )


def _private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65_537, key_size=3072)


def _write(path: Path, content: bytes, *, private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    if private:
        path.chmod(0o600)


def _key_bytes(key: rsa.RSAPrivateKey) -> bytes:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _leaf_certificate(
    *,
    subject: x509.Name,
    public_key: rsa.RSAPublicKey,
    issuer: x509.Name,
    issuer_key: rsa.RSAPrivateKey,
    now: datetime,
    usage: ObjectIdentifier,
    san: x509.SubjectAlternativeName | None = None,
) -> x509.Certificate:
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=None,
                decipher_only=None,
            ),
            critical=True,
        )
        .add_extension(x509.ExtendedKeyUsage([usage]), critical=False)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(public_key), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()),
            critical=False,
        )
    )
    if san is not None:
        builder = builder.add_extension(san, critical=False)
    return builder.sign(private_key=issuer_key, algorithm=hashes.SHA256())


def generate_development_pki(
    output: Path = DEFAULT_OUTPUT,
    *,
    now: datetime | None = None,
) -> DevelopmentPki:
    """Create or reuse a complete local-only trust bundle.

    Incomplete, corrupt, or near-expiry development bundles are replaced together so a leaf
    certificate is never accidentally paired with a different local CA.
    """

    observed_at = now or datetime.now(UTC)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    reusable = _paths(output, created=False)
    if _bundle_is_current(reusable, now=observed_at):
        return reusable

    root_key = _private_key()
    root_name = _name("Lemoo development root CA")
    root_certificate = (
        x509.CertificateBuilder()
        .subject_name(root_name)
        .issuer_name(root_name)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(observed_at - timedelta(minutes=5))
        .not_valid_after(observed_at + timedelta(days=5 * 365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=None,
                decipher_only=None,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(root_key.public_key()),
            critical=False,
        )
        .sign(private_key=root_key, algorithm=hashes.SHA256())
    )

    server_key = _private_key()
    server_certificate = _leaf_certificate(
        subject=_name("localhost"),
        public_key=server_key.public_key(),
        issuer=root_name,
        issuer_key=root_key,
        now=observed_at,
        usage=ExtendedKeyUsageOID.SERVER_AUTH,
        san=x509.SubjectAlternativeName(
            [x509.DNSName("localhost"), x509.IPAddress(IPv4Address("127.0.0.1"))]
        ),
    )
    client_key = _private_key()
    client_certificate = _leaf_certificate(
        subject=_name("lemoo-local-platform-smoke"),
        public_key=client_key.public_key(),
        issuer=root_name,
        issuer_key=root_key,
        now=observed_at,
        usage=ExtendedKeyUsageOID.CLIENT_AUTH,
    )

    created = _paths(output, created=True)
    ca_bytes = root_certificate.public_bytes(serialization.Encoding.PEM)
    _write(created.root_certificate, ca_bytes)
    _write(created.root_key, _key_bytes(root_key), private=True)
    _write(created.server_ca, ca_bytes)
    _write(
        created.server_certificate,
        server_certificate.public_bytes(serialization.Encoding.PEM),
    )
    _write(created.server_key, _key_bytes(server_key), private=True)
    _write(created.client_ca, ca_bytes)
    _write(
        created.client_certificate,
        client_certificate.public_bytes(serialization.Encoding.PEM),
    )
    _write(created.client_key, _key_bytes(client_key), private=True)
    return created


def main() -> None:
    bundle = generate_development_pki()
    status = "created" if bundle.created else "reused"
    relative = bundle.root_certificate.parent.relative_to(REPOSITORY_ROOT)
    print(f"development_pki={status} path={relative} production_supported=false")


if __name__ == "__main__":
    main()
