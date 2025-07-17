import asyncio
import sys
import types
import tempfile
import os
import importlib
from pathlib import Path

sys.modules.setdefault(
    "ai_karen_engine.plugins.llm_services.llama.handler", types.SimpleNamespace(router=None)
)


class DummyLlama:
    def __init__(self, *a, **k):
        pass

    def create_completion(self, prompt, stream=False, **kwargs):
        if stream:
            for ch in ["a", "b"]:
                yield {"choices": [{"text": ch}]}
        else:
            return {"choices": [{"text": "ab"}]}

    def embed(self, text):
        return [0.0]


sys.modules.setdefault("llama_cpp", types.SimpleNamespace(Llama=DummyLlama))

tmp = tempfile.mkdtemp()
Path(tmp, "model.gguf").touch()
Path(tmp, "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf").touch()
os.environ["KARI_MODEL_DIR"] = tmp
os.environ["OLLAMA_MODEL_NAME"] = "model.gguf"

module = importlib.import_module(
    "ai_karen_engine.plugins.llm_services.llama.llama_client"
)
OllamaEngine = module.OllamaEngine


class DummyEngine(OllamaEngine):
    def __init__(self):
        # avoid loading real models
        pass


def test_achat_non_stream(monkeypatch):
    engine = DummyEngine()
    monkeypatch.setattr(engine, "chat", lambda msgs, stream=False, **k: "ok")

    async def run():
        return [chunk async for chunk in engine.achat([{"role": "user", "content": "hi"}], stream=False)]

    result = asyncio.run(run())
    assert result == ["ok"]


def test_achat_stream(monkeypatch):
    engine = DummyEngine()

    def fake_chat(msgs, stream=False, **k):
        if stream:
            yield "a"
            yield "b"
        else:
            return "ab"

    monkeypatch.setattr(engine, "chat", fake_chat)

    async def run():
        return [chunk async for chunk in engine.achat([{"role": "user", "content": "hi"}], stream=True)]

    result = asyncio.run(run())
    assert result == ["a", "b"]
