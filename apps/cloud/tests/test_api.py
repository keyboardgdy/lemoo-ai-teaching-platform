"""Contract tests for the non-sensitive health surface."""

from collections.abc import Coroutine
from typing import cast

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.config import Settings
from app.entrypoints import api
from app.entrypoints.api import create_app


@pytest.mark.asyncio
async def test_health_endpoints_expose_only_non_sensitive_skeleton_metadata() -> None:
    settings = Settings(environment="test", service_name="lemoo-api-test")
    transport = ASGITransport(app=create_app(settings))

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        live: Response = await client.get("/health/live")
        ready: Response = await client.get("/health/ready")

    assert live.status_code == 200
    assert ready.status_code == 200
    live_payload = cast(dict[str, str], live.json())
    ready_payload = cast(dict[str, str], ready.json())
    assert live_payload == {
        "status": "alive",
        "service": "lemoo-api-test",
        "version": "0.1.0",
        "environment": "test",
        "mode": "simulator-only",
    }
    assert ready_payload["status"] == "ready"
    assert "database" not in ready_payload


@pytest.mark.parametrize("feature", ["content", "teaching", "ai", "ota"])
def test_future_capabilities_fail_closed(feature: str) -> None:
    values: dict[str, bool | str] = {"environment": "test", f"feature_{feature}": True}
    settings = Settings.model_validate(values)

    with pytest.raises(RuntimeError, match=feature):
        create_app(settings)


def test_console_runner_uses_selector_event_loop_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    served: dict[str, object] = {}

    class FakeServer:
        async def serve(self) -> None:
            return None

    def fake_asyncio_run(
        coroutine: Coroutine[object, object, None],
        *,
        loop_factory: object,
    ) -> None:
        coroutine.close()
        served["loop_factory"] = loop_factory

    def fake_server(config: object) -> FakeServer:
        return FakeServer()

    monkeypatch.setattr(api.sys, "platform", "win32")
    monkeypatch.setattr(api.uvicorn, "Server", fake_server)
    monkeypatch.setattr(api.asyncio, "run", fake_asyncio_run)

    api.run()

    assert served["loop_factory"] is api.asyncio.SelectorEventLoop


def test_console_runner_delegates_to_uvicorn_elsewhere(monkeypatch: pytest.MonkeyPatch) -> None:
    served: dict[str, bool] = {}

    class FakeServer:
        def run(self) -> None:
            served["run"] = True

    def fake_server(config: object) -> FakeServer:
        return FakeServer()

    monkeypatch.setattr(api.sys, "platform", "linux")
    monkeypatch.setattr(api.uvicorn, "Server", fake_server)

    api.run()

    assert served["run"] is True
