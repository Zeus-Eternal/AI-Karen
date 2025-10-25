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
        """Get list of available GGUF models with enhanced scanning."""
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
            return [
                "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                "llama-2-7b-chat.Q4_K_M.gguf",
                "llama-2-13b-chat.Q4_K_M.gguf",
                "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
            ]
        
        return sorted(unique_models)

    def _scan_local_models(self) -> List[str]:
        """Scan local directories for GGUF models with validation."""
        models = []
        
        # Scan multiple potential directories
        scan_dirs = [
            Path("models/llama-cpp"),
            Path("models"),
            Path("./models"),
            Path("../models"),
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
            
            # Also look for safetensors files (for transformers compatibility)
            for model_file in models_dir.rglob("*.safetensors"):
                if self._validate_safetensors_file(model_file):
                    models.append(model_file.name)
                    logger.debug(f"Found valid safetensors model: {model_file}")
        
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

    def _validate_safetensors_file(self, file_path: Path) -> bool:
        """Validate that a file is a proper safetensors model."""
        try:
            # Check file size (should be at least 1MB for a valid model)
            if file_path.stat().st_size < 1024 * 1024:
                return False
            
            # Basic safetensors validation - check for JSON header
            with open(file_path, "rb") as f:
                # Read first 8 bytes to get header length
                header_size_bytes = f.read(8)
                if len(header_size_bytes) != 8:
                    return False
                
                header_size = int.from_bytes(header_size_bytes, byteorder='little')
                if header_size > 100 * 1024 * 1024:  # Sanity check: header shouldn't be > 100MB
                    return False
                
                # Try to read and parse the JSON header
                header_bytes = f.read(header_size)
                if len(header_bytes) != header_size:
                    return False
                
                import json
                header = json.loads(header_bytes.decode('utf-8'))
                
                # Check if it looks like a model (has tensors)
                if not isinstance(header, dict) or not header:
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Safetensors validation failed for {file_path}: {e}")
            return False

    def extract_model_metadata(self, model_path: str) -> Dict[str, Any]:
        """Extract metadata from a GGUF or safetensors model file."""
        file_path = Path(model_path)
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix.lower(),
            "capabilities": [],
            "parameters": {}
        }
        
        try:
            if file_path.suffix.lower() == ".gguf":
                metadata.update(self._extract_gguf_metadata(file_path))
            elif file_path.suffix.lower() == ".safetensors":
                metadata.update(self._extract_safetensors_metadata(file_path))
            
            # Infer capabilities based on metadata
            metadata["capabilities"] = self._infer_model_capabilities(metadata)
            
        except Exception as e:
            metadata["error"] = f"Metadata extraction failed: {e}"
            logger.warning(f"Failed to extract metadata from {model_path}: {e}")
        
        return metadata

    def _extract_gguf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from GGUF file."""
        metadata = {}
        
        try:
            # Try to use llama-cpp-python to get metadata if available
            try:
                from llama_cpp import Llama
                
                # Create a temporary instance to get metadata
                temp_llama = Llama(
                    model_path=str(file_path),
                    n_ctx=1,  # Minimal context
                    verbose=False
                )
                
                # Get model info
                if hasattr(temp_llama, 'metadata'):
                    metadata["model_metadata"] = temp_llama.metadata
                
                # Clean up
                del temp_llama
                
            except Exception as e:
                logger.debug(f"Could not extract GGUF metadata with llama-cpp: {e}")
            
            # Basic file analysis
            with open(file_path, "rb") as f:
                # Skip magic header
                f.seek(4)
                
                # Try to read version and other basic info
                version_bytes = f.read(4)
                if len(version_bytes) == 4:
                    version = int.from_bytes(version_bytes, byteorder='little')
                    metadata["gguf_version"] = version
            
            # Infer model type from filename
            filename_lower = file_path.name.lower()
            if "chat" in filename_lower or "instruct" in filename_lower:
                metadata["model_type"] = "chat"
            elif "code" in filename_lower:
                metadata["model_type"] = "code"
            elif "embed" in filename_lower:
                metadata["model_type"] = "embedding"
            else:
                metadata["model_type"] = "base"
            
            # Extract quantization info from filename
            if "q4" in filename_lower:
                metadata["quantization"] = "Q4"
            elif "q8" in filename_lower:
                metadata["quantization"] = "Q8"
            elif "f16" in filename_lower:
                metadata["quantization"] = "F16"
            elif "f32" in filename_lower:
                metadata["quantization"] = "F32"
            
        except Exception as e:
            logger.debug(f"GGUF metadata extraction error: {e}")
        
        return metadata

    def _extract_safetensors_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from safetensors file."""
        metadata = {}
        
        try:
            with open(file_path, "rb") as f:
                # Read header
                header_size_bytes = f.read(8)
                header_size = int.from_bytes(header_size_bytes, byteorder='little')
                header_bytes = f.read(header_size)
                
                import json
                header = json.loads(header_bytes.decode('utf-8'))
                
                # Extract tensor information
                tensor_count = len([k for k in header.keys() if k != "__metadata__"])
                metadata["tensor_count"] = tensor_count
                
                # Extract model metadata if available
                if "__metadata__" in header:
                    metadata["model_metadata"] = header["__metadata__"]
                
                # Infer model type from metadata or filename
                filename_lower = file_path.name.lower()
                if "chat" in filename_lower or "instruct" in filename_lower:
                    metadata["model_type"] = "chat"
                elif "code" in filename_lower:
                    metadata["model_type"] = "code"
                elif "embed" in filename_lower:
                    metadata["model_type"] = "embedding"
                else:
                    metadata["model_type"] = "base"
            
        except Exception as e:
            logger.debug(f"Safetensors metadata extraction error: {e}")
        
        return metadata

    def _infer_model_capabilities(self, metadata: Dict[str, Any]) -> List[str]:
        """Infer model capabilities from metadata."""
        capabilities = []
        
        model_type = metadata.get("model_type", "base")
        
        # Basic capabilities
        capabilities.append("text-generation")
        
        # Type-specific capabilities
        if model_type == "chat":
            capabilities.extend(["chat", "instruction-following"])
        elif model_type == "code":
            capabilities.extend(["code-generation", "code-completion"])
        elif model_type == "embedding":
            capabilities.append("embeddings")
        
        # File format capabilities
        if metadata.get("file_type") == ".gguf":
            capabilities.extend(["local-inference", "cpu-optimized"])
            
            # Quantization-specific capabilities
            quantization = metadata.get("quantization", "")
            if quantization in ["Q4", "Q8"]:
                capabilities.append("memory-efficient")
        
        return capabilities
    
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
        """Perform comprehensive health check with enhanced model scanning."""
        try:
            # Get basic runtime health
            health_result = self.runtime.health_check()
            health_result["provider"] = "llama-cpp"
            
            # Enhanced model availability check
            try:
                available_models = self.get_models()
                scanned_models = self._scan_local_models()
                
                health_result["model_scanning"] = {
                    "status": "success",
                    "total_models_found": len(available_models),
                    "scanned_models_count": len(scanned_models),
                    "sample_models": available_models[:5]  # First 5 models
                }
                
                # Validate a few models
                validated_models = []
                for model_name in available_models[:3]:  # Check first 3 models
                    model_path = self._find_model_path(model_name)
                    if model_path and self._validate_gguf_file(Path(model_path)):
                        validated_models.append(model_name)
                
                health_result["model_validation"] = {
                    "validated_models": validated_models,
                    "validation_success_rate": len(validated_models) / min(len(available_models), 3) if available_models else 0
                }
                
            except Exception as e:
                health_result["model_scanning"] = {
                    "status": "failed",
                    "error": str(e)
                }
                health_result["warnings"] = health_result.get("warnings", [])
                health_result["warnings"].append("Model scanning failed")
            
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
            
            # Add current model metadata if available
            if self.model_path:
                try:
                    current_model_metadata = self.extract_model_metadata(self.model_path)
                    health_result["current_model"] = {
                        "path": self.model_path,
                        "metadata": current_model_metadata,
                        "loaded": self.runtime.is_loaded()
                    }
                except Exception as e:
                    health_result["current_model"] = {
                        "path": self.model_path,
                        "metadata_error": str(e),
                        "loaded": self.runtime.is_loaded()
                    }
            
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

    def _find_model_path(self, model_name: str) -> Optional[str]:
        """Find the full path for a model by name."""
        # Check common directories
        search_dirs = [
            Path("models/llama-cpp"),
            Path("models"),
            Path("./models"),
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                model_path = search_dir / model_name
                if model_path.exists():
                    return str(model_path)
        
        # Check Model Library
        try:
            from ai_karen_engine.services.model_library_service import ModelLibraryService
            model_library = ModelLibraryService()
            available_models = model_library.get_available_models()
            
            for model_info in available_models:
                if (model_info.provider == "llama-cpp" and 
                    model_info.local_path and
                    Path(model_info.local_path).name == model_name):
                    return model_info.local_path
                    
        except Exception:
            pass
        
        return None

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

    def create_model_fallback_chain(self, preferred_capabilities: List[str] = None) -> List[str]:
        """Create a fallback chain of models based on capabilities and availability."""
        available_models = self.get_models()
        
        if not available_models:
            return []
        
        # If no specific capabilities requested, return all models sorted by size (larger first)
        if not preferred_capabilities:
            return self._sort_models_by_preference(available_models)
        
        # Group models by capabilities
        capability_groups = {
            "chat": [],
            "code": [],
            "embedding": [],
            "base": []
        }
        
        for model_name in available_models:
            model_path = self._find_model_path(model_name)
            if model_path:
                metadata = self.extract_model_metadata(model_path)
                model_type = metadata.get("model_type", "base")
                capability_groups[model_type].append(model_name)
        
        # Build fallback chain based on preferred capabilities
        fallback_chain = []
        
        for capability in preferred_capabilities:
            if capability in ["chat", "instruction-following"] and capability_groups["chat"]:
                fallback_chain.extend(self._sort_models_by_preference(capability_groups["chat"]))
            elif capability in ["code-generation", "code-completion"] and capability_groups["code"]:
                fallback_chain.extend(self._sort_models_by_preference(capability_groups["code"]))
            elif capability == "embeddings" and capability_groups["embedding"]:
                fallback_chain.extend(self._sort_models_by_preference(capability_groups["embedding"]))
        
        # Add base models as final fallback
        fallback_chain.extend(self._sort_models_by_preference(capability_groups["base"]))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_chain = []
        for model in fallback_chain:
            if model not in seen:
                seen.add(model)
                unique_chain.append(model)
        
        return unique_chain

    def _sort_models_by_preference(self, models: List[str]) -> List[str]:
        """Sort models by preference (size, quantization, etc.)."""
        def model_score(model_name: str) -> tuple:
            """Calculate preference score for a model."""
            name_lower = model_name.lower()
            
            # Size preference (larger models first, but not too large)
            size_score = 0
            if "7b" in name_lower:
                size_score = 100
            elif "13b" in name_lower:
                size_score = 90
            elif "3b" in name_lower:
                size_score = 80
            elif "1b" in name_lower:
                size_score = 70
            elif "70b" in name_lower:
                size_score = 60  # Too large for most systems
            
            # Quantization preference (Q4 is good balance)
            quant_score = 0
            if "q4" in name_lower:
                quant_score = 50
            elif "q8" in name_lower:
                quant_score = 40
            elif "f16" in name_lower:
                quant_score = 30
            elif "q2" in name_lower:
                quant_score = 20
            
            # Model family preference
            family_score = 0
            if "llama" in name_lower:
                family_score = 30
            elif "mistral" in name_lower:
                family_score = 25
            elif "tinyllama" in name_lower:
                family_score = 20
            
            return (size_score + quant_score + family_score, model_name)
        
        return [model for _, model in sorted([(model_score(m), m) for m in models], reverse=True)]
