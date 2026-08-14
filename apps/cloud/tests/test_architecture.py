"""Executable dependency rules for the modular domain core."""

from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_ROOT = Path(__file__).resolve().parents[1] / "app" / "modules"
FORBIDDEN_DOMAIN_IMPORTS = frozenset(
    {"fastapi", "sqlalchemy", "redis", "paho", "boto3", "dramatiq"}
)


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


def test_domain_modules_do_not_depend_on_framework_or_infrastructure_sdks() -> None:
    domains = sorted(DOMAIN_ROOT.glob("*/domain.py"))
    assert len(domains) >= 3
    for domain in domains:
        assert imported_roots(domain).isdisjoint(FORBIDDEN_DOMAIN_IMPORTS), domain


def test_cross_module_domain_dependency_uses_public_api_only() -> None:
    operations = DOMAIN_ROOT / "device_operations" / "domain.py"
    imported_modules = {
        node.module
        for node in ast.walk(
            ast.parse(operations.read_text(encoding="utf-8"), filename=str(operations))
        )
        if isinstance(node, ast.ImportFrom) and node.module
    }
    cross_module_imports = {
        module
        for module in imported_modules
        if module.startswith("app.modules.")
        and not module.startswith("app.modules.device_operations")
    }
    assert cross_module_imports == {"app.modules.device_fleet.public"}
