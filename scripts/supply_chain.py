"""Deterministic helpers for the local-only W7b3 artifact verification gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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


def _read_json_object(path: Path) -> dict[str, object]:
    raw = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(raw, dict):
        raise TypeError(f"JSON artifact must be an object: {path.name}")
    return cast(dict[str, object], raw)


def _load_report(output: Path) -> dict[str, object]:
    report_path = output / "verification-report.json"
    if not report_path.is_file():
        raise FileNotFoundError(f"missing supply-chain report: {report_path}")
    report = _read_json_object(report_path)
    if report.get("schema_version") != 1:
        raise RuntimeError("unsupported supply-chain report schema")
    return report


def _report_images(report: dict[str, object]) -> list[dict[str, object]]:
    raw_images = report.get("images")
    if not isinstance(raw_images, list):
        raise TypeError("supply-chain report images must be a list")
    images: list[dict[str, object]] = []
    for raw_image in cast(list[object], raw_images):
        if not isinstance(raw_image, dict):
            raise TypeError("supply-chain report image entry must be an object")
        images.append(cast(dict[str, object], raw_image))
    return images


def verify_immutable_evidence(output: Path) -> None:
    """Independently validate immutable image references and artifact hashes."""

    report = _load_report(output)
    if report.get("scope") != "Stage 1A Simulator-only non-production":
        raise RuntimeError("supply-chain scope mismatch")
    if report.get("production_authorized") is not False:
        raise RuntimeError("supply-chain evidence must not authorize production")
    revision = report.get("revision")
    if not isinstance(revision, str) or re.fullmatch(r"[a-f0-9]{40}", revision) is None:
        raise RuntimeError("supply-chain revision must be a full Git commit")

    expected_specs = {spec.name: spec for spec in IMAGES}
    observed_names: set[str] = set()
    expected_hashed_artifacts: set[str] = set()
    for image in _report_images(report):
        reference = image.get("reference")
        digest = image.get("digest")
        archive = image.get("archive")
        user = image.get("user")
        if not isinstance(reference, str):
            raise TypeError("image reference must be a string")
        digest_body = require_digest_reference(reference)
        name = reference.split("@", maxsplit=1)[0]
        if name not in expected_specs or name in observed_names:
            raise RuntimeError(f"unexpected or duplicate image evidence: {name}")
        observed_names.add(name)
        if digest != f"sha256:{digest_body}":
            raise RuntimeError(f"image digest mismatch: {name}")
        if archive != f"{name}.image.tar":
            raise RuntimeError(f"image archive name mismatch: {name}")
        if not isinstance(user, str) or user in {
            "",
            "0",
            "root",
            "0:0",
            "root:root",
        }:
            raise RuntimeError(f"image runtime user is not non-root: {name}")
        expected_hashed_artifacts.update(
            {
                f"{name}.image.tar",
                f"{name}.cdx.json",
                f"{name}.trivy.json",
                f"{name}.provenance.json",
            }
        )
    if observed_names != set(expected_specs):
        raise RuntimeError(
            "supply-chain evidence does not contain both expected images"
        )

    manifest_path = output / "artifact-hashes.json"
    manifest = _read_json_object(manifest_path)
    if set(manifest) != expected_hashed_artifacts:
        raise RuntimeError("artifact hash manifest inventory mismatch")
    verify_hash_manifest(manifest_path, output)


def verify_sbom_evidence(output: Path) -> None:
    """Independently validate both CycloneDX component inventories."""

    _load_report(output)
    for spec in IMAGES:
        sbom = _read_json_object(output / f"{spec.name}.cdx.json")
        if sbom.get("bomFormat") != "CycloneDX":
            raise RuntimeError(f"SBOM is not CycloneDX: {spec.name}")
        if not isinstance(sbom.get("specVersion"), str):
            raise TypeError(f"CycloneDX spec version is missing: {spec.name}")
        components = sbom.get("components")
        if not isinstance(components, list) or not components:
            raise RuntimeError(f"CycloneDX component inventory is empty: {spec.name}")


def verify_scan_evidence(output: Path) -> None:
    """Independently reject any fixed HIGH/CRITICAL result in Trivy JSON."""

    _load_report(output)
    blocked: list[str] = []
    for spec in IMAGES:
        scan = _read_json_object(output / f"{spec.name}.trivy.json")
        if not isinstance(scan.get("SchemaVersion"), int):
            raise TypeError(f"Trivy schema version is missing: {spec.name}")
        results = scan.get("Results")
        if not isinstance(results, list) or not results:
            raise RuntimeError(f"Trivy result inventory is empty: {spec.name}")
        for raw_result in cast(list[object], results):
            if not isinstance(raw_result, dict):
                raise TypeError(f"invalid Trivy result entry: {spec.name}")
            vulnerabilities = cast(dict[object, object], raw_result).get(
                "Vulnerabilities"
            )
            if vulnerabilities is None:
                continue
            if not isinstance(vulnerabilities, list):
                raise TypeError(f"invalid Trivy vulnerability inventory: {spec.name}")
            for raw_vulnerability in cast(list[object], vulnerabilities):
                if not isinstance(raw_vulnerability, dict):
                    raise TypeError(f"invalid Trivy vulnerability entry: {spec.name}")
                vulnerability = cast(dict[object, object], raw_vulnerability)
                severity = vulnerability.get("Severity")
                if severity in {"HIGH", "CRITICAL"}:
                    identifier = vulnerability.get("VulnerabilityID", "unknown")
                    blocked.append(f"{spec.name}:{identifier}:{severity}")
    if blocked:
        raise RuntimeError(
            "Trivy evidence contains HIGH/CRITICAL vulnerabilities: "
            + ", ".join(blocked)
        )


def verify_provenance_evidence(output: Path) -> None:
    """Independently bind SLSA v1 provenance to images, source, and bases."""

    report = _load_report(output)
    revision = report.get("revision")
    if not isinstance(revision, str):
        raise TypeError("supply-chain revision must be a string")
    images: dict[str, dict[str, object]] = {}
    for image in _report_images(report):
        reference = image.get("reference")
        if not isinstance(reference, str):
            raise TypeError("image reference must be a string")
        images[reference.split("@", maxsplit=1)[0]] = image

    for spec in IMAGES:
        statement = _read_json_object(output / f"{spec.name}.provenance.json")
        if statement.get("_type") != "https://in-toto.io/Statement/v1":
            raise RuntimeError(f"invalid in-toto statement: {spec.name}")
        if statement.get("predicateType") != "https://slsa.dev/provenance/v1":
            raise RuntimeError(f"invalid SLSA predicate: {spec.name}")
        image = images.get(spec.name)
        if image is None:
            raise RuntimeError(f"missing report image: {spec.name}")
        digest = image.get("digest")
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise RuntimeError(f"invalid report digest: {spec.name}")
        expected_subject = [
            {"name": spec.name, "digest": {"sha256": digest.removeprefix("sha256:")}}
        ]
        if statement.get("subject") != expected_subject:
            raise RuntimeError(f"provenance subject mismatch: {spec.name}")

        predicate = statement.get("predicate")
        if not isinstance(predicate, dict):
            raise TypeError(f"provenance predicate is missing: {spec.name}")
        build_definition = cast(dict[object, object], predicate).get("buildDefinition")
        if not isinstance(build_definition, dict):
            raise TypeError(f"provenance build definition is missing: {spec.name}")
        build_fields = cast(dict[object, object], build_definition)
        external_parameters = build_fields.get("externalParameters")
        if (
            not isinstance(external_parameters, dict)
            or cast(dict[object, object], external_parameters).get("dockerfile")
            != spec.dockerfile
        ):
            raise RuntimeError(f"provenance Dockerfile mismatch: {spec.name}")
        dependencies = build_fields.get("resolvedDependencies")
        if not isinstance(dependencies, list):
            raise TypeError(f"provenance dependencies are missing: {spec.name}")
        expected_dependencies = create_provenance(
            image_name=spec.name,
            image_digest=digest,
            revision=revision,
            dockerfile=spec.dockerfile,
            builder_id="validation-only",
            invocation_id="validation-only",
            base_references=spec.base_references,
        )["predicate"]
        expected_build = cast(dict[str, object], expected_dependencies)[
            "buildDefinition"
        ]
        expected_resolved = cast(dict[str, object], expected_build)[
            "resolvedDependencies"
        ]
        if dependencies != expected_resolved:
            raise RuntimeError(f"provenance dependency mismatch: {spec.name}")


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


def verify_signature_evidence(output: Path) -> None:
    """Independently verify all Cosign bundles and both negative controls."""

    report = _load_report(output)
    signer = report.get("signer")
    if not isinstance(signer, dict):
        raise TypeError("signer evidence is missing")
    signer_fields = cast(dict[object, object], signer)
    if signer_fields.get("type") != "ephemeral in-run Cosign test identity":
        raise RuntimeError("unexpected signing identity type")
    if signer_fields.get("private_key_retention") != "destroyed before gate completion":
        raise RuntimeError("private key destruction was not asserted")
    public_key_name = signer_fields.get("public_key")
    wrong_public_key_name = signer_fields.get("wrong_public_key")
    if (
        not isinstance(public_key_name, str)
        or public_key_name != "ephemeral-test-signer.pub"
    ):
        raise RuntimeError("unexpected signer public key")
    if (
        not isinstance(wrong_public_key_name, str)
        or wrong_public_key_name != "ephemeral-wrong-signer.pub"
    ):
        raise RuntimeError("unexpected negative-control public key")
    public_key = output / public_key_name
    wrong_public_key = output / wrong_public_key_name
    if not public_key.is_file() or not wrong_public_key.is_file():
        raise FileNotFoundError("signing public-key evidence is missing")
    if any(output.glob("*.key")):
        raise RuntimeError("private signing key is present in evidence")

    verification = report.get("verification")
    if not isinstance(verification, dict):
        raise TypeError("signature verification evidence is missing")
    verification_fields = cast(dict[object, object], verification)
    for negative_control in (
        "tampered_artifact_rejected",
        "wrong_signer_rejected",
        "mutable_reference_rejected",
    ):
        if verification_fields.get(negative_control) is not True:
            raise RuntimeError(f"negative control did not pass: {negative_control}")
    raw_bundles = verification_fields.get("bundles")
    if not isinstance(raw_bundles, dict):
        raise TypeError("signature bundle inventory is missing")
    bundles = cast(dict[object, object], raw_bundles)
    expected_artifacts = {
        f"{spec.name}.{suffix}"
        for spec in IMAGES
        for suffix in (
            "image.tar",
            "cdx.json",
            "trivy.json",
            "provenance.json",
        )
    } | {"artifact-hashes.json"}
    if set(bundles) != expected_artifacts:
        raise RuntimeError("signature bundle inventory mismatch")

    cosign = _tool("cosign", "LEMOO_COSIGN_PATH", "cosign-windows-amd64.exe")
    environment = _cosign_environment()

    def verify_bundle(artifact: Path, bundle: Path, key: Path) -> None:
        if not artifact.is_file() or not bundle.is_file():
            raise FileNotFoundError(
                f"signed artifact or bundle is missing: {artifact.name}"
            )
        _run(
            [
                cosign,
                "verify-blob",
                "--insecure-ignore-tlog",
                "--key",
                str(key),
                "--bundle",
                str(bundle),
                str(artifact),
            ],
            environment=environment,
        )

    for raw_artifact_name, raw_bundle_name in bundles.items():
        if not isinstance(raw_artifact_name, str) or not isinstance(
            raw_bundle_name, str
        ):
            raise TypeError("signature bundle entries must be strings")
        verify_bundle(
            output / raw_artifact_name,
            output / raw_bundle_name,
            public_key,
        )
    verify_bundle(
        output / "verification-report.json",
        output / "verification-report.json.sigstore.json",
        public_key,
    )

    first_artifact_name = min(expected_artifacts)
    first_artifact = output / first_artifact_name
    first_bundle_name = bundles[first_artifact_name]
    if not isinstance(first_bundle_name, str):
        raise TypeError("negative-control signature bundle name must be a string")
    first_bundle = output / first_bundle_name
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output,
            prefix=".negative-tampered-",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        shutil.copyfile(first_artifact, temporary_path)
        with temporary_path.open("ab") as stream:
            stream.write(b"tampered")
        _expect_failure(
            [
                cosign,
                "verify-blob",
                "--insecure-ignore-tlog",
                "--key",
                str(public_key),
                "--bundle",
                str(first_bundle),
                str(temporary_path),
            ],
            environment=environment,
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    _expect_failure(
        [
            cosign,
            "verify-blob",
            "--insecure-ignore-tlog",
            "--key",
            str(wrong_public_key),
            "--bundle",
            str(first_bundle),
            str(first_artifact),
        ],
        environment=environment,
    )


def verify_evidence(control: str, output: Path = DEFAULT_OUTPUT) -> None:
    """Run one stable, independent supply-chain CI control."""

    controls = {
        "immutable": verify_immutable_evidence,
        "sbom": verify_sbom_evidence,
        "scan": verify_scan_evidence,
        "provenance": verify_provenance_evidence,
        "signature": verify_signature_evidence,
    }
    validator = controls.get(control)
    if validator is None:
        raise ValueError(f"unknown supply-chain control: {control}")
    validator(output.resolve())
    print(f"supply_chain_control={control} result=pass")


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
    if len(sys.argv) == 1:
        verify_supply_chain()
        return
    parser = argparse.ArgumentParser(
        description="Generate or independently validate Stage 1A supply-chain evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    check = subparsers.add_parser("check")
    check.add_argument(
        "control",
        choices=("immutable", "sbom", "scan", "provenance", "signature"),
    )
    check.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    if arguments.command == "generate":
        verify_supply_chain(cast(Path, arguments.output))
        return
    verify_evidence(cast(str, arguments.control), cast(Path, arguments.output))


__all__ = [
    "IMAGES",
    "create_provenance",
    "require_digest_reference",
    "sha256_file",
    "verify_evidence",
    "verify_hash_manifest",
    "verify_immutable_evidence",
    "verify_provenance_evidence",
    "verify_sbom_evidence",
    "verify_scan_evidence",
    "verify_signature_evidence",
    "verify_supply_chain",
]


if __name__ == "__main__":
    main()
