"""HuggingFace-backed text generation utilities with optional caching."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class LLMUtils:
    """Wrapper around a local HuggingFace pipeline with auto-download."""

    def __init__(self, model_name: str = "distilgpt2", cache_dir: str | None = None) -> None:
        self.model_name = model_name
        self.cache_dir = Path(cache_dir or Path.home() / ".cache" / "hf_models" / model_name)
        try:
            from transformers import pipeline  # type: ignore
            from huggingface_hub import snapshot_download  # type: ignore

            # attempt to ensure the model is cached locally
            try:
                snapshot_download(
                    repo_id=model_name,
                    local_dir=str(self.cache_dir),
                    local_dir_use_symlinks=True,
                    resume_download=True,
                    local_files_only=True,
                )
                model_path = str(self.cache_dir)
            except Exception:
                model_path = model_name

            self.generator = pipeline(
                "text-generation",
                model=model_path,
                tokenizer=model_path,
                cache_dir=str(self.cache_dir),
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
