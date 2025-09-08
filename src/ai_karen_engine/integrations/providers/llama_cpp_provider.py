"""
LlamaCpp Provider Implementation

Manages local llama.cpp model integration with support for GGUF models.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ai_karen_engine.integrations.llm_utils import (
    EmbeddingFailed,
    GenerationFailed,
    LLMProviderBase,
    record_llm_metric,
)

logger = logging.getLogger("kari.llamacpp_provider")


class LlamaCppProvider(LLMProviderBase):
    """Provider for local llama.cpp model execution."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        context_length: int = 4096,
        threads: Optional[int] = None,
        batch_size: int = 512,
        gpu_layers: int = 0,
    ):
        """
        Initialize LlamaCpp provider.

        Args:
            model_path: Path to GGUF model file (required)
            context_length: Model context window size
            threads: Number of CPU threads (default: auto)
            batch_size: Batch size for inference
            gpu_layers: Number of layers to offload to GPU (0 for CPU-only)
        """
        self.model_path = model_path
        self.context_length = context_length
        self.threads = threads or max(1, os.cpu_count() or 1)
        self.batch_size = batch_size
        self.gpu_layers = gpu_layers
        self._model = None
        self._tokenizer = None

        # Import llama-cpp-python lazily to avoid startup dependency
        try:
            from llama_cpp import Llama, LlamaGrammar
            self.Llama = Llama
            self.LlamaGrammar = LlamaGrammar
        except ImportError:
            raise RuntimeError(
                "llama-cpp-python not installed. Install with: pip install llama-cpp-python"
            )

        if not self.model_path:
            raise ValueError("model_path is required for LlamaCpp provider")

        # Ensure model file exists
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        # Load model on initialization
        self._load_model()

    def _load_model(self):
        """Load the GGUF model using llama-cpp-python."""
        try:
            self._model = self.Llama(
                model_path=self.model_path,
                n_ctx=self.context_length,
                n_threads=self.threads,
                n_batch=self.batch_size,
                n_gpu_layers=self.gpu_layers,
            )
            logger.info(
                f"Loaded model: {self.model_path} (context={self.context_length}, threads={self.threads})"
            )
        except Exception as ex:
            raise RuntimeError(f"Failed to load model: {ex}")

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        try:
            return {
                "name": "llama-cpp",
                "description": "Local llama.cpp GGUF model integration",
                "model_path": self.model_path,
                "context_length": self.context_length,
                "threads": self.threads,
                "batch_size": self.batch_size,
                "gpu_layers": self.gpu_layers,
                "loaded": self._model is not None,
                "supports_streaming": True,
                "supports_embeddings": True,
                "requires_api_key": False,
            }
        except Exception as ex:
            logger.error(f"Failed to get provider info: {ex}")
            return {
                "name": "llama-cpp",
                "error": str(ex),
                "loaded": False,
            }

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        """Generate text completion."""
        try:
            if not self._model:
                raise RuntimeError("Model not loaded")

            # Record start time for metrics
            start_time = time.perf_counter()

            completion = self._model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or [],
            )

            # Record metrics
            duration = time.perf_counter() - start_time
            record_llm_metric(
                "llamacpp_generate",
                duration,
                {"model": self.model_path, "tokens": len(completion["choices"][0]["text"])},
            )

            return completion["choices"][0]["text"]

        except Exception as ex:
            raise GenerationFailed(f"LlamaCpp generation failed: {ex}")

    def generate_text_stream(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> Iterator[str]:
        """Generate streaming text completion."""
        try:
            if not self._model:
                raise RuntimeError("Model not loaded")

            # Record start time for metrics
            start_time = time.perf_counter()
            total_tokens = 0

            for chunk in self._model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or [],
                stream=True,
            ):
                text = chunk["choices"][0]["text"]
                total_tokens += 1
                yield text

            # Record metrics after stream completes
            duration = time.perf_counter() - start_time
            record_llm_metric(
                "llamacpp_generate_stream",
                duration,
                {"model": self.model_path, "tokens": total_tokens},
            )

        except Exception as ex:
            raise GenerationFailed(f"LlamaCpp streaming failed: {ex}")

    def embed_text(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Generate text embeddings."""
        try:
            if not self._model:
                raise RuntimeError("Model not loaded")

            # Ensure text is a string
            if isinstance(text, list):
                text = " ".join(text)

            # Record start time for metrics
            start_time = time.perf_counter()

            # Generate embeddings using the model's embed() method
            embedding = self._model.embed(text)

            # Record metrics
            duration = time.perf_counter() - start_time
            record_llm_metric(
                "llamacpp_embed",
                duration,
                {"model": self.model_path},
            )

            return embedding.tolist()

        except Exception as ex:
            raise EmbeddingFailed(f"LlamaCpp embedding failed: {ex}")

    def health_check(self) -> Dict[str, Any]:
        """Check provider health by attempting a small completion."""
        try:
            if not self._model:
                return {
                    "status": "unhealthy",
                    "message": "Model not loaded",
                    "error": "Model initialization failed",
                }

            # Try a minimal completion
            start_time = time.perf_counter()
            _ = self.generate_text("Test.", max_tokens=1)
            response_time = time.perf_counter() - start_time

            return {
                "status": "healthy",
                "message": "Model loaded and responsive",
                "response_time": response_time,
                "model_path": self.model_path,
                "context_length": self.context_length,
            }

        except Exception as ex:
            return {
                "status": "unhealthy",
                "message": "Health check failed",
                "error": str(ex),
                "model_path": self.model_path,
            }

    def cleanup(self):
        """Clean up resources."""
        if self._model:
            del self._model
            self._model = None
