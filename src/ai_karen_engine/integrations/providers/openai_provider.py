"""
Enhanced OpenAI LLM Provider Implementation

Improved version with latest API features, better error handling, and streaming support.
"""

import logging
import time
import os
from typing import Any, Dict, List, Optional, Union, Iterator

from ai_karen_engine.integrations.llm_utils import LLMProviderBase, GenerationFailed, EmbeddingFailed, record_llm_metric

logger = logging.getLogger("kari.openai_provider")


class OpenAIProvider(LLMProviderBase):
    """Enhanced OpenAI provider with latest API features."""
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            model: Default model name (e.g., "gpt-3.5-turbo", "gpt-4")
            api_key: OpenAI API key (from env OPENAI_API_KEY if not provided)
            base_url: Custom base URL for OpenAI-compatible APIs
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
        
        try:
            import openai
            self.openai = openai
            
            # Initialize client with custom settings
            client_kwargs = {"api_key": self.api_key, "timeout": self.timeout}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            self.client = openai.OpenAI(**client_kwargs)
            
        except ImportError:
            raise GenerationFailed("OpenAI Python package not installed. Install with: pip install openai")
    
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
        """Generate text using OpenAI API."""
        t0 = time.time()
        
        if not self.api_key:
            raise GenerationFailed("OpenAI API key required")
        
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
            
            record_llm_metric("generate_text", time.time() - t0, True, "openai")
            return text
            
        except Exception as ex:
            record_llm_metric(
                "generate_text", time.time() - t0, False, "openai", error=str(ex)
            )
            
            # Provide more specific error messages
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg:
                raise GenerationFailed("Invalid OpenAI API key. Check your OPENAI_API_KEY environment variable.")
            elif "rate limit" in error_msg or "quota" in error_msg:
                raise GenerationFailed("OpenAI rate limit exceeded or quota reached. Please try again later.")
            elif "model" in error_msg and "not found" in error_msg:
                raise GenerationFailed(f"Model '{model}' not available. Check available models.")
            else:
                raise GenerationFailed(f"OpenAI generation failed: {ex}")
    
    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """Generate text with streaming support."""
        if not self.api_key:
            raise GenerationFailed("OpenAI API key required")
        
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
                raise GenerationFailed("Invalid OpenAI API key. Check your OPENAI_API_KEY environment variable.")
            elif "rate limit" in error_msg:
                raise GenerationFailed("OpenAI rate limit exceeded. Please try again later.")
            else:
                raise GenerationFailed(f"OpenAI streaming failed: {ex}")
    
    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Generate embeddings using OpenAI embeddings API."""
        t0 = time.time()
        
        if not self.api_key:
            raise EmbeddingFailed("OpenAI API key required")
        
        try:
            # Use embedding model
            model = kwargs.get("embedding_model", "text-embedding-3-small")
            
            def _embed():
                if isinstance(text, str):
                    response = self.client.embeddings.create(
                        model=model,
                        input=text
                    )
                    return response.data[0].embedding
                else:
                    response = self.client.embeddings.create(
                        model=model,
                        input=text
                    )
                    return [item.embedding for item in response.data]
            
            embeddings = self._retry_with_backoff(_embed)
            
            record_llm_metric("embed", time.time() - t0, True, "openai")
            return embeddings
            
        except Exception as ex:
            record_llm_metric("embed", time.time() - t0, False, "openai", error=str(ex))
            
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg:
                raise EmbeddingFailed("Invalid OpenAI API key. Check your OPENAI_API_KEY environment variable.")
            elif "rate limit" in error_msg:
                raise EmbeddingFailed("OpenAI rate limit exceeded. Please try again later.")
            else:
                raise EmbeddingFailed(f"OpenAI embedding failed: {ex}")
    
    def get_models(self) -> List[str]:
        """Get list of available models from OpenAI."""
        try:
            if not self.api_key:
                # Return common models as fallback
                return self._get_common_models()
            
            def _list_models():
                models = self.client.models.list()
                return [model.id for model in models.data if "gpt" in model.id.lower()]
            
            return self._retry_with_backoff(_list_models)
            
        except Exception as ex:
            logger.warning(f"Could not fetch OpenAI models: {ex}")
            return self._get_common_models()
    
    def _get_common_models(self) -> List[str]:
        """Get list of common OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        try:
            models = self.get_models()
        except Exception:
            models = []
        
        return {
            "name": "openai",
            "model": self.model,
            "base_url": self.base_url or "https://api.openai.com/v1",
            "has_api_key": bool(self.api_key),
            "available_models": models,
            "supports_streaming": True,
            "supports_embeddings": True,
            "supports_function_calling": True,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on OpenAI API."""
        if not self.api_key:
            return {
                "status": "unhealthy",
                "error": "No API key provided"
            }
        
        try:
            start_time = time.time()
            
            # Simple test request
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "model_tested": "gpt-3.5-turbo"
            }
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": str(ex)
            }