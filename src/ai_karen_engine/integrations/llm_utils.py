"""LLM utilities with HuggingFace text generation, SentenceTransformer inference,
benchmark-aware fallback, and optional quantized model wrappers."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        pipeline,
        Pipeline,
        set_seed,
    )
    from transformers.pipelines.base import PipelineException
except Exception:
    AutoTokenizer = AutoModelForCausalLM = pipeline = None  # type: ignore
    Pipeline = None  # type: ignore

    def set_seed(_seed: int) -> None:
        pass

    class PipelineException(Exception):
        pass

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # type: ignore

try:
    from huggingface_hub import snapshot_download
except Exception:
    snapshot_download = None  # type: ignore

logger = logging.getLogger(__name__)


class LLMUtils:
    """HuggingFace text generation + embedding inference + latency-based fallback."""

    def __init__(
        self,
        model_name: str = "distilgpt2",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_dir: str | None = None,
        seed: int = 42,
        max_latency_ms: int = 3000,
    ) -> None:
        self.model_name = model_name
        self.embedding_model_name = embedding_model
        self.cache_dir = Path(
            cache_dir or Path.home() / ".cache" / "hf_models" / model_name
        )
        self._counter = 0
        self._error: Optional[Exception] = None
        self.max_latency_ms = max_latency_ms
        self.generator: Optional[Pipeline] = None
        self.embedder: Optional[SentenceTransformer] = None

        if AutoTokenizer is None or AutoModelForCausalLM is None or pipeline is None or snapshot_download is None:
            logger.warning("transformers or huggingface_hub unavailable; using mock generator")
            self._error = ImportError("transformers or huggingface_hub missing")
        else:
            set_seed(seed)
            self._load_generation_pipeline()

        if SentenceTransformer:
            try:
                self.embedder = SentenceTransformer(self.embedding_model_name)
                logger.info(f"Embedding model loaded: {self.embedding_model_name}")
            except Exception as e:
                logger.warning(f"Embedding model failed: {e}")
                self.embedder = None

    def _load_generation_pipeline(self) -> None:
        try:
            logger.info(f"Ensuring model is downloaded: {self.model_name}")
            snapshot_download(
                repo_id=self.model_name,
                local_dir=str(self.cache_dir),
                local_dir_use_symlinks=True,
                resume_download=True,
            )
            tokenizer = AutoTokenizer.from_pretrained(str(self.cache_dir))
            model = AutoModelForCausalLM.from_pretrained(str(self.cache_dir))

            self.generator = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
            )
            logger.info(f"Text generator ready: {self.model_name}")

        except Exception as e:
            logger.warning(f"Model load failed: {e}")
            self._error = e
            self.generator = None

    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        """Generate text, falling back if latency > max_latency_ms or model fails."""

        if self.generator:
            try:
                start = time.perf_counter()
                outputs = self.generator(
                    prompt,
                    max_new_tokens=max_tokens,
                    do_sample=False,
                    pad_token_id=self.generator.tokenizer.eos_token_id,
                )
                latency = (time.perf_counter() - start) * 1000

                if latency > self.max_latency_ms:
                    logger.warning(f"Latency {latency:.2f}ms exceeded threshold; using fallback.")
                    raise TimeoutError("Generation too slow")

                return outputs[0]["generated_text"]

            except (PipelineException, TimeoutError) as pipe_exc:
                logger.error(f"Generation error: {pipe_exc}")
            except Exception as err:
                logger.exception("Generation failed: %s", err)

        self._counter += 1
        return f"{prompt.strip()} (mock #{self._counter})"

    def embed_text(self, text: str) -> list[float]:
        """Generate dense embedding vector for given text input."""
        if not self.embedder:
            raise RuntimeError("SentenceTransformer not available")

        return self.embedder.encode(text, normalize_embeddings=True).tolist()

    def get_error(self) -> Optional[Exception]:
        return self._error
