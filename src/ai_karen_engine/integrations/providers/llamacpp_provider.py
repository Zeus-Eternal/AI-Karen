"""
LLaMA-CPP Provider Implementation

Wraps the LlamaCppRuntime to provide a consistent provider interface
for local GGUF model execution using llama-cpp-python.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ai_karen_engine.integrations.llm_utils import LLMProviderBase, GenerationFailed, EmbeddingFailed, record_llm_metric
from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime

logger = logging.getLogger("kari.llamacpp_provider")


class LlamaCppProvider(LLMProviderBase):
    """LLaMA-CPP provider using the existing LlamaCppRuntime."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = 2048,
        n_batch: int = 512,
        n_gpu_layers: int = 0,
        n_threads: Optional[int] = None,
        **kwargs
    ):
        """Initialize LLaMA-CPP provider."""
        self.model_path = model_path
        self.runtime_kwargs = {
            "n_ctx": n_ctx,
            "n_batch": n_batch,
            "n_gpu_layers": n_gpu_layers,
            "n_threads": n_threads,
            **kwargs
        }
        
        # Initialize runtime
        try:
            self.runtime = LlamaCppRuntime(
                model_path=model_path,
                **self.runtime_kwargs
            )
            logger.info("LlamaCppProvider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LlamaCppProvider: {e}")
            raise GenerationFailed(f"LlamaCpp initialization failed: {e}")
        
        # Find default model if none specified
        if not model_path:
            self._find_default_model()  
  
    def _find_default_model(self):
        """Resolve and load a reasonable default GGUF model dynamically.

        Preference order:
          1) Any local llama-cpp model from Model Library registry (validated path)
          2) Largest valid .gguf under models/llama-cpp
          3) Auto-download a TinyLlama predefined model (if allowed), then load
        """
        allow_model_library = (
            os.getenv("AI_KAREN_ENABLE_MODEL_LIBRARY", "")
            .lower()
            in {"1", "true", "yes", "on"}
        )
        if allow_model_library:
            try:
                from ai_karen_engine.services.model_library_service import ModelLibraryService

                lib = ModelLibraryService()
                models = lib.get_available_models()
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
                    self.runtime.load_model(self.model_path)
                    logger.info(
                        "Loaded default model from Model Library: %s", self.model_path
                    )
                    return
            except Exception as e:
                logger.debug("Model Library scan failed: %s", e)

        # 2) Scan models/llama-cpp for .gguf and choose the largest valid file
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
                    self.runtime.load_model(self.model_path)
                    logger.info(f"Loaded default model from directory: {self.model_path}")
                    return
        except Exception as e:
            logger.debug(f"Directory scan failed: {e}")

        # 3) Auto-download TinyLlama if allowed
        allow_download = (
            os.getenv("KARI_AUTO_DOWNLOAD_LLM", "false")
            .lower()
            in {"1", "true", "yes", "on"}
        )
        if allow_download and allow_model_library:
            try:
                from ai_karen_engine.services.model_library_service import ModelLibraryService

                lib = ModelLibraryService()
                preferred = ["tinyllama-1.1b-chat-q4", "tinyllama-1.1b-instruct-q4"]
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
                        if time.time() - start > 600:  # 10 minutes
                            logger.warning("Download timed out")
                            break
                        time.sleep(1.0)
                    if st and st.status == "completed":
                        lib._add_downloaded_model_to_registry(task)
                        target = Path("models/llama-cpp") / task.filename
                        if target.exists():
                            self.model_path = str(target)
                            self.runtime.load_model(self.model_path)
                            logger.info("Loaded downloaded model: %s", self.model_path)
                            return
                logger.error("Auto-download failed or no preferred models available")
            except Exception as e:
                logger.error("Auto-download encountered an error: %s", e)

        # If we reach here, fail fast with a clear message
        raise GenerationFailed(
            "No valid local GGUF model found. Place a model under models/llama-cpp/ or set model_path explicitly."
        )
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using LlamaCppRuntime."""
        t0 = time.time()
        
        try:
            # Extract generation parameters
            max_tokens = kwargs.pop("max_tokens", kwargs.pop("num_predict", 256))
            temperature = kwargs.pop("temperature", 0.7)
            top_p = kwargs.pop("top_p", 0.9)
            top_k = kwargs.pop("top_k", 40)
            repeat_penalty = kwargs.pop("repeat_penalty", 1.1)
            stop = kwargs.pop("stop", None)
            
            # Generate text
            result = self.runtime.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop,
                stream=False,
                **kwargs
            )
            
            record_llm_metric("generate_text", time.time() - t0, True, "llama-cpp")
            return result
            
        except Exception as ex:
            record_llm_metric(
                "generate_text", time.time() - t0, False, "llama-cpp", error=str(ex)
            )
            
            # Provide specific error messages
            if "No model loaded" in str(ex):
                raise GenerationFailed(
                    "No GGUF model loaded. Please load a model first or place a model in models/llama-cpp/"
                )
            else:
                raise GenerationFailed(f"LlamaCpp generation failed: {ex}")
    
    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """Generate text with streaming support."""
        try:
            # Extract generation parameters
            max_tokens = kwargs.pop("max_tokens", kwargs.pop("num_predict", 256))
            temperature = kwargs.pop("temperature", 0.7)
            top_p = kwargs.pop("top_p", 0.9)
            top_k = kwargs.pop("top_k", 40)
            repeat_penalty = kwargs.pop("repeat_penalty", 1.1)
            stop = kwargs.pop("stop", None)
            
            # Generate streaming text
            for chunk in self.runtime.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop,
                stream=True,
                **kwargs
            ):
                yield chunk
                
        except Exception as ex:
            if "No model loaded" in str(ex):
                raise GenerationFailed(
                    "No GGUF model loaded. Please load a model first or place a model in models/llama-cpp/"
                )
            else:
                raise GenerationFailed(f"LlamaCpp streaming failed: {ex}")
    
    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Generate embeddings using LlamaCppRuntime."""
        t0 = time.time()
        
        try:
            if isinstance(text, str):
                embeddings = self.runtime.embed(text)
            else:
                # Handle list of texts
                embeddings = []
                for t in text:
                    embedding = self.runtime.embed(t)
                    embeddings.append(embedding)
            
            record_llm_metric("embed", time.time() - t0, True, "llama-cpp")
            return embeddings
            
        except Exception as ex:
            record_llm_metric("embed", time.time() - t0, False, "llama-cpp", error=str(ex))
            
            if "does not support embeddings" in str(ex):
                raise EmbeddingFailed(
                    "Current GGUF model does not support embeddings. "
                    "Please load an embedding-capable model."
                )
            else:
                raise EmbeddingFailed(f"LlamaCpp embedding failed: {ex}")
    
    def get_models(self) -> List[str]:
        """Get list of available GGUF models from Model Library registry."""
        models = []
        
        try:
            # Try to get models from Model Library service
            from ai_karen_engine.services.model_library_service import ModelLibraryService
            model_library = ModelLibraryService()
            available_models = model_library.get_available_models()
            
            # Filter for llama-cpp compatible models
            for model_info in available_models:
                if (model_info.provider == "llama-cpp" and 
                    model_info.status == "local" and 
                    model_info.local_path):
                    models.append(Path(model_info.local_path).name)
            
        except Exception as e:
            logger.warning(f"Failed to get models from Model Library: {e}")
        
        # Fallback to directory scan if Model Library unavailable
        if not models:
            models_dir = Path("models/llama-cpp")
            if models_dir.exists():
                for model_file in models_dir.glob("*.gguf"):
                    models.append(model_file.name)
        
        # Add currently loaded model if not in list
        if self.model_path:
            model_name = Path(self.model_path).name
            if model_name not in models:
                models.append(model_name)
        
        # Return predefined models as fallback if none found
        if not models:
            return [
                "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                "llama-2-7b-chat.Q4_K_M.gguf",
                "llama-2-13b-chat.Q4_K_M.gguf",
                "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
            ]
        
        return sorted(models)
    
    def load_model(self, model_path: str) -> bool:
        """Load a specific GGUF model."""
        try:
            success = self.runtime.load_model(model_path)
            if success:
                self.model_path = model_path
                logger.info(f"Successfully loaded model: {model_path}")
            return success
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            return False
    
    def load_model_by_id(self, model_id: str) -> bool:
        """Load a model by its Model Library ID."""
        try:
            from ai_karen_engine.services.model_library_service import ModelLibraryService
            model_library = ModelLibraryService()
            model_info = model_library.get_model_info(model_id)
            
            if not model_info:
                logger.error(f"Model {model_id} not found in Model Library")
                return False
            
            if model_info.provider != "llama-cpp":
                logger.error(f"Model {model_id} is not compatible with LlamaCpp provider")
                return False
            
            if model_info.status != "local" or not model_info.local_path:
                logger.error(f"Model {model_id} is not available locally")
                return False
            
            if not Path(model_info.local_path).exists():
                logger.error(f"Model file not found: {model_info.local_path}")
                return False
            
            return self.load_model(model_info.local_path)
            
        except Exception as e:
            logger.error(f"Failed to load model by ID {model_id}: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata with Model Library integration."""
        info = {
            "name": "llama-cpp",
            "model_path": self.model_path,
            "available_models": self.get_models(),
            "supports_streaming": True,
            "supports_embeddings": True,
            "runtime_info": self.runtime.get_model_info() if self.runtime.is_loaded() else None,
            "context_length": self.runtime_kwargs.get("n_ctx", 2048),
            "gpu_layers": self.runtime_kwargs.get("n_gpu_layers", 0),
            "model_library_integration": True
        }
        
        # Add current model info from Model Library if available
        try:
            from ai_karen_engine.services.model_library_service import ModelLibraryService
            model_library = ModelLibraryService()
            available_models = model_library.get_available_models()
            
            # Find current model in Model Library
            current_model_info = None
            if self.model_path:
                for model_info in available_models:
                    if (model_info.provider == "llama-cpp" and 
                        model_info.local_path == self.model_path):
                        current_model_info = model_info
                        break
            
            if current_model_info:
                info["current_model_info"] = {
                    "id": current_model_info.id,
                    "name": current_model_info.name,
                    "size": current_model_info.size,
                    "capabilities": current_model_info.capabilities,
                    "metadata": current_model_info.metadata
                }
            
            # Add Model Library statistics
            local_models = [m for m in available_models if m.provider == "llama-cpp" and m.status == "local"]
            available_for_download = [m for m in available_models if m.provider == "llama-cpp" and m.status == "available"]
            
            info["model_library_stats"] = {
                "local_models": len(local_models),
                "available_for_download": len(available_for_download),
                "total_models": len([m for m in available_models if m.provider == "llama-cpp"])
            }
            
        except Exception as e:
            logger.warning(f"Failed to get Model Library info: {e}")
            info["model_library_integration"] = False
        
        return info
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check using runtime with Model Library integration."""
        try:
            # Get basic runtime health
            health_result = self.runtime.health_check()
            
            # Add Model Library availability check
            try:
                from ai_karen_engine.services.model_library_service import ModelLibraryService
                model_library = ModelLibraryService()
                available_models = model_library.get_available_models()
                
                local_models = [m for m in available_models if m.provider == "llama-cpp" and m.status == "local"]
                
                health_result["model_library"] = {
                    "available": True,
                    "local_models_count": len(local_models),
                    "models_available": len(local_models) > 0
                }
                
                # If no models available, mark as warning
                if len(local_models) == 0:
                    health_result["warnings"] = health_result.get("warnings", [])
                    health_result["warnings"].append("No local GGUF models available in Model Library")
                
            except Exception as e:
                health_result["model_library"] = {
                    "available": False,
                    "error": str(e)
                }
                health_result["warnings"] = health_result.get("warnings", [])
                health_result["warnings"].append(f"Model Library unavailable: {e}")
            
            return health_result
            
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": str(ex),
                "provider": "llama-cpp",
                "model_library": {
                    "available": False,
                    "error": "Provider health check failed"
                }
            }

    # Lightweight status helpers
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
