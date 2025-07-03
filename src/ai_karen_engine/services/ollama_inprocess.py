"""Local GGUF inference without an Ollama server."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import asyncio

try:  # pragma: no cover - optional dependency
    from llama_cpp import Llama  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    Llama = None  # type: ignore
    _IMPORT_ERROR: Optional[Exception] = exc

_MODEL_CACHE: dict[str, "Llama"] = {}


def _load(model_path: str) -> Optional["Llama"]:
    if not Llama:
        return None
    if model_path not in _MODEL_CACHE:
        if not Path(model_path).exists():
            return None
        _MODEL_CACHE[model_path] = Llama(model_path=model_path)
    return _MODEL_CACHE[model_path]


def generate(prompt: str, model_path: str, *, max_tokens: int = 128) -> str:
    """Generate text using llama-cpp or fallback to ``ollama``."""
    model = _load(model_path)
    if model:
        output = model.create(prompt=prompt, max_tokens=max_tokens, stream=False)
        return output["choices"][0]["text"]

    try:  # pragma: no cover - optional dependency
        import ollama  # type: ignore

        resp = ollama.chat(
            model=Path(model_path).stem,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp["message"]["content"]
    except Exception:
        return f"{prompt} (model unavailable)"


async def async_generate(prompt: str, model_path: str, max_tokens: int = 128) -> str:
    return await asyncio.to_thread(generate, prompt, model_path, max_tokens=max_tokens)
