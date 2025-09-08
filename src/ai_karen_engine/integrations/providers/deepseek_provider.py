"""
Enhanced Deepseek LLM Provider Implementation

Improved version with streaming support, better error handling, and latest API features.
"""

import logging
import time
import os
from typing import Any, Dict, List, Optional, Union, Iterator

from ai_karen_engine.integrations.llm_utils import LLMProviderBase, GenerationFailed, EmbeddingFailed, record_llm_metric

logger = logging.getLogger("kari.deepseek_provider")


class DeepseekProvider(LLMProviderBase):
    """Enhanced Deepseek provider with streaming support and latest features."""
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize Deepseek provider.
        
        Args:
            model: Default model name (e.g., "deepseek-chat", "deepseek-coder")
            api_key: Deepseek API key (from env DEEPSEEK_API_KEY if not provided)
            base_url: Deepseek API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.model = model
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("No Deepseek API key provided. Set DEEPSEEK_API_KEY environment variable.")
        
        # Deepseek uses OpenAI-compatible API, so we can use the OpenAI client
        try:
            import openai
            self.openai = openai
            
            # Initialize client with Deepseek settings
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            
        except ImportError:
            raise GenerationFailed("OpenAI Python package required for Deepseek. Install with: pip install openai")
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                last_exception = ex
                
                # Check if it's a retryable error
                if self._is_retryable_error(ex):
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {ex}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {self.max_retries} attempts failed")
                else:
                    # Non-retryable error, fail immediately
                    break
        
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        error_str = str(error).lower()
        
        # Rate limiting and server errors are retryable
        retryable_patterns = [
            "rate limit",
            "too many requests",
            "server error",
            "timeout",
            "connection",
            "503",
            "502", 
            "500"
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Deepseek API."""
        t0 = time.time()
        
        if not self.api_key:
            raise GenerationFailed("Deepseek API key required")
        
        try:
            model = kwargs.pop("model", self.model)
            
            # Prepare chat completion parameters
            messages = [{"role": "user", "content": prompt}]
            
            # Handle system message if provided
            if "system_message" in kwargs:
                messages.insert(0, {"role": "system", "content": kwargs.pop("system_message")})
            
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.pop("max_tokens", 1000),
                "temperature": kwargs.pop("temperature", 0.7),
                "top_p": kwargs.pop("top_p", 1.0),
                "frequency_penalty": kwargs.pop("frequency_penalty", 0.0),
                "presence_penalty": kwargs.pop("presence_penalty", 0.0),
            }
            
            # Add any additional parameters
            completion_kwargs.update({k: v for k, v in kwargs.items() if k not in ["stream"]})
            
            def _generate():
                response = self.client.chat.completions.create(**completion_kwargs)
                return response.choices[0].message.content or ""
            
            text = self._retry_with_backoff(_generate)
            
            record_llm_metric("generate_text", time.time() - t0, True, "deepseek")
            return text
            
        except Exception as ex:
            record_llm_metric(
                "generate_text", time.time() - t0, False, "deepseek", error=str(ex)
            )
            
            # Provide more specific error messages
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg:
                raise GenerationFailed("Invalid Deepseek API key. Check your DEEPSEEK_API_KEY environment variable.")
            elif "rate limit" in error_msg or "quota" in error_msg:
                raise GenerationFailed("Deepseek rate limit exceeded or quota reached. Please try again later.")
            elif "model" in error_msg and "not found" in error_msg:
                raise GenerationFailed(f"Model '{model}' not available. Check available models.")
            else:
                raise GenerationFailed(f"Deepseek generation failed: {ex}")
    
    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """Generate text with streaming support."""
        if not self.api_key:
            raise GenerationFailed("Deepseek API key required")
        
        try:
            model = kwargs.pop("model", self.model)
            
            # Prepare chat completion parameters
            messages = [{"role": "user", "content": prompt}]
            
            # Handle system message if provided
            if "system_message" in kwargs:
                messages.insert(0, {"role": "system", "content": kwargs.pop("system_message")})
            
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.pop("max_tokens", 1000),
                "temperature": kwargs.pop("temperature", 0.7),
                "top_p": kwargs.pop("top_p", 1.0),
                "frequency_penalty": kwargs.pop("frequency_penalty", 0.0),
                "presence_penalty": kwargs.pop("presence_penalty", 0.0),
                "stream": True
            }
            
            # Add any additional parameters
            completion_kwargs.update({k: v for k, v in kwargs.items()})
            
            def _stream():
                return self.client.chat.completions.create(**completion_kwargs)
            
            stream = self._retry_with_backoff(_stream)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as ex:
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg:
                raise GenerationFailed("Invalid Deepseek API key. Check your DEEPSEEK_API_KEY environment variable.")
            elif "rate limit" in error_msg:
                raise GenerationFailed("Deepseek rate limit exceeded. Please try again later.")
            else:
                raise GenerationFailed(f"Deepseek streaming failed: {ex}")
    
    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Generate embeddings using Deepseek API (if supported)."""
        t0 = time.time()
        
        # Note: Deepseek may not have a dedicated embedding API
        # This is a placeholder implementation that could be updated when available
        try:
            # For now, we'll raise an informative error
            raise EmbeddingFailed(
                "Deepseek embedding API not yet supported. "
                "Use another provider like OpenAI or HuggingFace for embeddings."
            )
            
        except Exception as ex:
            record_llm_metric("embed", time.time() - t0, False, "deepseek", error=str(ex))
            raise EmbeddingFailed(f"Deepseek embedding failed: {ex}")
    
    def get_models(self) -> List[str]:
        """Get list of available models from Deepseek."""
        try:
            if not self.api_key:
                return self._get_common_models()
            
            def _list_models():
                models = self.client.models.list()
                return [model.id for model in models.data]
            
            return self._retry_with_backoff(_list_models)
            
        except Exception as ex:
            logger.warning(f"Could not fetch Deepseek models: {ex}")
            return self._get_common_models()
    
    def _get_common_models(self) -> List[str]:
        """Get list of common Deepseek models."""
        return [
            "deepseek-chat",
            "deepseek-coder"
        ]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        try:
            models = self.get_models()
        except Exception:
            models = []
        
        return {
            "name": "deepseek",
            "model": self.model,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "available_models": models,
            "supports_streaming": True,
            "supports_embeddings": False,  # Not yet supported
            "supports_code_generation": True,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Deepseek API with model availability information."""
        if not self.api_key:
            return {
                "status": "unhealthy",
                "error": "No API key provided"
            }
        
        try:
            start_time = time.time()
            
            # Simple test request
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            
            response_time = time.time() - start_time
            
            health_result = {
                "status": "healthy",
                "response_time": response_time,
                "model_tested": "deepseek-chat"
            }

            # Add Model Library compatibility check
            try:
                from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
                compatibility_service = ProviderModelCompatibilityService()
                validation = compatibility_service.validate_provider_model_setup("deepseek")
                
                health_result["model_library"] = {
                    "available": True,
                    "compatible_models_count": validation.get("total_compatible", 0),
                    "validation_status": validation.get("status", "unknown")
                }
                
                # Add recommendations if no compatible models
                if validation.get("total_compatible", 0) == 0:
                    health_result["warnings"] = health_result.get("warnings", [])
                    health_result["warnings"].append("No compatible models found in Model Library")
                
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
                "model_library": {
                    "available": False,
                    "error": "Provider health check failed"
                }
            }

    # Lightweight status helpers -------------------------------------------------

    def ping(self) -> bool:
        try:
            self.health_check()
            return True
        except Exception:
            return False

    def available_models(self) -> list[str]:
        try:
            return self.get_models()
        except Exception:
            return [self.model]
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            int: Estimated number of tokens
        """
        try:
            # Use tiktoken for accurate token counting
            import tiktoken
            
            # Get encoding for the current model
            model = self.model.lower()
            if "coder" in model:
                encoding = tiktoken.encoding_for_model("gpt-4")  # Close approximation for coder model
            else:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")  # Close approximation for chat model
                
            return len(encoding.encode(text))
            
        except ImportError:
            # Fallback to rough estimation if tiktoken not available
            logger.warning("tiktoken not installed. Using rough token estimation.")
            return len(text.split()) * 1.3  # Rough estimation
        
        except Exception as ex:
            logger.warning(f"Token counting failed: {ex}. Using rough estimation.")
            return len(text.split()) * 1.3  # Rough estimation
