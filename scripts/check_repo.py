"""Check W2 repository invariants and forbidden tracked material."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    ".python-version",
    ".node-version",
    ".env.example",
    "package.json",
    "pnpm-workspace.yaml",
    "pnpm-lock.yaml",
    "Taskfile.yml",
    "apps/cloud/pyproject.toml",
    "apps/cloud/uv.lock",
    "apps/web/package.json",
    "compose.yaml",
    ".github/CODEOWNERS",
    ".github/workflows/ci.yml",
)
FORBIDDEN_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    errors = [name for name in REQUIRED_FILES if not (REPOSITORY_ROOT / name).is_file()]
    for name in tracked_files():
        normalized = name.replace("\\", "/")
        if normalized == ".env" or normalized.startswith("docs/.obsidian/"):
            errors.append(f"forbidden tracked local file: {normalized}")
        if normalized.lower().endswith(FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden tracked key material: {normalized}")

    python_version = (
        (REPOSITORY_ROOT / ".python-version").read_text(encoding="utf-8").strip()
    )
    node_version = (
        (REPOSITORY_ROOT / ".node-version").read_text(encoding="utf-8").strip()
    )
    if python_version != "3.14":
        errors.append(f"unexpected .python-version: {python_version}")
    if not node_version.startswith("24."):
        errors.append(f"unexpected .node-version: {node_version}")

    lockfiles = sorted(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in REPOSITORY_ROOT.rglob("*lock*")
        if ".git" not in path.parts
        and "node_modules" not in path.parts
        and ".venv" not in path.parts
    )
    expected_locks = ["apps/cloud/uv.lock", "pnpm-lock.yaml"]
    if lockfiles != expected_locks:
        errors.append(
            f"lockfile invariant failed: expected {expected_locks}, got {lockfiles}"
        )

    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"repo_check=pass required_files={len(REQUIRED_FILES)} tracked_files={len(tracked_files())}"
    )


if __name__ == "__main__":
    main()
