import pytest

from ai_karen_engine.services.llm_router import ChatRequest, LLMRouter


class DummyRegistry:
    def list_providers(self):
        return ["openai", "gemini"]

    def get_provider_info(self, name):
        defaults = {
            "openai": {"default_model": "gpt-3.5-turbo", "supports_streaming": True, "requires_api_key": True},
            "gemini": {"default_model": "gemini-1.5-flash", "supports_streaming": True, "requires_api_key": True},
        }
        return defaults.get(name)

    def get_provider(self, name, **kwargs):  # pragma: no cover - not used in test
        return object()

    def health_check(self, name):
        return {"status": "healthy"}


@pytest.mark.asyncio
async def test_preferred_model_selection():
    registry = DummyRegistry()
    router = LLMRouter(registry=registry)
    req = ChatRequest(message="hi", preferred_model="gpt-3.5-turbo")
    provider = await router.select_provider(req)
    assert provider == ("openai", "gpt-3.5-turbo")
