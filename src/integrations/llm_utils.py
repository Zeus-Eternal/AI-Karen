"""HuggingFace-backed text generation utilities with auto-download and fallback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependencies
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        pipeline,
        Pipeline,
        set_seed,
    )
    from transformers.pipelines.base import PipelineException
except Exception:  # library missing
    AutoTokenizer = AutoModelForCausalLM = pipeline = None  # type: ignore
    Pipeline = None  # type: ignore
    def set_seed(_seed: int) -> None:  # type: ignore
        pass

    class PipelineException(Exception):
        pass

try:  # pragma: no cover - optional dependency
    from huggingface_hub import snapshot_download
except Exception:  # pragma: no cover
    snapshot_download = None  # type: ignore

logger = logging.getLogger(__name__)


class LLMUtils:
    """Wrapper around HuggingFace text generation with auto-download fallback."""

    def __init__(
        self,
        model_name: str = "distilgpt2",
        cache_dir: str | None = None,
        seed: int = 42,
    ) -> None:
        self.model_name = model_name
        self.cache_dir = Path(
            cache_dir or Path.home() / ".cache" / "hf_models" / model_name
        )
        self._counter = 0
        self._error: Optional[Exception] = None
        self.generator: Optional[Pipeline] = None

        if AutoTokenizer is None or AutoModelForCausalLM is None or pipeline is None or snapshot_download is None:
            logger.warning("transformers or huggingface_hub unavailable; using mock generator")
            self.generator = None
            self._error = ImportError("transformers or huggingface_hub missing")
            return

        set_seed(seed)

        try:
            # Force download if missing
            logger.info(f"Ensuring model is downloaded: {model_name}")
            snapshot_download(
                repo_id=model_name,
                local_dir=str(self.cache_dir),
                local_dir_use_symlinks=True,
                resume_download=True,
            )

            model_path = str(self.cache_dir)

            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(model_path)

            self.generator = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
            )

            logger.info(f"Model pipeline ready: {model_name}")

        except Exception as e:
            logger.warning(f"Model fallback engaged: {e}")
            self._error = e
            self.generator = None

    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        """Generate text using the underlying model or fallback."""

        if self.generator:
            try:
                outputs = self.generator(
                    prompt,
                    max_new_tokens=max_tokens,
                    do_sample=False,
                    pad_token_id=self.generator.tokenizer.eos_token_id,
                )
                return outputs[0]["generated_text"]
            except PipelineException as pipe_exc:
                logger.error(f"Pipeline error: {pipe_exc}")
            except Exception as err:
                logger.exception("Generation failed, falling back: %s", err)

        self._counter += 1
        return f"{prompt.strip()} (mock #{self._counter})"
