import asyncio
import importlib.util
import os
import tempfile

tmp = tempfile.mkdtemp()
model_path = os.path.join(tmp, "llama3.gguf")
open(model_path, "w").close()
os.environ["KARI_MODEL_DIR"] = tmp
os.environ["OLLAMA_MODEL_NAME"] = "llama3.gguf"

spec = importlib.util.spec_from_file_location(
    "llama_client",
    "src/ai_karen_engine/plugins/llm_services/llama/llama_client.py",
)
llama_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llama_client)
OllamaEngine = llama_client.OllamaEngine


def test_achat_non_streaming():
    client = OllamaEngine(model_path=model_path)
    out = asyncio.run(client.achat([{"role": "user", "content": "hi"}], stream=False))
    assert isinstance(out, str)


def test_achat_streaming():
    client = OllamaEngine(model_path=model_path)
    async def gather():
        chunks = []
        async for c in client.achat([{"role": "user", "content": "hi"}], stream=True):
            chunks.append(c)
        return chunks
    result = asyncio.run(gather())
    assert result == ["a", "b"]
