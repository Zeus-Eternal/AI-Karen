import importlib
import sys

from ai_karen_engine.integrations import llm_utils
from ai_karen_engine.integrations.llm_utils import LLMUtils, LLMProviderBase


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



