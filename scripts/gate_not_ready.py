"""Fail closed for named tasks whose prerequisite gate has not passed."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: gate_not_ready.py <required-gate> <capability>")
    gate, capability = sys.argv[1:]
    raise SystemExit(f"BLOCKED: {capability} is unavailable until {gate} passes")


if __name__ == "__main__":
    main()
