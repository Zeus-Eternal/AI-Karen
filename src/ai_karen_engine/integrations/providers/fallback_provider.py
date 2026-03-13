"""Enhanced fallback provider with local model support.

This provider acts as an intelligent fallback when primary LLM providers fail.
It prioritizes local downloaded models (transformers, llama-cpp) before falling
back to deterministic responses, ensuring real AI responses even in offline mode.
"""

from __future__ import annotations

import hashlib
import logging
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from ai_karen_engine.integrations.llm_utils import (
    EmbeddingFailed,
    GenerationFailed,
    LLMProviderBase,
    record_llm_metric,
)

logger = logging.getLogger("kari.fallback_provider")


class FallbackProvider(LLMProviderBase):
    """Deterministic provider that keeps Kari responsive without real LLMs.

    The goal is graceful degradation: when "real" providers are unavailable the
    fallback still returns a contextual acknowledgement so that the UI and
    downstream services can verify the full request/response loop.
    """

    def __init__(
        self,
        model: str = "kari-fallback-v1",
        max_history: int = 5,
        **_: Any,
    ) -> None:
        self.model = model
        self.max_history = max_history
        self._history: List[str] = []
        self.last_usage: Dict[str, Any] = {}
        self.provider_name = "fallback"
        
        # Initialize local model paths
        self._local_models = self._discover_local_models()
        logger.info(f"FallbackProvider initialized with {len(self._local_models)} local models")

    # ------------------------------------------------------------------
    # Core helpers
    def _discover_local_models(self) -> Dict[str, str]:
        """Discover available local models on the system.
        
        Returns:
            Dictionary mapping model types to their paths
        """
        models = {}
        base_path = Path("/mnt/development/KIRO/AI-Karen/models")
        
        # Check for llama-cpp models
        llama_path = base_path / "llama-cpp"
        if llama_path.exists():
            gguf_files = list(llama_path.glob("*.gguf"))
            for gguf in gguf_files:
                # Skip zero-size files
                if gguf.stat().st_size > 1000:
                    models[f"llamacpp_{gguf.stem}"] = str(gguf)
                    logger.debug(f"Found llama-cpp model: {gguf.name}")
        
        # Check for transformers models
        transformers_path = base_path / "transformers"
        if transformers_path.exists():
            # Look for model directories (contain config.json or model files)
            for model_dir in transformers_path.iterdir():
                if model_dir.is_dir() and not model_dir.name.startswith('.'):
                    # Check if it's a valid model directory
                    if (model_dir / "config.json").exists() or \
                       (model_dir / "pytorch_model.bin").exists() or \
                       (model_dir / "model.safetensors").exists():
                        models[f"transformers_{model_dir.name}"] = str(model_dir)
                        logger.debug(f"Found transformers model: {model_dir.name}")
        
        logger.info(f"Discovered {len(models)} local models: {list(models.keys())}")
        return models
    
    def _try_local_llamacpp(self, prompt: str, **kwargs: Any) -> Optional[str]:
        """Try to use local llama-cpp model for generation.
        
        Returns:
            Generated text or None if failed
        """
        # Find llama-cpp model paths
        llama_models = {k: v for k, v in self._local_models.items() if k.startswith("llamacpp_")}
        
        if not llama_models:
            logger.debug("No local llama-cpp models found")
            return None
        
        # Try each model (prefer smaller models for speed)
        for model_name, model_path in sorted(llama_models.items(), 
                                           key=lambda x: Path(x[1]).stat().st_size):
            try:
                from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime
                
                logger.info(f"Attempting to use local model: {model_name}")
                
                # Initialize runtime if not already done
                if not hasattr(self, '_llamacpp_runtimes'):
                    self._llamacpp_runtimes = {}
                
                # Create or get cached runtime
                if model_name not in self._llamacpp_runtimes:
                    runtime = LlamaCppRuntime(
                        model_path=model_path,
                        n_ctx=2048,
                        n_batch=512,
                        n_threads=4
                    )
                    if not runtime.load_model(model_path):
                        logger.warning(f"Failed to load model: {model_name}")
                        continue
                    self._llamacpp_runtimes[model_name] = runtime
                
                # Generate response
                runtime = self._llamacpp_runtimes[model_name]
                response = runtime.generate(
                    prompt,
                    max_tokens=256,
                    temperature=0.7,
                    top_p=0.9,
                    stop=["\n\n", "Human:", "User:"]
                )
                
                if response and len(response.strip()) > 0:
                    logger.info(f"Successfully generated response using {model_name}")
                    return response
                
            except Exception as e:
                logger.warning(f"Failed to use {model_name}: {e}")
                continue
        
        return None
    
    def _try_local_transformers(self, prompt: str, **kwargs: Any) -> Optional[str]:
        """Try to use local transformers model for generation.
        
        Returns:
            Generated text or None if failed
        """
        # Find transformers model paths
        transformer_models = {k: v for k, v in self._local_models.items() if k.startswith("transformers_")}
        
        if not transformer_models:
            logger.debug("No local transformers models found")
            return None
        
        # Prefer specific chat models
        preferred_order = ["DialoGPT", "gpt2", "deepseek", "tinyllama"]
        
        for model_name in sorted(transformer_models.keys(), 
                                key=lambda x: any(p in x.lower() for p in preferred_order),
                                reverse=True):
            model_path = transformer_models[model_name]
            try:
                from ai_karen_engine.inference.transformers_runtime import TransformersRuntime
                
                logger.info(f"Attempting to use transformers model: {model_name}")
                
                # Initialize runtime if not already done
                if not hasattr(self, '_transformers_runtimes'):
                    self._transformers_runtimes = {}
                
                # Create or get cached runtime
                if model_name not in self._transformers_runtimes:
                    runtime = TransformersRuntime(
                        model_path=model_path,
                        device="cpu",  # Use CPU for compatibility
                        torch_dtype="float32"
                    )
                    if not runtime.load_model(model_path):
                        logger.warning(f"Failed to load transformers model: {model_name}")
                        continue
                    self._transformers_runtimes[model_name] = runtime
                
                # Generate response
                runtime = self._transformers_runtimes[model_name]
                response = runtime.generate(
                    prompt,
                    max_tokens=150,
                    temperature=0.8,
                    top_p=0.9,
                    do_sample=True
                )
                
                if response and len(response.strip()) > 0:
                    logger.info(f"Successfully generated response using {model_name}")
                    return response
                
            except Exception as e:
                logger.warning(f"Failed to use transformers model {model_name}: {e}")
                continue
        
        return None
    def _summarize_prompt(self, prompt: str) -> str:
        """Create a compact summary snippet for the prompt."""

        cleaned = " ".join(prompt.strip().split())
        if not cleaned:
            return "an empty prompt"

        words = cleaned.split(" ")
        if len(words) <= 16:
            return cleaned

        # Generate a deterministic checksum fragment so responses are stable
        digest = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:6]
        preview = " ".join(words[:16])
        return f"{preview}… (ref:{digest})"

    def _build_suggestions(self, prompt: str) -> List[str]:
        """Generate a couple of lightweight follow-up suggestions."""

        topics = [
            "analysis",
            "planning",
            "next steps",
            "limitations",
            "validation",
        ]
        # Deterministic shuffle based on prompt hash for variety without RNG drift
        digest = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        start = int(digest[:8], 16)
        ordered = topics[start % len(topics) :] + topics[: start % len(topics)]
        return [f"Explore {topic}." for topic in ordered[:2]]

    # ------------------------------------------------------------------
    # LLMProviderBase interface
    def generate_text(self, prompt: str, **kwargs: Any) -> str:  # type: ignore[override]
        """Intelligent fallback with local model support.
        
        Fallback hierarchy:
        1. Try registered llamacpp provider (if available)
        2. Try local llama-cpp models directly
        3. Try local transformers models
        4. Fall back to deterministic response
        """

        start = datetime.utcnow()
        error_details = []
        
        # Step 1: Try registered llamacpp provider
        try:
            from ai_karen_engine.integrations.llm_registry import get_registry
            registry = get_registry()
            llamacpp_provider = registry.get_provider("llamacpp")
            
            if llamacpp_provider:
                logger.info("Attempting to use registered llamacpp provider")
                real_response = llamacpp_provider.generate_text(prompt, **kwargs)
                if real_response and len(real_response.strip()) > 0:
                    logger.info("✓ Successfully used registered llamacpp provider")
                    return self._record_success(real_response, start, "registered_llamacpp")
        except Exception as e:
            error_details.append(f"Registered llamacpp: {str(e)}")
            logger.debug(f"Registered llamacpp provider failed: {e}")
        
        # Step 2: Try local llama-cpp models directly
        try:
            logger.info("Attempting to use local llama-cpp models")
            local_llama_response = self._try_local_llamacpp(prompt, **kwargs)
            if local_llama_response:
                logger.info("✓ Successfully used local llama-cpp model")
                return self._record_success(local_llama_response, start, "local_llamacpp")
        except Exception as e:
            error_details.append(f"Local llama-cpp: {str(e)}")
            logger.debug(f"Local llama-cpp failed: {e}")
        
        # Step 3: Try local transformers models
        try:
            logger.info("Attempting to use local transformers models")
            transformers_response = self._try_local_transformers(prompt, **kwargs)
            if transformers_response:
                logger.info("✓ Successfully used local transformers model")
                return self._record_success(transformers_response, start, "local_transformers")
        except Exception as e:
            error_details.append(f"Local transformers: {str(e)}")
            logger.debug(f"Local transformers failed: {e}")
        
        # Step 4: Intelligent deterministic fallback based on errors
        logger.warning(f"All model attempts failed. Using intelligent fallback. Errors: {error_details}")
        return self._intelligent_fallback(prompt, start, error_details, **kwargs)
    
    def _record_success(self, response: str, start: datetime, source: str) -> str:
        """Record successful generation metrics."""
        duration = (datetime.utcnow() - start).total_seconds()
        token_estimate = max(1, len(response.split()))
        
        self.last_usage = {
            "prompt_tokens": token_estimate,
            "completion_tokens": token_estimate,
            "total_tokens": token_estimate * 2,
            "cost": 0.0,
            "source": source,
        }
        
        record_llm_metric("generate_text", duration, True, source)
        return response
    
    def _intelligent_fallback(self, prompt: str, start: datetime, errors: List[str], **kwargs: Any) -> str:
        """Generate intelligent fallback response based on actual errors."""
        
        # Analyze errors to provide helpful guidance
        error_type = self._classify_error(errors)
        
        # Build context-aware response
        prompt_summary = self._summarize_prompt(prompt)
        self._history.append(prompt_summary)
        
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

        # Generate intelligent error message
        if error_type == "model_load_failed":
            message = f"""I apologize, but I'm having difficulty loading the local AI models. 

Based on your message about: {prompt_summary}

This appears to be a model loading issue. Here are some suggestions:
• Check if the model files exist in /mnt/development/KIRO/AI-Karen/models/
• Verify sufficient disk space and memory
• Check the application logs for specific error details

The system has {len(self._local_models)} local models discovered but unavailable."""
        
        elif error_type == "generation_failed":
            message = f"""I attempted to process your message about: {prompt_summary}

However, the AI generation encountered an error. This could be due to:
• Insufficient memory resources
• Model incompatibility with the request
• Temporary system resource constraints

Would you like to rephrase your request or try again?"""
        
        elif error_type == "no_models":
            message = f"""I received your message about: {prompt_summary}

However, no local AI models are currently available. The system needs:
• Local model files in /mnt/development/KIRO/AI-Karen/models/
• Proper model configuration and initialization

Please ensure models are downloaded and configured."""
        
        else:
            # Generic fallback with context
            suggestions = self._build_suggestions(prompt)
            message = f"""I understand you're asking about: {prompt_summary}

I'm currently in a degraded mode with limited AI capabilities. While I can't provide a full AI response right now, here are some next steps:

• {suggestions[0]}
• {suggestions[1]}

The system is working to restore full AI capabilities."""

        duration = (datetime.utcnow() - start).total_seconds()
        token_estimate = max(1, len(prompt.split()))
        
        self.last_usage = {
            "prompt_tokens": token_estimate,
            "completion_tokens": max(1, len(message.split()) // 2),
            "total_tokens": token_estimate + max(1, len(message.split()) // 2),
            "cost": 0.0,
            "source": "intelligent_fallback",
            "error_type": error_type,
        }

        record_llm_metric("generate_text", duration, True, "intelligent_fallback")
        return message
    
    def _classify_error(self, errors: List[str]) -> str:
        """Classify errors to provide intelligent fallback responses."""
        error_text = " ".join(errors).lower()
        
        if any(term in error_text for term in ["load", "not found", "file", "path"]):
            return "model_load_failed"
        elif any(term in error_text for term in ["generate", "inference", "runtime"]):
            return "generation_failed"
        elif any(term in error_text for term in ["no model", "not available", "empty"]):
            return "no_models"
        else:
            return "unknown_error"

    # The orchestrator prefers providers exposing ``generate_response`` (and
    # sometimes ``enhanced_generate_response``) so mirror ``generate_text`` to
    # keep compatibility with richer providers without duplicating logic.
    def generate_response(self, prompt: str, **kwargs: Any) -> str:  # type: ignore[override]
        return self.generate_text(prompt, **kwargs)

    def enhanced_generate_response(self, prompt: str, **kwargs: Any) -> str:  # type: ignore[override]
        return self.generate_text(prompt, **kwargs)

    def stream_generate(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Provide a very small streaming-compatible generator."""

        try:
            result = self.generate_text(prompt, **kwargs)
        except GenerationFailed as exc:  # pragma: no cover - defensive
            raise exc

        for chunk in textwrap.wrap(result, 80):
            yield chunk

    def embed(self, text: Any, **kwargs: Any) -> List[float]:  # type: ignore[override]
        """Produce a deterministic pseudo-embedding vector."""

        if isinstance(text, str):
            values = text
        elif isinstance(text, Iterable):
            values = " ".join(str(item) for item in text)
        else:
            raise EmbeddingFailed("Unsupported input type for fallback embeddings")

        digest = hashlib.sha1(values.encode("utf-8")).digest()
        # Create a small deterministic vector in range [-1, 1]
        vector = [((b / 255.0) * 2) - 1 for b in digest[:32]]
        if not vector:
            raise EmbeddingFailed("Unable to generate embedding")
        return vector

    def warm_cache(self) -> None:  # type: ignore[override]
        """Nothing to warm, but keep interface parity."""

        logger.debug("FallbackProvider warm_cache invoked - no action needed")

    # ------------------------------------------------------------------
    # Metadata helpers
    def get_provider_info(self) -> Dict[str, Any]:
        local_model_list = list(self._local_models.keys()) if self._local_models else []
        return {
            "name": "fallback",
            "model": self.model,
            "supports_streaming": False,
            "supports_embeddings": True,
            "description": "Intelligent fallback provider with local model support",
            "local_models_available": len(local_model_list),
            "local_model_names": local_model_list,
            "fallback_hierarchy": [
                "registered_llamacpp",
                "local_llamacpp",
                "local_transformers",
                "intelligent_fallback"
            ]
        }

    def health_check(self) -> Dict[str, Any]:
        health_status = {
            "status": "healthy",
            "message": "Fallback provider operational",
            "checked_at": datetime.utcnow().isoformat(),
            "local_models_count": len(self._local_models),
            "local_models_discovered": list(self._local_models.keys()) if self._local_models else [],
        }
        
        # Check if any local models are actually available
        if not self._local_models:
            health_status["warning"] = "No local models discovered - will use intelligent fallback only"
            health_status["status"] = "degraded"
        
        return health_status


__all__ = ["FallbackProvider"]

