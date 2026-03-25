"""
Dynamic model loading and management.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .backend import LocalLlamaBackend, BackendError
from .utils import Stopwatch
from .config import ServerConfig

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.models_dir = Path(config.get("models.directory"))
        self.max_loaded = config.get("models.max_loaded_models", 2)
        self.loaded: Dict[str, LocalLlamaBackend] = {}
        self.available: Dict[str, Dict[str, Any]] = {}
        self.current_model: Optional[str] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        await self.scan()
        default_model = self.config.get("models.default_model")
        if self.config.get("models.auto_load_default") and default_model:
            await self.load_model(default_model)

    async def scan(self) -> None:
        self.available.clear()
        for path in self.models_dir.rglob("*.gguf"):
            model_id = path.stem
            self.available[model_id] = {
                "id": model_id,
                "name": path.name,
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "modified_ts": path.stat().st_mtime,
            }
        logger.info("Discovered %s model(s)", len(self.available))

    async def load_model(self, model_id: str) -> bool:
        async with self._lock:
            if model_id in self.loaded:
                self.current_model = model_id
                return True
            info = self.available.get(model_id)
            if not info:
                logger.error("Model %s not found", model_id)
                return False

            if len(self.loaded) >= self.max_loaded:
                # simple LRU eviction: pop first inserted
                evict_id = next(iter(self.loaded.keys()))
                await self.unload_model(evict_id)

            # Get backend configuration
            backend_config = self.config.get("backend", {})
            backend_type = backend_config.get("type", "auto")
            local_config = backend_config.get("local", {})
            
            # Create backend with configuration
            backend = LocalLlamaBackend(
                model_path=Path(info["path"]),
                threads=local_config.get("n_threads", self.config.get("performance.num_threads", 4)),
                low_vram=local_config.get("low_mem", self.config.get("performance.low_vram", False)),
                n_ctx=local_config.get("n_ctx", 4096)
            )
            timer = Stopwatch()
            try:
                await backend.load()
                self.loaded[model_id] = backend
                self.current_model = model_id
                logger.info("Loaded model %s in %.2fms", model_id, timer.ms())
                return True
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to load model %s: %s", model_id, exc)
                return False

    async def unload_model(self, model_id: str) -> bool:
        async with self._lock:
            backend = self.loaded.get(model_id)
            if not backend:
                return True
            try:
                await backend.unload()
            finally:
                self.loaded.pop(model_id, None)
                if self.current_model == model_id:
                    self.current_model = None
            return True

    async def inference(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with self._lock:
            if not self.current_model:
                raise BackendError("No model loaded")
            backend = self.loaded[self.current_model]
        timer = Stopwatch()
        response = await backend.perform_inference(prompt, params)
        duration_ms = timer.ms()
        return {
            "response": response,
            "model_id": self.current_model,
            "duration_ms": duration_ms,
        }

    async def status(self) -> Dict[str, Any]:
        return {
            "available": list(self.available.values()),
            "loaded": list(self.loaded.keys()),
            "current": self.current_model,
        }

    async def cleanup(self) -> None:
        async with self._lock:
            for mid in list(self.loaded.keys()):
                await self.unload_model(mid)
