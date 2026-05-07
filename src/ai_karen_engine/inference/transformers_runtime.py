from __future__ import annotations

"""Neutral local runtime backed by optional Transformers support."""

import logging
import threading
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ai_karen_engine.integrations.llm_utils import LLMProviderBase, ProviderNotAvailable, GenerationFailed

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
        self._pipeline = None
        self._lock = threading.Lock()

        if not self._transformers_available:
            logger.info("Transformers not installed; using deterministic fallback runtime")
        elif model_path:
            # Pre-warm if model path is provided
            threading.Thread(target=self.warm, args=(model_path,), daemon=True).start()

    def _resolve_model_name(self, model_path: Optional[str]) -> str:
        """Resolve a human-readable model name from a path or ID."""
        if not model_path or model_path == "auto":
            return "gpt2"
        
        # Strip directory path if it's a file path
        name = Path(model_path).name
        # Remove common extensions
        if name.endswith(".gguf"):
            name = name[:-5]
        
        return name

    def warm(self, model_path: Optional[str] = None) -> bool:
        """Pre-load the model pipeline to avoid cold-start latency."""
        if not self._transformers_available:
            return False
            
        target_path = model_path or self.model_path
        
        # Handle 'auto' or None by resolving to default
        if not target_path or target_path == "auto":
            from ai_karen_engine.config.config_manager import config_manager
            target_path = config_manager.get_config_value("llm.default_model", default="gpt2")
            # If it's an absolute path that doesn't exist, try local
            import os
            if target_path.startswith("/") and not os.path.exists(target_path):
                target_path = target_path.split("/")[-1]

        if not target_path:
            logger.debug("No model path provided for pre-warming")
            return False

        with self._lock:
            if self._pipeline and (not model_path or target_path == self.model_path):
                return True

            try:
                import torch
                from transformers import pipeline

                logger.info(f"Pre-warming Transformers pipeline for {target_path} on {self.device}")
                
                # Determine device index
                device_idx = -1
                if self.device == "auto":
                    device_idx = 0 if torch.cuda.is_available() else -1
                elif self.device.startswith("cuda"):
                    try:
                        device_idx = int(self.device.split(":")[1]) if ":" in self.device else 0
                    except (ValueError, IndexError):
                        device_idx = 0
                
                dtype = torch.float16 if torch.cuda.is_available() and self.torch_dtype == "auto" else "auto"
                
                self._pipeline = pipeline(
                    "text-generation",
                    model=target_path,
                    device=device_idx,
                    torch_dtype=dtype,
                    model_kwargs={"low_cpu_mem_usage": True}
                )
                self.model_path = target_path
                self._model_name = self._resolve_model_name(target_path)
                logger.info(f"Transformers pipeline warmed successfully for {self._model_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to pre-warm Transformers pipeline: {e}")
                return False

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using a real transformers pipeline."""
        if not self._pipeline and self._transformers_available:
            self.warm(self.model_path)

        if self._pipeline:
            try:
                max_new_tokens = kwargs.get("max_new_tokens") or kwargs.get("max_tokens") or 128
                temperature = kwargs.get("temperature")
                if temperature is None:
                    temperature = 0.7
                else:
                    temperature = float(temperature)

                result = self._pipeline(
                    prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    pad_token_id=self._pipeline.tokenizer.eos_token_id
                )

                if result and isinstance(result, list) and "generated_text" in result[0]:
                    generated = result[0]["generated_text"]
                    if generated.startswith(prompt):
                        generated = generated[len(prompt):].strip()
                    if generated:
                        return generated
            except Exception as e:
                logger.warning(f"Transformers generation failed: {e}.")

        if not self._transformers_available:
            raise ProviderNotAvailable("Transformers runtime is not available")
        raise GenerationFailed("Transformers generation failed")

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        raise ProviderNotAvailable("Streaming unavailable without active transformers pipeline")

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

    @classmethod
    def get_instance(cls, **kwargs: Any) -> "TransformersRuntime":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    def get_provider_info(self) -> Dict[str, Any]:

        return {
            "name": getattr(self, "provider_name", "builtin_transformers"),
            "provider_type": "local",
            "runtime": "transformers",
            "requires_api_key": False,
            "has_api_key": True,
            "api_key_valid": True,
            "available_models": [self._model_name],
            "default_model": self._model_name,
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
            # If we reach here, Transformers is installed but generation failed/bypassed
            text = "I'm processing your request using local resources, but I'm currently experiencing high latency. Please bear with me or try again in a moment."
        else:
            text = "I'm currently operating in a limited capacity mode. Please check my configuration or try again later."

        return ResponseSanitizer().sanitize(text)


__all__ = ["TransformersRuntime"]
