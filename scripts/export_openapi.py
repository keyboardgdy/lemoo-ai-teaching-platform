"""Export or verify the deterministic Stage 1A Web OpenAPI 3.1 document."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.config import Settings
from app.entrypoints.api import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPOSITORY_ROOT / "packages" / "openapi" / "openapi.json"


def rendered_openapi() -> str:
    application = create_app(Settings(environment="ci"))
    payload = application.openapi()
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    rendered = rendered_openapi()
    if "--check" in sys.argv:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("openapi_check=fail generated contract drift")
        print(f"openapi_check=pass path={OUTPUT.relative_to(REPOSITORY_ROOT)}")
        return
    OUTPUT.write_text(
        rendered,
        encoding="utf-8",
        newline="\n",
    )
    print(f"openapi_export=pass path={OUTPUT.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
