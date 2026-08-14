"""Cross-platform pytest runtime configuration."""

from __future__ import annotations

import asyncio
import selectors
import sys
from collections.abc import Callable, Mapping


def _selector_loop() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


def pytest_asyncio_loop_factories(
    config: object, item: object
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]]:
    """Use psycopg-compatible Selector loops on Windows without policy APIs."""

    del config, item
    if sys.platform == "win32":
        return {"selector": _selector_loop}
    return {"default": asyncio.new_event_loop}
