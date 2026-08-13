"""Export the deterministic W2 health-only OpenAPI 3.1 document."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.entrypoints.api import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPOSITORY_ROOT / "packages" / "openapi" / "openapi.json"


def main() -> None:
    application = create_app(Settings(environment="ci"))
    payload = application.openapi()
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"openapi_export=pass path={OUTPUT.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
