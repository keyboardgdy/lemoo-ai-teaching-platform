"""Deterministic helpers for the local-only W7b3 artifact verification gate."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

IMMUTABLE_REFERENCE = re.compile(r"^[a-z0-9][a-z0-9._/-]*@sha256:([a-f0-9]{64})$")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / ".tmp" / "supply-chain"


@dataclass(frozen=True, slots=True)
class ImageSpec:
    """One test-only image and its immutable build inputs."""

    name: str
    dockerfile: str
    base_references: tuple[str, ...]


IMAGES = (
    ImageSpec(
        name="lemoo-api",
        dockerfile="docker/api.Dockerfile",
        base_references=(
            "python@sha256:23c59390fc717bf09f9336908199a0ae75d9c4264bf296123f94ad772fea3b52",
        ),
    ),
    ImageSpec(
        name="lemoo-web",
        dockerfile="docker/web.Dockerfile",
        base_references=(
            "node@sha256:48abc13a19400ca3985071e287bd405a1d99306770eb81d61202fb6b65cf0b57",
            "golang@sha256:622e56dbc11a8cfe87cafa2331e9a201877271cbff918af53d3be315f3da88cc",
            "alpine@sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40",
        ),
    ),
)


def require_digest_reference(reference: str) -> str:
    """Return the digest body or reject a mutable/malformed image reference."""

    match = IMMUTABLE_REFERENCE.fullmatch(reference)
    if match is None:
        raise ValueError(
            "immutable image reference required: name@sha256:<64 lowercase hex>"
        )
    return match.group(1)


def sha256_file(path: Path) -> str:
    """Hash an artifact without loading it into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for block in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_hash_manifest(manifest_path: Path, artifact_root: Path) -> None:
    """Fail closed if an artifact is missing, escapes the root, or was changed."""

    raw = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
    if not isinstance(raw, dict) or not raw:
        raise ValueError("artifact hash manifest must be a non-empty object")
    entries = cast(dict[object, object], raw)
    root = artifact_root.resolve()
    for relative_name, expected in entries.items():
        if not isinstance(relative_name, str) or not isinstance(expected, str):
            raise TypeError("artifact hash manifest entries must be strings")
        artifact = (root / relative_name).resolve()
        if artifact.parent != root or not artifact.is_file():
            raise ValueError(f"artifact missing or outside root: {relative_name}")
        observed = sha256_file(artifact)
        if observed != expected:
            raise ValueError(f"artifact digest mismatch: {relative_name}")


def create_provenance(
    *,
    image_name: str,
    image_digest: str,
    revision: str,
    dockerfile: str,
    builder_id: str,
    invocation_id: str,
    base_references: tuple[str, ...] = (),
) -> dict[str, object]:
    """Create the stable SLSA v1/in-toto envelope for one test image."""

    digest_body = require_digest_reference(f"{image_name}@{image_digest}")
    dependencies: list[dict[str, object]] = [
        {
            "uri": "git+https://github.com/keyboardgdy/lemoo-ai-teaching-platform",
            "digest": {"gitCommit": revision},
        }
    ]
    for reference in base_references:
        base_digest = require_digest_reference(reference)
        base_name = reference.split("@", maxsplit=1)[0]
        dependencies.append(
            {"uri": f"docker://{base_name}", "digest": {"sha256": base_digest}}
        )
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": image_name, "digest": {"sha256": digest_body}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://github.com/docker/buildx",
                "externalParameters": {
                    "dockerfile": dockerfile,
                    "platform": "linux/amd64",
                    "stage": "Stage 1A Simulator-only non-production",
                },
                "internalParameters": {},
                "resolvedDependencies": dependencies,
            },
            "runDetails": {
                "builder": {"id": builder_id},
                "metadata": {"invocationId": invocation_id},
            },
        },
    }


