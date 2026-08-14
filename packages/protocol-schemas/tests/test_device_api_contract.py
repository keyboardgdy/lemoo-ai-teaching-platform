"""Executable contract tests for the Stage 1A Device HTTPS boundary."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
DEVICE_API = ROOT / "device-api"
OPENAPI = DEVICE_API / "openapi.v1.json"
POLICY = DEVICE_API / "identity-policy.v1.json"
CATALOG = DEVICE_API / "capability-catalog.v1.json"
REQUIRED_PATHS = {
    "/provision/enrollments",
    "/devices/{device_id}/bindings:consume",
    "/devices/{device_id}/certificates:rotate",
    "/devices/{device_id}/certificate-status",
    "/devices/{device_id}/time",
    "/devices/{device_id}/transfers:upload-url",
    "/devices/{device_id}/transfers:download-url",
}


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def auth_fixtures() -> Iterator[tuple[Path, dict[str, Any]]]:
    for path in sorted((DEVICE_API / "fixtures" / "auth").glob("*.json")):
        yield path, load_json(path)


def authorize(policy: dict[str, Any], case: dict[str, Any]) -> tuple[bool, str]:
    certificate = cast(dict[str, Any], case["certificate"])
    now = datetime.fromisoformat(cast(str, case["server_time"]).replace("Z", "+00:00"))
    not_before = datetime.fromisoformat(
        cast(str, certificate["not_before"]).replace("Z", "+00:00")
    )
    not_after = datetime.fromisoformat(
        cast(str, certificate["not_after"]).replace("Z", "+00:00")
    )

    if case["presented_scheme"] != "DeviceMtls":
        return False, "wrong_security_scheme"
    if certificate["issuer"] != policy["trusted_test_issuer"]:
        return False, "untrusted_issuer"
    if not_before > now or not_after <= now:
        return False, "certificate_not_current"
    if certificate["status"] != "active":
        return False, f"certificate_{certificate['status']}"
    if certificate["device_id"] != case["path_device_id"]:
        return False, "path_identity_mismatch"
    if certificate["san_uri"] != policy["san_uri_template"].replace(
        "{device_id}", cast(str, certificate["device_id"])
    ):
        return False, "san_identity_mismatch"
    return True, "authorized"


def test_w5b_has_authoritative_openapi_policy_catalog_and_fixtures() -> None:
    assert DEVICE_API.is_dir()
    assert OPENAPI.is_file()
    assert POLICY.is_file()
    assert CATALOG.is_file()
    assert len(list(auth_fixtures())) >= 6


def test_device_openapi_is_v31_simulator_first_and_https_only() -> None:
    document = load_json(OPENAPI)
    assert document["openapi"] == "3.1.0"
    assert document["info"]["version"] == "1.0.0"
    assert document["x-lemoo"] == {
        "status": "frozen",
        "scope": "stage-1a-simulator-first",
        "production_supported": False,
    }
    assert all(server["url"].startswith("https://") for server in document["servers"])
    assert set(document["paths"]) == REQUIRED_PATHS


def test_web_and_device_credentials_are_not_interchangeable() -> None:
    document = load_json(OPENAPI)
    schemes = document["components"]["securitySchemes"]
    assert schemes == {
        "DeviceMtls": {
            "type": "mutualTLS",
            "description": "Per-device X.509 certificate; identity comes from verified SAN URI.",
        },
        "ProvisioningMtls": {
            "type": "mutualTLS",
            "description": "Simulator bootstrap certificate; never accepted as a Web session.",
        },
    }
    assert document["security"] == [{"DeviceMtls": []}]
    serialized = json.dumps(document)
    assert "apiKey" not in serialized
    assert "bearer" not in serialized.lower()
    assert "cookie" not in serialized.lower()


def test_only_provisioning_uses_the_bootstrap_trust_domain() -> None:
    document = load_json(OPENAPI)
    paths = document["paths"]
    assert paths["/provision/enrollments"]["post"]["security"] == [
        {"ProvisioningMtls": []}
    ]
    for path, operations in paths.items():
        if path == "/provision/enrollments":
            continue
        for operation in operations.values():
            assert operation.get("security", document["security"]) == [
                {"DeviceMtls": []}
            ]


def test_binding_rotation_and_revocation_rules_fail_closed() -> None:
    policy = load_json(POLICY)
    assert policy["binding"] == {
        "code_ttl_seconds": 300,
        "one_time": True,
        "max_attempts": 5,
        "binds": ["serial_number", "organization_id", "site_id"],
        "audit_required": True,
    }
    assert policy["rotation"]["requires_current_certificate"] is True
    assert policy["rotation"]["csr_san_must_match_current_device"] is True
    assert policy["rotation"]["overlap_seconds"] == 300
    assert policy["revocation"]["deny_statuses"] == ["revoked", "suspended"]
    assert policy["revocation"]["unknown_status_behavior"] == "deny_and_audit"


def test_wrong_ca_expiry_revocation_path_and_web_session_are_rejected() -> None:
    policy = load_json(POLICY)
    cases = list(auth_fixtures())
    assert len(cases) >= 6
    for path, case in cases:
        allowed, reason = authorize(policy, case)
        assert allowed is case["allowed"], path.name
        assert reason == case["reason"], path.name


def test_transfer_contract_is_present_but_disabled_for_stage_1a() -> None:
    catalog = load_json(CATALOG)
    assert catalog["stage_1a_enabled"] == {
        "provision": True,
        "binding": True,
        "certificate_rotation": True,
        "certificate_status": True,
        "server_time": True,
        "upload_url": False,
        "download_url": False,
    }
    assert catalog["disabled_transfer_purposes"] == [
        "content",
        "diagnostics",
        "firmware",
        "student_audio",
    ]
    assert catalog["disabled_response"] == {
        "status": 403,
        "code": "capability_not_enabled",
    }


def test_auth_fixture_times_are_explicit_utc() -> None:
    for path, case in auth_fixtures():
        parsed = datetime.fromisoformat(
            cast(str, case["server_time"]).replace("Z", "+00:00")
        )
        assert parsed.tzinfo == UTC, path.name
