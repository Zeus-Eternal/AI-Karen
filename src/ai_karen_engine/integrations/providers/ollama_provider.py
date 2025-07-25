"""
Enhanced Ollama LLM Provider Implementation

Improved version with better error handling, retry logic, and streaming support.
"""

import logging
import time
import os
from typing import Any, Dict, List, Optional, Union, Iterator

from ..llm_utils import LLMProviderBase, GenerationFailed, EmbeddingFailed, record_llm_metric

logger = logging.getLogger("kari.ollama_provider")


class OllamaProvider(LLMProviderBase):
    """Enhanced Ollama provider with improved error handling and features."""
    
    def __init__(
        self,
        model: str = "llama3.2:latest",
        base_url: str = "http://localhost:11434",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Default model name (e.g., "llama3.2:latest")
            base_url: Ollama server URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        try:
            import ollama
            self.ollama = ollama
            # Configure client with custom base URL if provided
            if base_url != "http://localhost:11434":
                self.client = ollama.Client(host=base_url)
            else:
                self.client = ollama
        except ImportError:
            raise GenerationFailed("Ollama Python package not installed. Install with: pip install ollama")
        
        # Test connection on initialization
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            # Try to list models to test connection
            self.client.list()
            logger.info(f"Successfully connected to Ollama at {self.base_url}")
        except Exception as ex:
            logger.warning(f"Could not connect to Ollama at {self.base_url}: {ex}")
            # Don't fail initialization, just log warning
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                last_exception = ex
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {ex}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_exception
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from Ollama with enhanced error handling."""
        t0 = time.time()
        
        try:
            model = kwargs.pop("model", self.model)
            
            # Prepare generation options
            options = {
                "temperature": kwargs.pop("temperature", 0.7),
                "num_predict": kwargs.pop("max_tokens", kwargs.pop("num_predict", 100)),
                "top_p": kwargs.pop("top_p", 0.9),
                "top_k": kwargs.pop("top_k", 40),
            }
            
            # Add any additional options
            options.update({k: v for k, v in kwargs.items() if k not in ["stream"]})
            
            def _generate():
                result = self.client.generate(
                    model=model,
                    prompt=prompt,
                    options=options,
                    stream=False
                )
                return result.get("response") or result.get("text") or ""
            
            text = self._retry_with_backoff(_generate)
            
            record_llm_metric("generate_text", time.time() - t0, True, "ollama")
            return text
            
        except Exception as ex:
            record_llm_metric(
                "generate_text", time.time() - t0, False, "ollama", error=str(ex)
            )
            
            # Provide more specific error messages
            error_msg = str(ex).lower()
            if "connection" in error_msg or "refused" in error_msg:
                raise GenerationFailed(
                    f"Cannot connect to Ollama server at {self.base_url}. "
                    f"Make sure Ollama is running and accessible."
                )
            elif "model" in error_msg and "not found" in error_msg:
                raise GenerationFailed(
                    f"Model '{model}' not found. Pull the model first with: ollama pull {model}"
                )
            else:
                raise GenerationFailed(f"Ollama generation failed: {ex}")
    
    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """Generate text with streaming support."""
        try:
            model = kwargs.pop("model", self.model)
            
            # Prepare generation options
            options = {
                "temperature": kwargs.pop("temperature", 0.7),
                "num_predict": kwargs.pop("max_tokens", kwargs.pop("num_predict", 100)),
                "top_p": kwargs.pop("top_p", 0.9),
                "top_k": kwargs.pop("top_k", 40),
            }
            
            # Add any additional options
            options.update({k: v for k, v in kwargs.items()})
            
            def _stream():
                return self.client.generate(
                    model=model,
                    prompt=prompt,
                    options=options,
                    stream=True
                )
            
            stream = self._retry_with_backoff(_stream)
            
            for chunk in stream:
                if "response" in chunk:
                    yield chunk["response"]
                elif "text" in chunk:
                    yield chunk["text"]
                    
        except Exception as ex:
            error_msg = str(ex).lower()
            if "connection" in error_msg or "refused" in error_msg:
                raise GenerationFailed(
                    f"Cannot connect to Ollama server at {self.base_url}. "
                    f"Make sure Ollama is running and accessible."
                )
            else:
                raise GenerationFailed(f"Ollama streaming failed: {ex}")
    
    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Generate embeddings using Ollama embedding models."""
        t0 = time.time()
        
        try:
            # Use embedding model if specified, otherwise try to use current model
            model = kwargs.get("model", kwargs.get("embedding_model", "nomic-embed-text"))
            
            def _embed():
                if isinstance(text, str):
                    result = self.client.embeddings(model=model, prompt=text)
                    return result.get("embedding", [])
                else:
                    # Handle list of texts
                    embeddings = []
                    for t in text:
                        result = self.client.embeddings(model=model, prompt=t)
                        embeddings.append(result.get("embedding", []))
                    return embeddings
            
            embeddings = self._retry_with_backoff(_embed)
            
            record_llm_metric("embed", time.time() - t0, True, "ollama")
            return embeddings
            
        except Exception as ex:
            record_llm_metric("embed", time.time() - t0, False, "ollama", error=str(ex))
            
            error_msg = str(ex).lower()
            if "model" in error_msg and "not found" in error_msg:
                raise EmbeddingFailed(
                    f"Embedding model '{model}' not found. "
                    f"Pull an embedding model first with: ollama pull nomic-embed-text"
                )
            else:
                raise EmbeddingFailed(f"Ollama embedding failed: {ex}")
    
    def get_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            def _list_models():
                result = self.client.list()
                return [model["name"] for model in result.get("models", [])]
            
            return self._retry_with_backoff(_list_models)
            
        except Exception as ex:
            logger.warning(f"Could not fetch Ollama models: {ex}")
            # Return common models as fallback
            return [
                "llama3.2:latest",
                "llama3.1:latest", 
                "codellama:latest",
                "mistral:latest",
                "phi3:latest",
                "nomic-embed-text:latest"
            ]
    
    def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            def _pull():
                self.client.pull(model)
                return True
            
            return self._retry_with_backoff(_pull)
            
        except Exception as ex:
            logger.error(f"Failed to pull model {model}: {ex}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        try:
            models = self.get_models()
        except Exception:
            models = []
        
        return {
            "name": "ollama",
            "base_url": self.base_url,
            "model": self.model,
            "available_models": models,
            "supports_streaming": True,
            "supports_embeddings": True,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Ollama server."""
        try:
            start_time = time.time()
            models = self.get_models()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "available_models": len(models),
                "base_url": self.base_url
            }
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": str(ex),
                "base_url": self.base_url
            }