def _tool(name: str, environment_name: str, local_name: str | None = None) -> str:
    configured = os.environ.get(environment_name)
    if configured:
        candidate = Path(configured)
        if candidate.is_file():
            return str(candidate)
        raise RuntimeError(f"Configured tool does not exist: {environment_name}")
    discovered = shutil.which(name)
    if discovered:
        return discovered
    local = REPOSITORY_ROOT / ".tools" / "supply-chain" / (local_name or name)
    if local.is_file():
        return str(local)
    raise RuntimeError(f"Required supply-chain tool is unavailable: {name}")


def _run(
    command: list[str],
    *,
    environment: dict[str, str] | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=capture,
        text=True,
    )


def _expect_failure(command: list[str], *, environment: dict[str, str]) -> None:
    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        raise RuntimeError("negative supply-chain verification unexpectedly succeeded")


def _json(command: list[str]) -> object:
    output = _run(command, capture=True).stdout
    return cast(object, json.loads(output))


def _prepare_output(path: Path) -> Path:
    resolved = path.resolve()
    expected_parent = (REPOSITORY_ROOT / ".tmp").resolve()
    if resolved.parent != expected_parent or resolved.name != "supply-chain":
        raise ValueError(
            "supply-chain output must be the repository .tmp/supply-chain directory"
        )
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)
    return resolved


def _git_revision() -> str:
    status = _run(["git", "status", "--porcelain"], capture=True).stdout.strip()
    if status:
        raise RuntimeError(
            "supply-chain verification requires a clean committed worktree"
        )
    revision = _run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()
    if re.fullmatch(r"[a-f0-9]{40}", revision) is None:
        raise RuntimeError("unable to resolve the committed source revision")
    return revision


def _builder_identity(revision: str) -> tuple[str, str]:
    server = os.environ.get("GITHUB_SERVER_URL")
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if server and repository and run_id:
        return f"{server}/{repository}/actions/runs/{run_id}", run_id
    return "local://docker-buildx", f"local-{revision[:12]}"


def _build_image(spec: ImageSpec, revision: str, output: Path) -> dict[str, str]:
    tag = f"{spec.name}:w7b3-{revision[:12]}"
    metadata = output / f"{spec.name}.build.json"
    _run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/amd64",
            "--load",
            "--provenance=mode=max",
            "--build-arg",
            f"VCS_REF={revision}",
            "--metadata-file",
            str(metadata),
            "--tag",
            tag,
            "--file",
            spec.dockerfile,
            ".",
        ]
    )
    inspected = _json(["docker", "image", "inspect", tag])
    if not isinstance(inspected, list):
        raise TypeError(f"unexpected Docker inspect response for {spec.name}")
    inspected_items = cast(list[object], inspected)
    if len(inspected_items) != 1:
        raise RuntimeError(f"unexpected Docker inspect response for {spec.name}")
    image = cast(dict[str, object], inspected_items[0])
    config = cast(dict[str, object], image.get("Config"))
    user = config.get("User")
    if not isinstance(user, str) or user in {"", "0", "root", "0:0", "root:root"}:
        raise RuntimeError(f"runtime image must use a non-root user: {spec.name}")
    if not isinstance(config.get("Healthcheck"), dict):
        raise TypeError(f"runtime image must define a health check: {spec.name}")
    labels = cast(dict[str, object], config.get("Labels"))
    if labels.get("org.opencontainers.image.revision") != revision:
        raise RuntimeError(f"image revision label mismatch: {spec.name}")
    repo_digests = cast(list[object], image.get("RepoDigests"))
    prefix = f"{spec.name}@sha256:"
    references = [
        item
        for item in repo_digests
        if isinstance(item, str) and item.startswith(prefix)
    ]
    if len(references) != 1:
        raise RuntimeError(
            f"image does not have exactly one immutable digest: {spec.name}"
        )
    digest = f"sha256:{require_digest_reference(references[0])}"
    archive = output / f"{spec.name}.image.tar"
    _run(["docker", "image", "save", "--output", str(archive), tag])
    return {
        "tag": tag,
        "reference": references[0],
        "digest": digest,
        "archive": archive.name,
        "user": user,
    }


