"""HuggingFace-backed text generation utilities."""

from __future__ import annotations

from typing import Optional


class LLMUtils:
    """Wrapper around a local HuggingFace pipeline."""

    def __init__(self, model_name: str = "distilgpt2") -> None:
        try:
            from transformers import pipeline  # type: ignore

            self.generator = pipeline(
                "text-generation", model=model_name, tokenizer=model_name
            )
        except Exception as exc:  # pragma: no cover - optional dependency
            self.generator = None
            self._counter = 0
            self._error: Optional[Exception] = exc

    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        if self.generator:
            outputs = self.generator(
                prompt, max_new_tokens=max_tokens, do_sample=False
            )
            return outputs[0]["generated_text"]

        # fallback when transformers or model is unavailable
        self._counter += 1
        return f"{prompt} #{self._counter}"
