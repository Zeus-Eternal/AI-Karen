import pytest

from ai_karen_engine.services.llm_router import ChatRequest, LLMRouter


class _SyncFallbackProvider:
    """Simple synchronous provider used to verify router compatibility."""

    def __init__(self) -> None:
        self.called = []

    def generate_response(self, prompt: str, **kwargs: object) -> str:
        self.called.append(("generate_response", prompt, kwargs))
        return f"response:{prompt}"

    def stream_generate(self, prompt: str, **kwargs: object):
        self.called.append(("stream_generate", prompt, kwargs))
        yield f"chunk:{prompt}"


class _DummyRegistry:
    def __init__(self, provider: _SyncFallbackProvider) -> None:
        self._provider = provider

    def get_provider(self, name: str, model: object | None = None) -> _SyncFallbackProvider:
        return self._provider

    def list_providers(self) -> list[str]:
        return ["fallback"]

    def get_provider_info(self, name: str) -> dict[str, object]:
        return {"default_model": None, "supports_streaming": False, "requires_api_key": False}

    def health_check(self, name: str) -> dict[str, str]:
        return {"status": "healthy"}


@pytest.mark.asyncio
async def test_process_with_provider_handles_sync_generation() -> None:
    provider = _SyncFallbackProvider()
    router = LLMRouter(registry=_DummyRegistry(provider))

    request = ChatRequest(message="hello", stream=False)
    chunks = [chunk async for chunk in router._process_with_provider("fallback", request)]

    assert chunks == ["response:hello"]
    assert provider.called[0][0] == "generate_response"


@pytest.mark.asyncio
async def test_process_with_provider_streams_sync_generator() -> None:
    provider = _SyncFallbackProvider()
    router = LLMRouter(registry=_DummyRegistry(provider))

    request = ChatRequest(message="world", stream=True)
    chunks = [chunk async for chunk in router._process_with_provider("fallback", request)]

    assert chunks == ["chunk:world"]
    assert provider.called[0][0] == "stream_generate"