def _generate_and_scan(
    spec: ImageSpec,
    image: dict[str, str],
    *,
    revision: str,
    builder_id: str,
    invocation_id: str,
    output: Path,
    syft: str,
    trivy: str,
) -> tuple[Path, Path, Path]:
    archive = output / image["archive"]
    sbom = output / f"{spec.name}.cdx.json"
    _run(
        [
            syft,
            "scan",
            f"docker-archive:{archive}",
            "--output",
            f"cyclonedx-json={sbom}",
        ]
    )
    sbom_document = cast(object, json.loads(sbom.read_text(encoding="utf-8")))
    if not isinstance(sbom_document, dict):
        raise TypeError(f"invalid CycloneDX SBOM: {spec.name}")
    sbom_fields = cast(dict[object, object], sbom_document)
    if sbom_fields.get("bomFormat") != "CycloneDX":
        raise RuntimeError(f"invalid CycloneDX SBOM: {spec.name}")
    if not isinstance(sbom_fields.get("components"), list):
        raise TypeError(f"CycloneDX SBOM has no component inventory: {spec.name}")

    scan = output / f"{spec.name}.trivy.json"
    _run(
        [
            trivy,
            "image",
            "--input",
            str(archive),
            "--scanners",
            "vuln",
            "--severity",
            "HIGH,CRITICAL",
            "--ignore-unfixed",
            "--exit-code",
            "1",
            "--format",
            "json",
            "--output",
            str(scan),
        ]
    )

    provenance = output / f"{spec.name}.provenance.json"
    provenance.write_text(
        json.dumps(
            create_provenance(
                image_name=spec.name,
                image_digest=image["digest"],
                revision=revision,
                dockerfile=spec.dockerfile,
                builder_id=builder_id,
                invocation_id=invocation_id,
                base_references=spec.base_references,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return sbom, scan, provenance


def _cosign_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["COSIGN_PASSWORD"] = "stage1a-ephemeral-test-only"
    return environment


def _sign_and_verify(
    *,
    cosign: str,
    artifacts: list[Path],
    output: Path,
    report_payload: dict[str, object],
) -> Path:
    environment = _cosign_environment()
    signer = output / "ephemeral-test-signer"
    wrong_signer = output / "ephemeral-wrong-signer"
    signing_config = output / "offline-signing-config.json"
    private_keys = [
        signer.with_suffix(".key"),
        wrong_signer.with_suffix(".key"),
    ]

    def sign_and_verify(artifact: Path) -> Path:
        bundle = output / f"{artifact.name}.sigstore.json"
        _run(
            [
                cosign,
                "sign-blob",
                "--yes",
                "--key",
                str(signer.with_suffix(".key")),
                "--signing-config",
                str(signing_config),
                "--bundle",
                str(bundle),
                str(artifact),
            ],
            environment=environment,
        )
        _run(
            [
                cosign,
                "verify-blob",
                "--insecure-ignore-tlog",
                "--key",
                str(signer.with_suffix(".pub")),
                "--bundle",
                str(bundle),
                str(artifact),
            ],
            environment=environment,
        )
        return bundle

    try:
        _run(
            [cosign, "signing-config", "create", "--out", str(signing_config)],
            environment=environment,
        )
        for prefix in (signer, wrong_signer):
            _run(
                [cosign, "generate-key-pair", "--output-key-prefix", str(prefix)],
                environment=environment,
            )
        bundles: dict[str, str] = {}
        for artifact in artifacts:
            bundle = sign_and_verify(artifact)
            bundles[artifact.name] = bundle.name

        target = artifacts[0]
        target_bundle = output / bundles[target.name]
        tampered = output / "negative-tampered-artifact"
        shutil.copyfile(target, tampered)
        with tampered.open("ab") as stream:
            stream.write(b"tampered")
        _expect_failure(
            [
                cosign,
                "verify-blob",
                "--insecure-ignore-tlog",
                "--key",
                str(signer.with_suffix(".pub")),
                "--bundle",
                str(target_bundle),
                str(tampered),
            ],
            environment=environment,
        )
        tampered.unlink()
        _expect_failure(
            [
                cosign,
                "verify-blob",
                "--insecure-ignore-tlog",
                "--key",
                str(wrong_signer.with_suffix(".pub")),
                "--bundle",
                str(target_bundle),
                str(target),
            ],
            environment=environment,
        )
        verification: dict[str, object] = {
            "bundles": bundles,
            "tampered_artifact_rejected": True,
            "wrong_signer_rejected": True,
            "mutable_reference_rejected": True,
        }
        report = output / "verification-report.json"
        report.write_text(
            json.dumps(
                report_payload | {"verification": verification},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        sign_and_verify(report)
        return report
    finally:
        for key in private_keys:
            key.unlink(missing_ok=True)
        signing_config.unlink(missing_ok=True)


def verify_supply_chain(output_path: Path = DEFAULT_OUTPUT) -> Path:
    """Build, inventory, scan, sign, and negatively verify both Stage 1A images."""

    output = _prepare_output(output_path)
    revision = _git_revision()
    builder_id, invocation_id = _builder_identity(revision)
    syft = _tool("syft", "LEMOO_SYFT_PATH", "syft.exe")
    cosign = _tool("cosign", "LEMOO_COSIGN_PATH", "cosign-windows-amd64.exe")
    trivy = _tool("trivy", "LEMOO_TRIVY_PATH", "trivy.exe")

    try:
        require_digest_reference("lemoo-api:latest")
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "mutable image tag negative verification unexpectedly succeeded"
        )

    images: list[dict[str, str]] = []
    signed_artifacts: list[Path] = []
    for spec in IMAGES:
        image = _build_image(spec, revision, output)
        sbom, scan, provenance = _generate_and_scan(
            spec,
            image,
            revision=revision,
            builder_id=builder_id,
            invocation_id=invocation_id,
            output=output,
            syft=syft,
            trivy=trivy,
        )
        images.append(image)
        signed_artifacts.extend((output / image["archive"], sbom, scan, provenance))

    hashes = output / "artifact-hashes.json"
    hashes.write_text(
        json.dumps(
            {artifact.name: sha256_file(artifact) for artifact in signed_artifacts},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    verify_hash_manifest(hashes, output)
    signed_artifacts.append(hashes)
    report = _sign_and_verify(
        cosign=cosign,
        artifacts=signed_artifacts,
        output=output,
        report_payload={
            "schema_version": 1,
            "scope": "Stage 1A Simulator-only non-production",
            "revision": revision,
            "builder": builder_id,
            "invocation_id": invocation_id,
            "images": images,
            "signer": {
                "type": "ephemeral in-run Cosign test identity",
                "public_key": "ephemeral-test-signer.pub",
                "wrong_public_key": "ephemeral-wrong-signer.pub",
                "private_key_retention": "destroyed before gate completion",
            },
            "production_authorized": False,
        },
    )
    if any(output.glob("*.key")):
        raise RuntimeError("ephemeral signing private key was not destroyed")
    print(
        "image_verification=pass images=2 sbom=cyclonedx provenance=slsa-v1 "
        f"signed={len(signed_artifacts) + 1} negatives=3 "
        "report_bundle=verification-report.json.sigstore.json"
    )
    return report


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: python scripts/supply_chain.py")
    verify_supply_chain()


__all__ = [
    "create_provenance",
    "require_digest_reference",
    "sha256_file",
    "verify_hash_manifest",
    "verify_supply_chain",
]


if __name__ == "__main__":
    main()
