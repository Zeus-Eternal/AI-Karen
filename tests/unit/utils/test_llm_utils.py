import importlib
import sys

from ai_karen_engine.integrations import llm_utils
from ai_karen_engine.integrations.llm_utils import (
    GenerationFailed,
    LLMProviderBase,
    LLMUtils,
)
from ai_karen_engine.integrations.providers.fallback_provider import FallbackProvider


class _DummyProvider(LLMProviderBase):
    def generate_text(self, prompt: str, **kwargs):
        return prompt

    def embed(self, text, **kwargs):
        return [0.0]


def test_llm_utils_fallback():
    llm = LLMUtils(providers={"dummy": _DummyProvider()}, default="dummy")
    out = llm.generate_text("hello")
    assert "hello" in out
    assert hasattr(llm, "providers")


def test_record_llm_metric_without_prometheus(monkeypatch):
    for mod in list(sys.modules):
        if mod.startswith("prometheus_client"):
            monkeypatch.delitem(sys.modules, mod, raising=False)
    monkeypatch.setitem(sys.modules, "prometheus_client", None)

    importlib.reload(llm_utils)
    llm_utils.record_llm_metric("test", 0.01, True, "dummy")
    importlib.reload(llm_utils)



def test_generate_text_skips_failing_registry_providers(monkeypatch):
    monkeypatch.setenv("AI_KAREN_ENABLE_FULL_REGISTRY", "true")

    fallback = FallbackProvider()

    class FakeRegistry:
        def get_available_providers(self):
            return ["broken", "fallback"]

        def auto_select_provider(self, requirements):
            return "fallback"

        def default_chain(self, healthy_only=False):
            return ["broken"]

        def list_providers(self):
            return ["broken", "fallback"]

        def get_provider(self, name, **_kwargs):
            if name == "broken":
                raise GenerationFailed("boom")
            if name == "fallback":
                return fallback
            raise GenerationFailed("unknown provider")

    monkeypatch.setattr(
        "ai_karen_engine.integrations.llm_registry.get_registry",
        lambda: FakeRegistry(),
    )

    llm = LLMUtils(default="broken", use_registry=True)
    response = llm.generate_text("Ensure fallback")

    assert "fallback assistant" in response


