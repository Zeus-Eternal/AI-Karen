"""
Optimized LLaMA-CPP Provider Implementation

This optimized version addresses performance issues by:
1. Adding proper async support with run_in_executor
2. Implementing better timeout handling
3. Adding performance monitoring and logging
4. Optimizing model loading and initialization
5. Improving error handling and fallback mechanisms
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ai_karen_engine.integrations.llm_utils import (
    LLMProviderBase,
    GenerationFailed,
    EmbeddingFailed,
    record_llm_metric,
)
from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime

logger = logging.getLogger("kari.llamacpp_provider_optimized")


class OptimizedLlamaCppProvider(LLMProviderBase):
    """Optimized LLaMA-CPP provider with improved performance and async support."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: Optional[int] = None,
        n_batch: Optional[int] = None,
        n_gpu_layers: Optional[int] = None,
        n_threads: Optional[int] = None,
        timeout: int = 30,  # Reduced default timeout
        **kwargs,
    ):
        """Initialize optimized LLaMA-CPP provider."""
        self.model_path = model_path
        self.timeout = timeout
        self.runtime_kwargs = {
            "n_ctx": n_ctx,
            "n_batch": n_batch,
            "n_gpu_layers": n_gpu_layers,
            "n_threads": n_threads,
            **kwargs,
        }

        # Performance tracking
        self._performance_metrics = {
            "load_time": 0,
            "generation_times": [],
            "timeout_count": 0,
            "error_count": 0,
            "total_requests": 0,
        }

        # Initialize runtime with error handling
        self.runtime = None
        self._initialize_runtime()

        # Find default model if none specified
        if not model_path:
            self._find_default_model()

    def _initialize_runtime(self):
        """Initialize runtime with better error handling and performance tracking."""
        start_time = time.time()
        try:
            self.runtime = LlamaCppRuntime.get_instance(
                model_path=self.model_path, **self.runtime_kwargs
            )
            load_time = time.time() - start_time
            self._performance_metrics["load_time"] = load_time
            logger.info(
                f"LlamaCppProvider initialized successfully in {load_time:.2f}s"
            )
        except Exception as e:
            load_time = time.time() - start_time
            self._performance_metrics["load_time"] = load_time
            self._performance_metrics["error_count"] += 1
            logger.error(
                f"Failed to initialize LlamaCppProvider in {load_time:.2f}s: {e}"
            )
            raise GenerationFailed(f"LlamaCpp initialization failed: {e}")

    def _find_default_model(self):
        """Resolve and load a reasonable default GGUF model with better performance."""
        start_time = time.time()

        allow_model_library = os.getenv(
            "AI_KAREN_ENABLE_MODEL_LIBRARY", ""
        ).lower() in {"1", "true", "yes", "on"}

        if allow_model_library:
            try:
                from ai_karen_engine.services.model_library_service import (
                    ModelLibraryService,
                )

                lib = ModelLibraryService()
                models = self._get_model_library_models(lib)
                local_candidates = [
                    m
                    for m in models
                    if m.provider == "llama-cpp"
                    and m.status == "local"
                    and m.local_path
                    and Path(m.local_path).exists()
                ]
                if local_candidates:
                    local_candidates.sort(
                        key=lambda m: (
                            Path(m.local_path).stat().st_size if m.local_path else 0
                        ),
                        reverse=True,
                    )
                    self.model_path = local_candidates[0].local_path  # type: ignore[assignment]
                    self._load_model_with_timeout(self.model_path)
                    load_time = time.time() - start_time
                    logger.info(
                        f"Loaded default model from Model Library in {load_time:.2f}s: {self.model_path}"
                    )
                    return
            except Exception as e:
                logger.debug(f"Model Library scan failed: {e}")

        # Scan models/llama-cpp for .gguf and choose the largest valid file
        try:
            gguf_dir = Path("models/llama-cpp")
            if gguf_dir.exists():
                candidates = [p for p in gguf_dir.glob("*.gguf") if p.is_file()]
                # Filter by basic validity (header check)
                valid = []
                for p in candidates:
                    try:
                        if p.stat().st_size < 50 * 1024 * 1024:
                            continue
                        with open(p, "rb") as f:
                            magic = f.read(4)
                        if magic == b"GGUF":
                            valid.append(p)
                    except Exception:
                        continue
                if valid:
                    valid.sort(key=lambda p: p.stat().st_size, reverse=True)
                    self.model_path = str(valid[0])
                    self._load_model_with_timeout(self.model_path)
                    load_time = time.time() - start_time
                    logger.info(
                        f"Loaded default model from directory in {load_time:.2f}s: {self.model_path}"
                    )
                    return
        except Exception as e:
            logger.debug(f"Directory scan failed: {e}")

        # Auto-download default model if allowed
        allow_download = os.getenv("KARI_AUTO_DOWNLOAD_LLM", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if allow_download:
            try:
                from ai_karen_engine.services.model_library_service import (
                    ModelLibraryService,
                )

                lib = ModelLibraryService()
                try:
                    from ai_karen_engine.config.config_manager import get_default_model

                    _dm = (
                        get_default_model("llamacpp")
                        or "Phi-3-mini-4k-instruct-q4.gguf"
                    )
                except Exception:
                    _dm = "Phi-3-mini-4k-instruct-q4.gguf"
                preferred = [_dm.replace(".gguf", "")]
                for model_id in preferred:
                    task = lib.download_model(model_id)
                    if not task:
                        continue
                    logger.info("Downloading %s ...", model_id)
                    start = time.time()
                    while True:
                        st = lib.get_download_status(task.task_id)
                        if st and st.status in ("completed", "failed", "cancelled"):
                            break
                        if time.time() - start > 300:  # 5 minutes timeout
                            logger.warning("Download timed out")
                            break
                        time.sleep(1.0)
                    if st and st.status == "completed":
                        lib._add_downloaded_model_to_registry(task)
                        target = Path("models/llama-cpp") / task.filename
                        if target.exists():
                            self.model_path = str(target)
                            self._load_model_with_timeout(self.model_path)
                            load_time = time.time() - start_time
                            logger.info(
                                f"Loaded downloaded model in {load_time:.2f}s: {self.model_path}"
                            )
                            return
                logger.error("Auto-download failed or no preferred models available")
            except Exception as e:
                logger.error(f"Auto-download encountered an error: {e}")

        # If we reach here, fail fast with a clear message
        raise GenerationFailed(
            "No valid local GGUF model found. Place a model under models/llama-cpp/ or set model_path explicitly."
        )

    def _load_model_with_timeout(self, model_path: str, timeout: int = 60):
        """Load model with timeout to prevent blocking."""
        try:
            # Use asyncio.wait_for to prevent blocking
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, self.runtime.load_model, model_path)
            asyncio.wait_for(future, timeout=timeout)
            logger.info(f"Successfully loaded model: {model_path}")
        except asyncio.TimeoutError:
            logger.error(f"Model loading timed out after {timeout}s: {model_path}")
            raise GenerationFailed(f"Model loading timed out: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            raise GenerationFailed(f"Failed to load model {model_path}: {e}")

    @staticmethod
    def _get_model_library_models(model_library: Any) -> List[Any]:
        """Prefer the fast model-library path to avoid chat-time cache rebuild stalls."""
        fast_getter = getattr(model_library, "get_available_models_fast", None)
        if callable(fast_getter):
            return list(fast_getter())
        return list(model_library.get_available_models())

    @property
    def last_usage(self) -> Dict[str, Any]:
        """Return the last generation usage from the runtime."""
        return getattr(self.runtime, "last_usage", {})

    async def generate_text_async(self, prompt: str, **kwargs) -> str:
        """Asynchronous text generation with better timeout handling."""
        start_time = time.time()
        self._performance_metrics["total_requests"] += 1

        try:
            # Validate prompt
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")

            # Extract and validate generation parameters
            max_tokens = kwargs.pop("max_tokens", kwargs.pop("num_predict", 256))
            if max_tokens <= 0:
                raise ValueError(f"max_tokens must be positive, got {max_tokens}")

            temperature = kwargs.pop("temperature", 0.7)
            if not 0 <= temperature <= 2:
                raise ValueError(
                    f"temperature must be between 0 and 2, got {temperature}"
                )

            top_p = kwargs.pop("top_p", 0.9)
            if not 0 <= top_p <= 1:
                raise ValueError(f"top_p must be between 0 and 1, got {top_p}")

            top_k = kwargs.pop("top_k", 40)
            if top_k <= 0:
                raise ValueError(f"top_k must be positive, got {top_k}")

            repeat_penalty = kwargs.pop("repeat_penalty", 1.1)
            if repeat_penalty <= 0:
                raise ValueError(
                    f"repeat_penalty must be positive, got {repeat_penalty}"
                )

            stop = kwargs.pop("stop", None)

            # Use asyncio.wait_for for better timeout handling
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.runtime.generate(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        repeat_penalty=repeat_penalty,
                        stop=stop,
                        stream=False,
                        **kwargs,
                    ),
                ),
                timeout=self.timeout,
            )

            # Validate result
            if not result or (isinstance(result, str) and not result.strip()):
                logger.error(f"Empty response generated for prompt: {prompt[:100]}...")
                raise GenerationFailed("Model returned empty response")

            # Update performance metrics
            elapsed = time.time() - start_time
            self._performance_metrics["generation_times"].append(elapsed)

            # Keep only last 100 generation times for performance tracking
            if len(self._performance_metrics["generation_times"]) > 100:
                self._performance_metrics["generation_times"] = (
                    self._performance_metrics["generation_times"][-100:]
                )

            record_llm_metric("generate_text", elapsed, True, "llama-cpp-optimized")
            logger.info(f"Generated text in {elapsed:.2f}s")
            return result

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            self._performance_metrics["timeout_count"] += 1
            self._performance_metrics["generation_times"].append(elapsed)
            logger.error(f"Generation timed out after {elapsed:.2f}s")
            record_llm_metric(
                "generate_text", elapsed, False, "llama-cpp-optimized", error="timeout"
            )
            raise GenerationFailed(f"Generation timed out after {elapsed:.2f}s")

        except ValueError as ve:
            elapsed = time.time() - start_time
            self._performance_metrics["error_count"] += 1
            record_llm_metric(
                "generate_text", elapsed, False, "llama-cpp-optimized", error=str(ve)
            )
            raise GenerationFailed(f"Invalid parameters: {ve}")

        except Exception as ex:
            elapsed = time.time() - start_time
            self._performance_metrics["error_count"] += 1
            logger.error(f"Generation failed after {elapsed:.2f}s: {ex}")
            record_llm_metric(
                "generate_text", elapsed, False, "llama-cpp-optimized", error=str(ex)
            )
            raise GenerationFailed(f"Generation failed: {ex}")

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Synchronous text generation wrapper."""
        try:
            # Use asyncio.run for synchronous calls
            return asyncio.run(self.generate_text_async(prompt, **kwargs))
        except Exception as ex:
            raise GenerationFailed(f"Generation failed: {ex}")

    async def stream_generate_async(self, prompt: str, **kwargs) -> Iterator[str]:
        """Asynchronous streaming text generation with better timeout handling."""
        start_time = time.time()
        self._performance_metrics["total_requests"] += 1

        try:
            # Validate prompt
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")

            # Extract generation parameters
            max_tokens = kwargs.pop("max_tokens", kwargs.pop("num_predict", 256))
            if max_tokens <= 0:
                raise ValueError(f"max_tokens must be positive, got {max_tokens}")

            temperature = kwargs.pop("temperature", 0.7)
            if not 0 <= temperature <= 2:
                raise ValueError(
                    f"temperature must be between 0 and 2, got {temperature}"
                )

            top_p = kwargs.pop("top_p", 0.9)
            if not 0 <= top_p <= 1:
                raise ValueError(f"top_p must be between 0 and 1, got {top_p}")

            top_k = kwargs.pop("top_k", 40)
            if top_k <= 0:
                raise ValueError(f"top_k must be positive, got {top_k}")

            repeat_penalty = kwargs.pop("repeat_penalty", 1.1)
            if repeat_penalty <= 0:
                raise ValueError(
                    f"repeat_penalty must be positive, got {repeat_penalty}"
                )

            stop = kwargs.pop("stop", None)

            # Create a streaming generator with timeout
            async def stream_generator():
                try:
                    # Use asyncio.wait_for for timeout handling
                    generation_result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: list(
                                self.runtime.generate(
                                    prompt=prompt,
                                    max_tokens=max_tokens,
                                    temperature=temperature,
                                    top_p=top_p,
                                    top_k=top_k,
                                    repeat_penalty=repeat_penalty,
                                    stop=stop,
                                    stream=True,
                                    **kwargs,
                                )
                            ),
                        ),
                        timeout=self.timeout,
                    )

                    for chunk in generation_result:
                        if chunk and chunk.strip():
                            yield chunk

                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    self._performance_metrics["timeout_count"] += 1
                    logger.error(f"Streaming generation timed out after {elapsed:.2f}s")
                    yield f"[ERROR: Generation timed out after {elapsed:.2f}s]"

                except Exception as ex:
                    elapsed = time.time() - start_time
                    self._performance_metrics["error_count"] += 1
                    logger.error(
                        f"Streaming generation failed after {elapsed:.2f}s: {ex}"
                    )
                    yield f"[ERROR: Generation failed: {ex}]"

            return stream_generator()

        except ValueError as ve:
            elapsed = time.time() - start_time
            self._performance_metrics["error_count"] += 1
            logger.error(f"Invalid parameters for streaming: {ve}")
            raise GenerationFailed(f"Invalid parameters for streaming: {ve}")

        except Exception as ex:
            elapsed = time.time() - start_time
            self._performance_metrics["error_count"] += 1
            logger.error(f"Streaming setup failed after {elapsed:.2f}s: {ex}")
            raise GenerationFailed(f"Streaming setup failed: {ex}")

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """Synchronous streaming text generation wrapper."""
        try:
            # Use asyncio.run for synchronous calls
            for chunk in asyncio.run(self.stream_generate_async(prompt, **kwargs)):
                yield chunk
        except Exception as ex:
            raise GenerationFailed(f"Streaming generation failed: {ex}")

    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Generate embeddings using LlamaCppRuntime."""
        start_time = time.time()

        try:
            if isinstance(text, str):
                embeddings = self.runtime.embed(text)
            else:
                # Handle list of texts
                embeddings = []
                for t in text:
                    embedding = self.runtime.embed(t)
                    embeddings.append(embedding)

            elapsed = time.time() - start_time
            record_llm_metric("embed", elapsed, True, "llama-cpp-optimized")
            return embeddings

        except Exception as ex:
            elapsed = time.time() - start_time
            record_llm_metric(
                "embed", elapsed, False, "llama-cpp-optimized", error=str(ex)
            )

            if "does not support embeddings" in str(ex):
                raise EmbeddingFailed(
                    "Current GGUF model does not support embeddings. "
                    "Please load an embedding-capable model."
                )
            else:
                raise EmbeddingFailed(f"LlamaCpp embedding failed: {ex}")

    def get_models(self) -> List[str]:
        """Get list of available GGUF models with enhanced scanning."""
        if getattr(self, "_scanning_models", False):
            return self._scan_local_models()

        self._scanning_models = True
        models = []

        try:
            # Try to get models from Model Library service
            try:
                from ai_karen_engine.services.model_library_service import (
                    ModelLibraryService,
                )

                model_library = ModelLibraryService()
                available_models = self._get_model_library_models(model_library)
            except Exception as lib_err:
                logger.debug(f"Inner Model Library access failed: {lib_err}")
                available_models = []

            # Filter for llama-cpp compatible models
            for model_info in available_models:
                if (
                    model_info.provider == "llama-cpp"
                    and model_info.status == "local"
                    and model_info.local_path
                ):
                    models.append(Path(model_info.local_path).name)

        except Exception as e:
            logger.warning(f"Failed to get models from Model Library: {e}")
        finally:
            self._scanning_models = False

        # Enhanced directory scan with validation
        scanned_models = self._scan_local_models()
        models.extend(scanned_models)

        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in models:
            if model not in seen:
                seen.add(model)
                unique_models.append(model)

        # Add currently loaded model if not in list
        if self.model_path:
            model_name = Path(self.model_path).name
            if model_name not in unique_models:
                unique_models.append(model_name)

        # Return predefined models as fallback if none found
        if not unique_models:
            logger.warning("No local GGUF models found, returning fallback list")
            try:
                from ai_karen_engine.config.config_manager import get_default_model

                _dm = get_default_model("llamacpp") or "Phi-3-mini-4k-instruct-q4.gguf"
            except Exception:
                _dm = "Phi-3-mini-4k-instruct-q4.gguf"
            return [
                _dm,
                "llama-2-7b-chat.Q4_K_M.gguf",
                "llama-2-13b-chat.Q4_K_M.gguf",
                "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
            ]

        return sorted(unique_models)

    def _scan_local_models(self) -> List[str]:
        """Scan local directories for GGUF models with validation."""
        models = []

        # Scan specific llama-cpp directory
        scan_dirs = [
            Path("models/llama-cpp"),
        ]

        for models_dir in scan_dirs:
            if not models_dir.exists():
                continue

            logger.debug(f"Scanning directory: {models_dir}")

            # Look for GGUF files
            for model_file in models_dir.rglob("*.gguf"):
                if self._validate_gguf_file(model_file):
                    models.append(model_file.name)
                    logger.debug(f"Found valid GGUF model: {model_file}")

        return models

    def _validate_gguf_file(self, file_path: Path) -> bool:
        """Validate that a file is a proper GGUF model."""
        try:
            # Check file size (should be at least 1MB for a valid model)
            if file_path.stat().st_size < 1024 * 1024:
                return False

            # Check GGUF magic header
            with open(file_path, "rb") as f:
                magic = f.read(4)
                if magic != b"GGUF":
                    return False

            return True

        except Exception as e:
            logger.debug(f"GGUF validation failed for {file_path}: {e}")
            return False

    def load_model(self, model_path: str) -> bool:
        """Load a specific GGUF model with timeout."""
        try:
            self._load_model_with_timeout(model_path)
            self.model_path = model_path
            return True
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata with performance metrics."""
        info = {
            "name": "llama-cpp-optimized",
            "model_path": self.model_path,
            "available_models": self.get_models(),
            "supports_streaming": True,
            "supports_embeddings": True,
            "timeout": self.timeout,
            "performance_metrics": self._performance_metrics,
            "runtime_info": self.runtime.get_model_info()
            if self.runtime and self.runtime.is_loaded()
            else None,
        }

        # Calculate performance statistics
        if self._performance_metrics["generation_times"]:
            avg_time = sum(self._performance_metrics["generation_times"]) / len(
                self._performance_metrics["generation_times"]
            )
            info["performance_stats"] = {
                "average_generation_time": avg_time,
                "total_requests": self._performance_metrics["total_requests"],
                "timeout_count": self._performance_metrics["timeout_count"],
                "error_count": self._performance_metrics["error_count"],
                "success_rate": (
                    self._performance_metrics["total_requests"]
                    - self._performance_metrics["timeout_count"]
                    - self._performance_metrics["error_count"]
                )
                / self._performance_metrics["total_requests"]
                if self._performance_metrics["total_requests"] > 0
                else 0,
            }

        return info

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check with performance monitoring."""
        try:
            # Get basic runtime health
            health_result = self.runtime.health_check()
            health_result["provider"] = "llama-cpp-optimized"
            health_result["performance_metrics"] = self._performance_metrics.copy()

            # Add performance analysis
            if self._performance_metrics["generation_times"]:
                times = self._performance_metrics["generation_times"]
                health_result["performance_analysis"] = {
                    "average_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "recent_performance": times[-10:],  # Last 10 generations
                }

                # Check for performance issues
                if any(t > self.timeout for t in times[-5:]):  # Recent timeouts
                    health_result["warnings"] = health_result.get("warnings", [])
                    health_result["warnings"].append(
                        "Recent generation times approaching or exceeding timeout"
                    )

            return health_result

        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": str(ex),
                "provider": "llama-cpp-optimized",
                "performance_metrics": self._performance_metrics,
            }

    def ping(self) -> bool:
        """Check if provider is responsive."""
        try:
            return self.runtime.is_loaded()
        except Exception:
            return False

    def available_models(self) -> List[str]:
        """Get available models."""
        try:
            return self.get_models()
        except Exception:
            return []
