"""Deterministic W7b3 supply-chain policy tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from scripts.supply_chain import (
    create_provenance,
    require_digest_reference,
    sha256_file,
    verify_hash_manifest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILES = (
    REPOSITORY_ROOT / "docker" / "api.Dockerfile",
    REPOSITORY_ROOT / "docker" / "web.Dockerfile",
)


@pytest.mark.parametrize(
    "reference",
    [
        "lemoo-api:latest",
        "lemoo-api:ci",
        "lemoo-api",
        "lemoo-api@sha256:not-a-digest",
    ],
)
def test_mutable_or_malformed_image_references_are_rejected(reference: str) -> None:
    with pytest.raises(ValueError, match="immutable image reference required"):
        require_digest_reference(reference)


def test_digest_image_reference_is_accepted() -> None:
    digest = "a" * 64
    assert require_digest_reference(f"lemoo-api@sha256:{digest}") == digest


def test_provenance_binds_commit_builder_and_immutable_subject() -> None:
    digest = "b" * 64
    statement = create_provenance(
        image_name="lemoo-api",
        image_digest=f"sha256:{digest}",
        revision="c" * 40,
        dockerfile="docker/api.Dockerfile",
        builder_id="https://github.com/keyboardgdy/lemoo/actions/runs/1",
        invocation_id="1",
    )

    assert statement["_type"] == "https://in-toto.io/Statement/v1"
    assert statement["predicateType"] == "https://slsa.dev/provenance/v1"
    assert statement["subject"] == [{"name": "lemoo-api", "digest": {"sha256": digest}}]
    predicate = cast(dict[str, object], statement["predicate"])
    run_details = cast(dict[str, object], predicate["runDetails"])
    builder = cast(dict[str, str], run_details["builder"])
    assert builder["id"].startswith("https://github.com/")
    build_definition = cast(dict[str, object], predicate["buildDefinition"])
    dependencies = cast(list[dict[str, object]], build_definition["resolvedDependencies"])
    assert dependencies[0]["digest"] == {"gitCommit": "c" * 40}


def test_hash_manifest_detects_artifact_tampering(tmp_path: Path) -> None:
    artifact = tmp_path / "image.tar"
    artifact.write_bytes(b"trusted-image")
    manifest = tmp_path / "hashes.json"
    manifest.write_text(
        json.dumps({"image.tar": sha256_file(artifact)}),
        encoding="utf-8",
    )
    verify_hash_manifest(manifest, tmp_path)

    artifact.write_bytes(b"tampered-image")
    with pytest.raises(ValueError, match="artifact digest mismatch"):
        verify_hash_manifest(manifest, tmp_path)


def test_all_container_stages_pin_base_digests_and_runtime_is_non_root() -> None:
    for dockerfile in DOCKERFILES:
        source = dockerfile.read_text(encoding="utf-8")
        from_lines = [line for line in source.splitlines() if line.startswith("FROM ")]
        assert from_lines, dockerfile
        assert all("@sha256:" in line for line in from_lines), dockerfile
        assert "USER root" not in source, dockerfile
        assert "USER " in source, dockerfile
