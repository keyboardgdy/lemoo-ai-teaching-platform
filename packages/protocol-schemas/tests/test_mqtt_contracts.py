"""Executable contract tests for the Stage 1A MQTT boundary."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
MQTT = ROOT / "mqtt"
SCHEMAS = {
    "reported-shadow": "reported-shadow.v1.schema.json",
    "telemetry": "telemetry.v1.schema.json",
    "device-event": "device-event.v1.schema.json",
    "command": "command.v1.schema.json",
    "command-ack": "command-ack.v1.schema.json",
}
REQUIRED_ARTIFACTS = {
    "README.md",
    "envelope.v1.schema.json",
    "topic-policy.v1.json",
    "acl.v1.json",
    "compatibility.v1.json",
    *SCHEMAS.values(),
}


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def schema_registry() -> Registry[Any]:
    resources: list[tuple[str, Resource[Any]]] = []
    for path in MQTT.glob("*.schema.json"):
        document = load_json(path)
        resources.append((cast(str, document["$id"]), Resource.from_contents(document)))
    return Registry().with_resources(resources)


def contract_fixtures(kind: str) -> Iterator[tuple[Path, dict[str, Any]]]:
    for path in sorted((MQTT / "fixtures" / kind).glob("*.json")):
        yield path, load_json(path)


def topic_matches(pattern: str, topic: str, device_id: str) -> bool:
    pattern_segments = pattern.replace("{device_id}", device_id).split("/")
    topic_segments = topic.split("/")
    if len(pattern_segments) != len(topic_segments):
        return False
    return all(
        expected == actual or (expected == "{command_id}" and bool(actual))
        for expected, actual in zip(pattern_segments, topic_segments, strict=True)
    )


def acl_allows(policy: dict[str, Any], identity: str, action: str, topic: str) -> bool:
    if "+" in topic or "#" in topic:
        return False
    if not topic.startswith(f"v1/devices/{identity}/"):
        return False
    patterns = cast(dict[str, list[str]], policy["device"])[action]
    return any(topic_matches(pattern, topic, identity) for pattern in patterns)


def test_w5a_contract_has_every_authoritative_artifact() -> None:
    assert MQTT.is_dir(), "W5a MQTT contract directory must exist"
    assert REQUIRED_ARTIFACTS <= {path.name for path in MQTT.iterdir()}


def test_every_schema_is_valid_draft_2020_12_and_simulator_first() -> None:
    schema_paths = sorted(MQTT.glob("*.schema.json"))
    assert len(schema_paths) == 6
    for path in schema_paths:
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        metadata = cast(dict[str, Any], schema["x-lemoo"])
        assert metadata == {
            "status": "frozen",
            "scope": "stage-1a-simulator-first",
            "production_supported": False,
        }


def test_accepted_messages_validate_against_their_named_contract() -> None:
    registry = schema_registry()
    fixtures = list(contract_fixtures("accepted"))
    assert len(fixtures) >= 5
    for path, fixture in fixtures:
        contract = cast(str, fixture["contract"])
        schema = load_json(MQTT / SCHEMAS[contract])
        errors = list(
            Draft202012Validator(schema, registry=registry).iter_errors(
                fixture["message"]
            )
        )
        assert not errors, f"{path.name}: {[error.message for error in errors]}"


def test_rejected_messages_fail_for_the_documented_reason() -> None:
    registry = schema_registry()
    fixtures = list(contract_fixtures("rejected"))
    assert len(fixtures) >= 7
    for path, fixture in fixtures:
        contract = cast(str, fixture["contract"])
        schema = load_json(MQTT / SCHEMAS[contract])
        errors = list(
            Draft202012Validator(schema, registry=registry).iter_errors(
                fixture["message"]
            )
        )
        assert errors, f"{path.name} unexpectedly passed"
        expected_fragment = cast(str, fixture["expected_error_contains"])
        assert any(expected_fragment in error.message for error in errors), (
            f"{path.name}: expected {expected_fragment!r}, got "
            f"{[error.message for error in errors]}"
        )


def test_acl_matrix_rejects_cross_device_and_wildcard_access() -> None:
    policy = load_json(MQTT / "acl.v1.json")
    cases = list(contract_fixtures("acl"))
    assert len(cases) >= 8
    for path, case in cases:
        actual = acl_allows(
            policy,
            cast(str, case["identity"]),
            cast(str, case["action"]),
            cast(str, case["topic"]),
        )
        assert actual is case["allowed"], path.name


def test_topic_policy_freezes_qos_retain_session_and_size() -> None:
    policy = load_json(MQTT / "topic-policy.v1.json")
    assert policy["protocol"] == "MQTT-5.0"
    assert policy["transport"] == "tcp-tls-mtls"
    assert policy["session"]["clean_start"] is False
    assert policy["session"]["expiry_seconds"] == 86400
    assert policy["limits"] == {
        "max_packet_bytes": 65536,
        "max_inflight_qos1": 32,
        "max_topic_depth": 7,
    }
    assert policy["topics"]["reported_shadow"] == {"qos": 1, "retain": True}
    assert policy["topics"]["telemetry"] == {"qos": 0, "retain": False}
    assert policy["topics"]["command"] == {"qos": 1, "retain": False}
    assert policy["topics"]["command_ack"] == {"qos": 1, "retain": False}


def test_duplicate_order_expiry_and_limit_outcomes_are_frozen() -> None:
    compatibility = load_json(MQTT / "compatibility.v1.json")
    limits = load_json(MQTT / "topic-policy.v1.json")["limits"]

    assert compatibility["duplicate_behavior"] == (
        "ack_without_reapplying_business_effect"
    )
    assert compatibility["out_of_order_behavior"] == (
        "persist_observation_without_regressing_current_state"
    )
    assert compatibility["new_boot_behavior"] == (
        "accept_sequence_reset_and_order_within_new_boot"
    )
    assert compatibility["expired_command_behavior"] == "reject_and_ack_expired"
    assert compatibility["oversize_packet_behavior"] == (
        "reject_before_schema_validation_and_audit"
    )
    assert limits["max_packet_bytes"] == 65536


@pytest.mark.parametrize("major", [0, 2, 99])
def test_unknown_topic_major_is_rejected(major: int) -> None:
    policy = load_json(MQTT / "compatibility.v1.json")
    assert major not in policy["accepted_topic_majors"]
    assert policy["unknown_major_behavior"] == "reject_and_audit"
