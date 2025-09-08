"""
llama.cpp Runtime Implementation

This module provides the LlamaCppRuntime class for executing GGUF models using llama-cpp-python.
It serves as the default always-on runtime for local model execution with privacy and efficiency.
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

logger = logging.getLogger(__name__)

try:
    from llama_cpp import Llama, LlamaGrammar
    # Patch noisy __del__ AttributeError in some llama-cpp-python versions
    try:  # defensive: best-effort monkey patch to suppress sampler AttributeError
        from llama_cpp import _internals as _ll_internals  # type: ignore
        _orig_del = getattr(getattr(_ll_internals, "LlamaModel", object), "__del__", None)
        if callable(_orig_del):
            def _safe_del(self):  # type: ignore
                try:
                    return _orig_del(self)
                except AttributeError:
                    # Older builds may not set attributes on failed init; ignore cleanup errors
                    return None
            try:
                _ll_internals.LlamaModel.__del__ = _safe_del  # type: ignore
            except Exception:
                pass
    except Exception:
        pass
    LLAMACPP_AVAILABLE = True
except ImportError:
    logger.warning("llama-cpp-python not available. LlamaCppRuntime will be disabled.")
    LLAMACPP_AVAILABLE = False
    Llama = None
    LlamaGrammar = None


class LlamaCppRuntime:
    """
    Runtime for executing GGUF models using llama.cpp.
    
    This runtime is designed to be the default backbone for local model execution,
    providing privacy-focused, resource-efficient inference for GGUF models.
    
    Key Features:
    - GGUF model support with automatic format detection
    - Configurable context length, batch size, and GPU layers
    - Memory-efficient KV cache management
    - Thread-safe model loading and inference
    - Health monitoring and resource tracking
    - Streaming and non-streaming inference modes
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = 2048,
        n_batch: int = 512,
        n_gpu_layers: int = 0,
        n_threads: Optional[int] = None,
        use_mmap: bool = True,
        use_mlock: bool = False,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize llama.cpp runtime.
        
        Args:
            model_path: Path to GGUF model file
            n_ctx: Context length (default: 2048)
            n_batch: Batch size for processing (default: 512)
            n_gpu_layers: Number of layers to offload to GPU (default: 0)
            n_threads: Number of CPU threads (default: auto-detect)
            use_mmap: Use memory mapping for model loading (default: True)
            use_mlock: Lock model in memory (default: False)
            verbose: Enable verbose logging (default: False)
            **kwargs: Additional llama.cpp parameters
        """
        if not LLAMACPP_AVAILABLE:
            raise RuntimeError("llama-cpp-python is not available. Please install it to use LlamaCppRuntime.")
        
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.n_gpu_layers = n_gpu_layers
        # Allow env overrides for performance tuning
        try:
            env_threads = int(os.getenv("LLAMA_THREADS", "0"))
        except ValueError:
            env_threads = 0
        self.n_threads = n_threads or (env_threads if env_threads > 0 else (os.cpu_count() or 1))
        self.use_mmap = use_mmap
        # Enable mlock via env if requested
        env_mlock = os.getenv("LLAMA_MLOCK", "false").lower() in ("1", "true", "yes")
        self.use_mlock = use_mlock or env_mlock
        self.verbose = verbose
        self.kwargs = kwargs
        
        self._model: Optional[Llama] = None
        self._lock = threading.RLock()
        self._loaded = False
        self._load_time: Optional[float] = None
        self._memory_usage: Optional[int] = None
        
        # Load model if path provided
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str, **override_kwargs) -> bool:
        """
        Load a GGUF model file.
        
        Args:
            model_path: Path to GGUF model file
            **override_kwargs: Override initialization parameters
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        with self._lock:
            try:
                start_time = time.time()
                
                # Validate model file early for speed & correctness
                p = Path(model_path)
                if not p.exists() or not p.is_file():
                    logger.error(f"Model file not found: {model_path}")
                    return False
                if p.suffix.lower() != ".gguf":
                    logger.error(f"Invalid model format (expected .gguf): {model_path}")
                    return False
                size = p.stat().st_size
                if size < 50 * 1024 * 1024:
                    logger.error(f"Model file too small to be valid GGUF: {model_path}")
                    return False
                try:
                    with open(p, "rb") as f:
                        magic = f.read(4)
                    if magic != b"GGUF":
                        logger.error(f"Model file header invalid (no GGUF magic): {model_path}")
                        return False
                except Exception as e:
                    logger.error(f"Failed to read model header: {e}")
                    return False
                
                if not model_path.lower().endswith('.gguf'):
                    logger.warning(f"Model file may not be GGUF format: {model_path}")
                
                # Merge override parameters
                params = {
                    "model_path": model_path,
                    "n_ctx": self.n_ctx,
                    "n_batch": self.n_batch,
                    "n_gpu_layers": self.n_gpu_layers,
                    "n_threads": self.n_threads,
                    "use_mmap": self.use_mmap,
                    "use_mlock": self.use_mlock,
                    "verbose": self.verbose,
                    **self.kwargs,
                    **override_kwargs
                }
                
                logger.info(f"Loading GGUF model: {model_path}")
                logger.debug(f"llama.cpp parameters: {params}")
                
                # Create llama.cpp instance
                self._model = Llama(**params)
                
                self.model_path = model_path
                self._loaded = True
                self._load_time = time.time() - start_time
                
                # Estimate memory usage (rough approximation)
                model_size = Path(model_path).stat().st_size
                self._memory_usage = model_size + (self.n_ctx * 4 * 1024)  # Context memory
                
                logger.info(f"Model loaded successfully in {self._load_time:.2f}s")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model {model_path}: {e}")
                # Attempt automatic recovery for known TinyLlama fallback model
                try:
                    filename = Path(model_path).name
                    auto_fix = os.getenv("KARI_AUTO_FIX_GGUF", "1").lower() in {"1", "true", "yes"}
                    if auto_fix and "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf" in filename:
                        logger.warning("Attempting to re-download TinyLlama GGUF due to load failure...")
                        # Move corrupt file aside first
                        try:
                            p = Path(model_path)
                            if p.exists():
                                corrupt_path = p.with_suffix(p.suffix + ".corrupt")
                                try:
                                    corrupt_path.unlink(missing_ok=True)  # type: ignore[arg-type]
                                except Exception:
                                    pass
                                p.rename(corrupt_path)
                                logger.warning(f"Renamed suspected corrupt file to {corrupt_path}")
                        except Exception as mv_err:
                            logger.debug(f"Could not move corrupt file aside: {mv_err}")

                        # Try huggingface_hub first (force download)
                        downloaded = False
                        try:
                            from huggingface_hub import hf_hub_download  # type: ignore
                            target_dir = str(Path(model_path).parent)
                            token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
                            hf_hub_download(
                                repo_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF",
                                filename="tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                                local_dir=target_dir,
                                local_dir_use_symlinks=False,
                                force_download=True,
                                token=token,
                            )
                            downloaded = True
                            logger.info("Re-download via huggingface_hub complete")
                        except Exception as dl_err:
                            logger.warning(f"huggingface_hub download failed: {dl_err}")

                        # Fallback to direct HTTP download if needed
                        if not downloaded:
                            try:
                                import requests  # type: ignore
                                url = (
                                    "https://huggingface.co/"
                                    "TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/"
                                    "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf?download=1"
                                )
                                tmp_path = str(Path(model_path).with_suffix(".tmp"))
                                with requests.get(url, stream=True, timeout=120) as r:
                                    r.raise_for_status()
                                    with open(tmp_path, "wb") as f:
                                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                                            if chunk:
                                                f.write(chunk)
                                # Basic validation: check magic and size
                                ok = False
                                try:
                                    size = Path(tmp_path).stat().st_size
                                    if size > 100 * 1024 * 1024:  # >100MB
                                        with open(tmp_path, "rb") as f:
                                            magic = f.read(4)
                                        ok = magic == b"GGUF"
                                except Exception:
                                    ok = False
                                if ok:
                                    Path(tmp_path).replace(model_path)
                                    downloaded = True
                                    logger.info("Re-download via direct URL complete")
                                else:
                                    try:
                                        Path(tmp_path).unlink(missing_ok=True)  # type: ignore[arg-type]
                                    except Exception:
                                        pass
                                    logger.error("Direct download failed validation; keeping no file")
                            except Exception as http_err:
                                logger.error(f"Direct download failed: {http_err}")

                        if downloaded:
                            logger.info("Retrying model load after re-download...")
                            # Retry once
                            self._model = Llama(**params)
                            self.model_path = model_path
                            self._loaded = True
                            self._load_time = time.time() - start_time
                            model_size = Path(model_path).stat().st_size
                            self._memory_usage = model_size + (self.n_ctx * 4 * 1024)
                            logger.info(f"Model loaded successfully after re-download in {self._load_time:.2f}s")
                            return True
                        else:
                            logger.error("Auto re-download failed; model remains unavailable")
                    else:
                        logger.debug("Auto-fix disabled or not applicable for this model")
                except Exception as rec_err:
                    logger.debug(f"Auto-fix logic encountered an error: {rec_err}")
                finally:
                    self._model = None
                    self._loaded = False
                return False
    
    def unload_model(self) -> None:
        """Unload the current model and free memory."""
        with self._lock:
            if self._model:
                # llama.cpp doesn't have explicit cleanup, but we can clear the reference
                self._model = None
                self._loaded = False
                self._load_time = None
                self._memory_usage = None
                logger.info("Model unloaded")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repeat_penalty: Repetition penalty
            stop: Stop sequences
            stream: Whether to stream tokens
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text (string) or token iterator if streaming
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        with self._lock:
            try:
                generation_params = {
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "repeat_penalty": repeat_penalty,
                    "stop": stop or [],
                    "stream": stream,
                    **kwargs
                }
                
                logger.debug(f"Generating with params: {generation_params}")
                
                if stream:
                    return self._stream_generate(prompt, **generation_params)
                else:
                    return self._complete_generate(prompt, **generation_params)
                    
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                raise
    
    def _complete_generate(self, prompt: str, **params) -> str:
        """Generate complete response (non-streaming)."""
        response = self._model(prompt, **params)
        
        if isinstance(response, dict) and "choices" in response:
            return response["choices"][0]["text"]
        elif isinstance(response, str):
            return response
        else:
            logger.warning(f"Unexpected response format: {type(response)}")
            return str(response)
    
    def _stream_generate(self, prompt: str, **params) -> Iterator[str]:
        """Generate streaming response."""
        params["stream"] = True
        
        for chunk in self._model(prompt, **params):
            if isinstance(chunk, dict):
                if "choices" in chunk and chunk["choices"]:
                    choice = chunk["choices"][0]
                    if "text" in choice:
                        yield choice["text"]
                    elif "delta" in choice and "content" in choice["delta"]:
                        yield choice["delta"]["content"]
            elif isinstance(chunk, str):
                yield chunk
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        with self._lock:
            try:
                # Check if model supports embeddings
                if not hasattr(self._model, "embed"):
                    raise RuntimeError("Model does not support embeddings")
                
                embedding = self._model.embed(text)
                return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
                
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                raise
    
    def tokenize(self, text: str) -> List[int]:
        """
        Tokenize text.
        
        Args:
            text: Input text
            
        Returns:
            List of token IDs
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        with self._lock:
            try:
                tokens = self._model.tokenize(text.encode('utf-8'))
                return tokens
            except Exception as e:
                logger.error(f"Tokenization failed: {e}")
                raise
    
    def detokenize(self, tokens: List[int]) -> str:
        """
        Detokenize token IDs to text.
        
        Args:
            tokens: List of token IDs
            
        Returns:
            Decoded text
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        with self._lock:
            try:
                text = self._model.detokenize(tokens)
                return text.decode('utf-8') if isinstance(text, bytes) else text
            except Exception as e:
                logger.error(f"Detokenization failed: {e}")
                raise
    
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self._loaded and self._model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        with self._lock:
            info = {
                "runtime": "llama.cpp",
                "loaded": self._loaded,
                "model_path": self.model_path,
                "load_time": self._load_time,
                "memory_usage": self._memory_usage,
                "context_length": self.n_ctx,
                "batch_size": self.n_batch,
                "gpu_layers": self.n_gpu_layers,
                "threads": self.n_threads,
            }
            
            if self._model and hasattr(self._model, "metadata"):
                try:
                    info["metadata"] = self._model.metadata
                except:
                    pass
            
            return info
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the runtime.
        
        Returns:
            Health status information
        """
        try:
            start_time = time.time()
            
            # Check if llama.cpp is available
            if not LLAMACPP_AVAILABLE:
                return {
                    "status": "unhealthy",
                    "error": "llama-cpp-python not available",
                    "response_time": time.time() - start_time
                }
            
            # Check if model is loaded
            if not self.is_loaded():
                return {
                    "status": "healthy",
                    "message": "Runtime available, no model loaded",
                    "response_time": time.time() - start_time,
                    "capabilities": {
                        "model_loading": True,
                        "text_generation": False,
                        "embeddings": False,
                        "streaming": True
                    }
                }
            
            # Test basic functionality with loaded model
            try:
                # Simple tokenization test
                tokens = self.tokenize("Hello")
                if not tokens:
                    raise RuntimeError("Tokenization returned empty result")
                
                # Test detokenization
                text = self.detokenize(tokens)
                if not text:
                    raise RuntimeError("Detokenization returned empty result")
                
                capabilities = {
                    "model_loading": True,
                    "text_generation": True,
                    "embeddings": hasattr(self._model, "embed"),
                    "streaming": True,
                    "tokenization": True
                }
                
                return {
                    "status": "healthy",
                    "message": "All systems operational",
                    "response_time": time.time() - start_time,
                    "model_info": self.get_model_info(),
                    "capabilities": capabilities
                }
                
            except Exception as e:
                return {
                    "status": "degraded",
                    "error": f"Model functionality test failed: {e}",
                    "response_time": time.time() - start_time,
                    "model_info": self.get_model_info()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": time.time() - start_time if 'start_time' in locals() else None
            }
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        return {
            "memory_usage": self._memory_usage,
            "model_loaded": self.is_loaded(),
            "context_length": self.n_ctx,
            "gpu_layers": self.n_gpu_layers,
            "threads": self.n_threads,
        }
    
    def shutdown(self) -> None:
        """Shutdown the runtime and cleanup resources."""
        logger.info("Shutting down llama.cpp runtime")
        self.unload_model()
    
    @staticmethod
    def is_available() -> bool:
        """Check if llama.cpp runtime is available."""
        return LLAMACPP_AVAILABLE
    
    @staticmethod
    def supports_format(format_name: str) -> bool:
        """Check if runtime supports a specific model format."""
        return format_name.lower() in ["gguf"]
    
    @staticmethod
    def supports_family(family_name: str) -> bool:
        """Check if runtime supports a specific model family."""
        supported_families = [
            "llama", "mistral", "qwen", "phi", "gemma", "codellama",
            "tinyllama", "vicuna", "alpaca", "orca"
        ]
        return family_name.lower() in supported_families


__all__ = ["LlamaCppRuntime"]
