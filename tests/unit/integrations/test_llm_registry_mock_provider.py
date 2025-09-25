import pytest

from ai_karen_engine.integrations.llm_registry import LLMRegistry
from ai_karen_engine.integrations.providers.mock_provider import MockLLMProvider


class BrokenProvider:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("boom")


@pytest.fixture()
def registry():
    return LLMRegistry()


def test_mock_provider_registered_by_default(registry):
    provider = registry.get_provider("mock")
    assert isinstance(provider, MockLLMProvider)
    response = provider.generate_text("Hello there")
    assert "mock provider" in response


def test_falls_back_to_mock_when_provider_unavailable(monkeypatch, registry):
    original = registry._get_provider_class

    def fake_get_provider_class(class_name):
        if class_name == "LlamaCppProvider":
            return BrokenProvider
        return original(class_name)

    monkeypatch.setattr(registry, "_get_provider_class", fake_get_provider_class)

    provider = registry.get_provider("llamacpp")
    assert isinstance(provider, MockLLMProvider)

    # cached instance should be reused without reattempting the broken provider
    second = registry.get_provider("llamacpp")
    assert provider is second
