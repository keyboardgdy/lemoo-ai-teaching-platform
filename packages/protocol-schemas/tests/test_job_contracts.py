"""Executable contracts for Stage 1A jobs, outbox, and command states."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "jobs"
SCHEMAS = {
    "job-envelope": "job-envelope.v1.schema.json",
    "job-progress": "job-progress.v1.schema.json",
    "job-result": "job-result.v1.schema.json",
    "job-error": "job-error.v1.schema.json",
    "outbox-event": "outbox-event.v1.schema.json",
}
REQUIRED_ARTIFACTS = {
    "README.md",
    "job-catalog.v1.json",
    "execution-policy.v1.json",
    "command-state-machine.v1.json",
    *SCHEMAS.values(),
}


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def fixtures(kind: str) -> Iterator[tuple[Path, dict[str, Any]]]:
    for path in sorted((JOBS / "fixtures" / kind).glob("*.json")):
        yield path, load_json(path)


def schema_registry() -> Registry[Any]:
    resources: list[tuple[str, Resource[Any]]] = []
    for path in JOBS.glob("*.schema.json"):
        document = load_json(path)
        resources.append((cast(str, document["$id"]), Resource.from_contents(document)))
    return Registry().with_resources(resources)


def validate_fixture(fixture: dict[str, Any]) -> list[Any]:
    schema = load_json(JOBS / SCHEMAS[cast(str, fixture["contract"])])
    return list(
        Draft202012Validator(schema, registry=schema_registry()).iter_errors(
            fixture["message"]
        )
    )


def test_w5c_has_every_authoritative_artifact() -> None:
    assert JOBS.is_dir()
    assert REQUIRED_ARTIFACTS <= {path.name for path in JOBS.iterdir()}


def test_every_job_schema_is_valid_frozen_and_simulator_first() -> None:
    paths = sorted(JOBS.glob("*.schema.json"))
    assert len(paths) == 5
    for path in paths:
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        assert schema["x-lemoo"] == {
            "status": "frozen",
            "scope": "stage-1a-simulator-first",
            "production_supported": False,
        }


def test_accepted_and_backward_fixtures_remain_valid() -> None:
    accepted = [*fixtures("accepted"), *fixtures("backward")]
    assert len(accepted) >= 7
    for path, fixture in accepted:
        errors = validate_fixture(fixture)
        assert not errors, f"{path.name}: {[error.message for error in errors]}"


def test_rejected_fixtures_fail_for_the_documented_reason() -> None:
    rejected = list(fixtures("rejected"))
    assert len(rejected) >= 5
    for path, fixture in rejected:
        errors = validate_fixture(fixture)
        assert errors, f"{path.name} unexpectedly passed"
        fragment = cast(str, fixture["expected_error_contains"])
        assert any(fragment in error.message for error in errors), (
            f"{path.name}: expected {fragment!r}, got "
            f"{[error.message for error in errors]}"
        )


def test_catalog_contains_only_stage_1a_core_jobs() -> None:
    catalog = load_json(JOBS / "job-catalog.v1.json")
    jobs = cast(dict[str, Any], catalog["jobs"])
    assert set(jobs) == {
        "device.command.dispatch",
        "device.command.expire",
        "device.presence.reconcile",
    }
    assert catalog["unknown_job_type_behavior"] == "dead_letter_without_execution"
    assert catalog["disabled_prefixes"] == [
        "ai.",
        "content.",
        "diagnostics.",
        "ota.",
        "teaching.",
    ]
    for definition in jobs.values():
        assert definition["max_attempts"] <= 5
        assert definition["timeout_seconds"] <= 30
        assert definition["payload_max_bytes"] <= 4096


def test_execution_policy_freezes_retry_cancel_timeout_and_recovery() -> None:
    policy = load_json(JOBS / "execution-policy.v1.json")
    assert policy["delivery"] == "at_least_once_business_idempotent"
    assert policy["duplicate_job_id_behavior"] == "return_existing_progress_or_result"
    assert policy["expired_deadline_behavior"] == "mark_timed_out_without_execution"
    assert policy["cancel_queued_behavior"] == "mark_cancelled_without_execution"
    assert (
        policy["cancel_running_behavior"] == "request_cooperative_cancel_then_timeout"
    )
    assert policy["progress_regression_behavior"] == "ignore_and_audit"
    assert policy["terminal_result_behavior"] == "immutable"
    assert policy["retry"] == {
        "strategy": "bounded_exponential_full_jitter",
        "base_seconds": 1,
        "max_seconds": 60,
        "dead_letter_after_catalog_max_attempts": True,
    }
    assert policy["outbox"] == {
        "claim": "for_update_skip_locked",
        "lease_seconds": 30,
        "batch_size": 100,
        "max_attempts": 10,
        "duplicate_delivery_behavior": "consumer_deduplicates_by_event_or_business_id",
    }


def test_error_categories_have_deterministic_retryability() -> None:
    policy = load_json(JOBS / "execution-policy.v1.json")
    assert policy["error_retryability"] == {
        "authorization": False,
        "cancelled": False,
        "conflict": False,
        "dependency_permanent": False,
        "dependency_transient": True,
        "timeout": True,
        "unknown_job_type": False,
        "validation": False,
    }


def test_command_state_machine_rejects_illegal_and_terminal_regression() -> None:
    machine = load_json(JOBS / "command-state-machine.v1.json")
    transitions = {
        source: set(targets) for source, targets in machine["transitions"].items()
    }
    assert transitions == {
        "created": {"approved", "cancelled", "expired"},
        "approved": {"published", "cancelled", "expired"},
        "published": {"accepted", "expired", "timed_out"},
        "accepted": {"running", "failed", "timed_out"},
        "running": {"succeeded", "failed", "timed_out"},
        "succeeded": set(),
        "failed": set(),
        "timed_out": set(),
        "expired": set(),
        "cancelled": set(),
    }
    assert machine["same_state_behavior"] == "idempotent_noop"
    assert machine["illegal_transition_behavior"] == "reject_and_audit"
    assert machine["late_ack_after_terminal_behavior"] == (
        "record_observation_without_state_regression"
    )
    assert machine["expiry_clock"] == "server_received_at"
    assert machine["device_revalidation_required"] is True
    assert machine["idempotency_key_scope"] == [
        "organization_id",
        "device_id",
        "command_type",
    ]
    assert machine["duplicate_request_behavior"] == "return_existing_command"
    assert machine["idempotency_conflict_behavior"] == "reject_and_audit"
    assert machine["expired_create_behavior"] == "reject_without_outbox_effect"
