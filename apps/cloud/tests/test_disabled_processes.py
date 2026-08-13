"""Ensure non-API process composition roots cannot be implied by W2."""

import pytest

from app.entrypoints.disabled import DISABLED_PROCESSES, disabled_process


def test_every_future_process_has_an_explicit_gate() -> None:
    assert len(DISABLED_PROCESSES) == 7
    assert all(process.required_gate for process in DISABLED_PROCESSES)
    assert all("disabled until" in process.reason for process in DISABLED_PROCESSES)


def test_unknown_process_is_rejected() -> None:
    with pytest.raises(KeyError, match="Unknown process"):
        disabled_process("unregistered")
