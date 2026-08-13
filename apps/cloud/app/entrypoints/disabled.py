"""Fail-closed helpers for process entrypoints not approved in W2."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DisabledProcess:
    name: str
    required_gate: str

    @property
    def reason(self) -> str:
        return f"{self.name} is disabled until {self.required_gate} passes"


DISABLED_PROCESSES: tuple[DisabledProcess, ...] = (
    DisabledProcess("device-gateway", "G2-Device"),
    DisabledProcess("interaction-gateway", "G2-AI"),
    DisabledProcess("outbox-dispatcher", "W6a"),
    DisabledProcess("worker-content", "G2-Content"),
    DisabledProcess("worker-operations", "G2-Device"),
    DisabledProcess("worker-analytics", "W6a"),
    DisabledProcess("scheduler", "W6a"),
)


def disabled_process(name: str) -> DisabledProcess:
    """Return a registered disabled process or reject the unknown name."""

    for process in DISABLED_PROCESSES:
        if process.name == name:
            return process
    msg = f"Unknown process: {name}"
    raise KeyError(msg)
