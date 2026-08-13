"""Cross-platform W2 bootstrap checks and safe local environment creation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def command_version(command: str) -> str:
    """Return the first version line for a required command."""

    executable = shutil.which(command)
    if executable is None:
        msg = f"Required command is unavailable: {command}"
        raise RuntimeError(msg)
    result = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return result.stdout.strip().splitlines()[0]


def require_version(label: str, actual: str, expected_token: str) -> None:
    """Reject a runtime outside the pinned major line."""

    if expected_token not in actual:
        msg = f"{label} version mismatch: expected {expected_token!r} in {actual!r}"
        raise RuntimeError(msg)


def main() -> None:
    if sys.version_info[:2] != (3, 14):
        msg = f"Python 3.14 is required, got {sys.version.split()[0]}"
        raise RuntimeError(msg)

    node_version = command_version("node")
    pnpm_version = command_version("pnpm")
    require_version("Node", node_version, "v24.")
    require_version("pnpm", pnpm_version, "11.")

    env_example = REPOSITORY_ROOT / ".env.example"
    env_local = REPOSITORY_ROOT / ".env"
    if not env_local.exists():
        shutil.copyfile(env_example, env_local)
        env_action = "created from .env.example"
    else:
        env_action = "preserved existing untracked file"

    print(f"Python={sys.version.split()[0]}")
    print(f"Node={node_version}")
    print(f"pnpm={pnpm_version}")
    print(f".env={env_action}")


if __name__ == "__main__":
    main()
