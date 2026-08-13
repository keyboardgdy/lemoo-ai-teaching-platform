"""Validate local Markdown links, UTF-8 text and balanced code fences."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
EXCLUDED_PARTS = {".git", ".obsidian", "node_modules", ".venv"}


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in REPOSITORY_ROOT.rglob("*.md")
        if not EXCLUDED_PARTS.intersection(path.parts)
    )


def main() -> None:
    errors: list[str] = []
    files = markdown_files()
    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        if "\ufffd" in text:
            errors.append(f"replacement character: {path}")
        if len(re.findall(r"(?m)^```", text)) % 2:
            errors.append(f"unbalanced code fences: {path}")
        for match in LINK_PATTERN.finditer(text):
            link = unquote(match.group(1))
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative_path = link.split("#", maxsplit=1)[0]
            if not relative_path:
                continue
            target = (path.parent / relative_path).resolve()
            if not target.exists():
                errors.append(
                    f"broken link: {path.relative_to(REPOSITORY_ROOT)} -> {link}"
                )

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"docs_check=pass files={len(files)}")


if __name__ == "__main__":
    main()
