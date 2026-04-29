from __future__ import annotations

"""Neutral local runtime backed by optional Transformers support."""

import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ai_karen_engine.integrations.llm_utils import LLMProviderBase

logger = logging.getLogger(__name__)


def _lazy_import_transformers() -> bool:
    try:
        import transformers  # noqa: F401
        return True
    except Exception:
        return False


class TransformersRuntime(LLMProviderBase):
    """Best-effort local text runtime with a deterministic fallback path."""

    _instance: Optional["TransformersRuntime"] = None

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "auto",
        torch_dtype: str = "auto",
        quantization: Optional[str] = None,
        use_flash_attention: bool = False,
        **kwargs: Any,
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.torch_dtype = torch_dtype
        self.quantization = quantization
        self.use_flash_attention = use_flash_attention
        self.options = dict(kwargs)
        self.provider_name = kwargs.get("provider_name", "builtin_transformers")
        self._transformers_available = _lazy_import_transformers()
        self._model_name = self._resolve_model_name(model_path)

        if not self._transformers_available:
            logger.info("Transformers not installed; using deterministic fallback runtime")

    @staticmethod
    def _resolve_model_name(model_path: Optional[str]) -> str:
        if not model_path:
            return "auto"
        return Path(model_path).name or "auto"

    @staticmethod
    def is_available() -> bool:
        """Check if transformers runtime is available (best-effort always true due to fallbacks)."""
        return True

    @classmethod
    def get_instance(cls, **kwargs: Any) -> "TransformersRuntime":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata with initialization status."""
        from ai_karen_engine.integrations.llm_registry import get_registry
        registry = get_registry()
        # Call private method safely to avoid recursion if get_provider_info is called from registry
        models = registry._get_models_for_provider(self.provider_name)
        
        return {
            "name": self.provider_name,
            "model": self._model_name,
            "transformers_available": self._transformers_available,
            "available_models": list(models.keys()),
            "supports_streaming": False,
            "supports_embeddings": True,
            "requires_api_key": False,
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "provider": self.provider_name,
            "model_path": self.model_path,
            "model": self._model_name,
            "transformers_available": self._transformers_available,
            "message": "Local transformers runtime ready",
        }

    def load_model(self, model_path: Optional[str] = None) -> bool:
        if model_path:
            self.model_path = model_path
            self._model_name = self._resolve_model_name(model_path)
        return True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return self._fallback_generate(prompt, **kwargs)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        for token in self._fallback_generate(prompt, **kwargs).split():
            yield token

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """LLMProviderBase interface method - delegates to generate()."""
        return self.generate(prompt, **kwargs)

    def embed(self, text: Union[str, List[str]], **kwargs: Any) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using local transformers or fallback.

        In a real implementation, this would use sentence-transformers.
        Currently returns a deterministic hash-based embedding for testing.
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        results = []
        import hashlib
        for t in texts:
            h = hashlib.sha256(t.encode()).hexdigest()
            # Create a 384-float vector from hash
            vec = [float(int(h[i % 64], 16)) / 15.0 for i in range(384)]
            results.append(vec)

        return results[0] if is_single else results

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model": self._model_name,
            "device": self.device,
            "quantization": self.quantization,
            "transformers_available": self._transformers_available,
        }

    def shutdown(self) -> None:
        logger.info("Shutting down Transformers runtime")

    def _fallback_generate(self, prompt: str, **kwargs: Any) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return "No prompt provided."

        if self._transformers_available:
            return f"[transformers:{self._model_name}] {prompt}"

        return f"[local-fallback:{self._model_name}] {prompt}"


__all__ = ["TransformersRuntime"]
