"""Ensure deferred cross-boundary schemas are explicit and fail closed."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "packages/openapi/_STATUS.md": "Status: `skeleton`",
    "packages/protocol-schemas/_STATUS.md": "Status: `partial_stage_1a`",
    "packages/content-package-schema/_STATUS.md": "Status: `disabled`",
}


def main() -> None:
    errors: list[str] = []
    for relative, marker in EXPECTED.items():
        path = REPOSITORY_ROOT / relative
        if not path.is_file() or marker not in path.read_text(encoding="utf-8"):
            errors.append(f"schema status mismatch: {relative} must contain {marker}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"schemas_check=pass boundaries={len(EXPECTED)}")


if __name__ == "__main__":
    main()
