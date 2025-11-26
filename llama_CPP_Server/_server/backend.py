"""
Backend adapter for llama.cpp.

This module wraps a simple abstraction so we can swap between:
- llama-cpp-python bindings (local inference)
- an existing llama.cpp HTTP server
- a stubbed backend for testing
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import llama-cpp-python, fall back to stub if not available
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
    logger.info("llama-cpp-python is available, using real backend")
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not available, using stub backend")


class BackendError(Exception):
    """Raised when the backend fails."""


class LocalLlamaBackend:
    """
    Backend wrapper for llama.cpp with fallback to stub if llama-cpp-python is not available.
    """

    def __init__(self, model_path: Path, threads: int, low_vram: bool = False, n_ctx: int = 4096) -> None:
        self.model_path = model_path
        self.threads = threads
        self.low_vram = low_vram
        self.n_ctx = n_ctx
        self.loaded = False
        self.model = None
        self.use_real_backend = LLAMA_CPP_AVAILABLE

    async def load(self) -> None:
        """Load the model using llama.cpp or stub if not available."""
        logger.info("Loading model %s (threads=%s low_vram=%s n_ctx=%s)",
                   self.model_path, self.threads, self.low_vram, self.n_ctx)
        
        if self.use_real_backend:
            try:
                # Load the model using llama-cpp-python
                self.model = Llama(
                    model_path=str(self.model_path),
                    n_threads=self.threads,
                    n_ctx=self.n_ctx,
                    low_mem=self.low_vram,
                    verbose=False
                )
                self.loaded = True
                logger.info("Model loaded successfully using llama.cpp")
            except Exception as e:
                logger.error(f"Failed to load model with llama.cpp: {e}")
                self.use_real_backend = False
                # Fall back to stub
                await self._stub_load()
        else:
            # Use stub implementation
            await self._stub_load()

    async def _stub_load(self) -> None:
        """Stub implementation for loading."""
        await asyncio.sleep(0.1)
        self.loaded = True
        logger.info("Model loaded using stub implementation")

    async def unload(self) -> None:
        """Unload the model."""
        logger.info("Unloading model %s", self.model_path)
        
        if self.use_real_backend and self.model:
            # Real llama.cpp models don't need explicit unloading
            # They'll be garbage collected
            self.model = None
        
        self.loaded = False
        logger.info("Model unloaded")

    async def perform_inference(self, prompt: str, params: Dict[str, Any]) -> str:
        """Perform inference using llama.cpp or stub if not available."""
        if not self.loaded:
            raise BackendError("Model not loaded")
        
        if self.use_real_backend and self.model:
            try:
                # Extract parameters with defaults
                temperature = params.get("temperature", 0.7)
                max_tokens = params.get("max_tokens", 2048)
                top_p = params.get("top_p", 0.9)
                
                # Generate response using llama.cpp
                response = self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=["User:", "System:"],  # Common stop tokens
                    echo=False
                )
                
                # Extract the generated text
                if isinstance(response, dict) and 'choices' in response:
                    generated_text = response['choices'][0]['text']
                    return generated_text.strip()
                else:
                    logger.error(f"Unexpected response format: {response}")
                    return "Error: Unexpected response format from model"
                    
            except Exception as e:
                logger.error(f"Inference failed with llama.cpp: {e}")
                # Fall back to stub
                return await self._stub_inference(prompt, params)
        else:
            # Use stub implementation
            return await self._stub_inference(prompt, params)

    async def _stub_inference(self, prompt: str, params: Dict[str, Any]) -> str:
        """Stub implementation for inference."""
        await asyncio.sleep(0.05)
        model_name = Path(self.model_path).stem if isinstance(self.model_path, str) else self.model_path.stem
        return f"[stub-{model_name}] {prompt[:200]}"

