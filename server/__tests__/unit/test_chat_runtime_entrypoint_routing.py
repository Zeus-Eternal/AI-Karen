import pytest


class _RuntimeStub:
    def __init__(self):
        self.calls = 0

    async def get_orchestrator(self):
        self.calls += 1
        return object()


@pytest.mark.asyncio
async def test_runtime_route_uses_canonical_runtime_entrypoint(monkeypatch):
    from ai_karen_engine.api_routes.chat import runtime as runtime_route

    stub = _RuntimeStub()
    monkeypatch.setattr(runtime_route, "get_chat_runtime_service", lambda: stub)

    result = await runtime_route.get_chat_orchestrator()
    assert result is not None
    assert stub.calls == 1


@pytest.mark.asyncio
async def test_websocket_gateway_uses_canonical_runtime_entrypoint():
    from ai_karen_engine.api_routes.chat import websocket as websocket_route

    stub = _RuntimeStub()

    gateway = await websocket_route.get_websocket_gateway(runtime_service=stub)
    assert gateway is not None
    assert stub.calls == 1


@pytest.mark.asyncio
async def test_copilot_route_uses_canonical_runtime_entrypoint(monkeypatch):
    from ai_karen_engine.api_routes.chat import copilot as copilot_route

    stub = _RuntimeStub()
    monkeypatch.setattr(copilot_route, "get_chat_runtime_service", lambda: stub)

    result = await copilot_route._get_chat_orchestrator()
    assert result is not None
    assert stub.calls == 1
