"""
Enhanced Gemini LLM Provider Implementation

Improved version with proper safety filtering, better error handling, and latest API features.
"""

import logging
import time
import os
from typing import Any, Dict, List, Optional, Union, Iterator

from ai_karen_engine.integrations.llm_utils import LLMProviderBase, GenerationFailed, EmbeddingFailed, record_llm_metric

logger = logging.getLogger("kari.gemini_provider")


class GeminiProvider(LLMProviderBase):
    """Enhanced Gemini provider with safety filtering and latest features."""
    
    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        safety_settings: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Gemini provider.
        
        Args:
            model: Default model name (e.g., "gemini-1.5-pro", "gemini-1.5-flash")
            api_key: Google AI API key (from env GEMINI_API_KEY if not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            safety_settings: Custom safety filter settings
        """
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Default safety settings - can be customized
        self.safety_settings = safety_settings or {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE", 
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE"
        }
        
        if not self.api_key:
            logger.warning("No Gemini API key provided. Set GEMINI_API_KEY environment variable.")
        
        try:
            import google.generativeai as genai
            self.genai = genai
            
            if self.api_key:
                genai.configure(api_key=self.api_key)
                
        except ImportError:
            raise GenerationFailed(
                "Google Generative AI package not installed. "
                "Install with: pip install google-generativeai"
            )
    
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
            "quota",
            "rate limit",
            "too many requests",
            "server error", 
            "timeout",
            "503",
            "502",
            "500"
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def _prepare_safety_settings(self) -> List[Dict[str, Any]]:
        """Prepare safety settings for Gemini API."""
        safety_settings = []
        
        for category, threshold in self.safety_settings.items():
            safety_settings.append({
                "category": getattr(self.genai.types.HarmCategory, category, category),
                "threshold": getattr(self.genai.types.HarmBlockThreshold, threshold, threshold)
            })
        
        return safety_settings
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini API."""
        t0 = time.time()
        
        if not self.api_key:
            raise GenerationFailed("Gemini API key required")
        
        try:
            model_name = kwargs.pop("model", self.model)
            
            # Initialize model
            model = self.genai.GenerativeModel(model_name)
            
            # Prepare generation config
            generation_config = {
                "temperature": kwargs.pop("temperature", 0.7),
                "top_p": kwargs.pop("top_p", 0.8),
                "top_k": kwargs.pop("top_k", 40),
                "max_output_tokens": kwargs.pop("max_tokens", kwargs.pop("max_output_tokens", 1000)),
            }
            
            # Add any additional config parameters
            generation_config.update({k: v for k, v in kwargs.items() if k not in ["stream", "safety_settings"]})
            
            # Prepare safety settings
            safety_settings = kwargs.get("safety_settings", self._prepare_safety_settings())
            
            def _generate():
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # Check if response was blocked by safety filters
                if response.prompt_feedback.block_reason:
                    raise GenerationFailed(
                        f"Content blocked by safety filters: {response.prompt_feedback.block_reason}"
                    )
                
                # Check if any candidate was blocked
                if not response.candidates:
                    raise GenerationFailed("No response candidates generated")
                
                candidate = response.candidates[0]
                if candidate.finish_reason and candidate.finish_reason.name != "STOP":
                    logger.warning(f"Generation finished with reason: {candidate.finish_reason.name}")
                
                return candidate.content.parts[0].text if candidate.content.parts else ""
            
            text = self._retry_with_backoff(_generate)
            
            record_llm_metric("generate_text", time.time() - t0, True, "gemini")
            return text
            
        except Exception as ex:
            record_llm_metric(
                "generate_text", time.time() - t0, False, "gemini", error=str(ex)
            )
            
            # Provide more specific error messages
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg:
                raise GenerationFailed("Invalid Gemini API key. Check your GEMINI_API_KEY environment variable.")
            elif "quota" in error_msg or "rate limit" in error_msg:
                raise GenerationFailed("Gemini quota exceeded or rate limited. Please try again later.")
            elif "safety" in error_msg or "blocked" in error_msg:
                raise GenerationFailed("Content blocked by Gemini safety filters. Try rephrasing your prompt.")
            elif "model" in error_msg and "not found" in error_msg:
                raise GenerationFailed(f"Model '{model_name}' not available. Check available models.")
            else:
                raise GenerationFailed(f"Gemini generation failed: {ex}")
    
    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """Generate text with streaming support."""
        if not self.api_key:
            raise GenerationFailed("Gemini API key required")
        
        try:
            model_name = kwargs.pop("model", self.model)
            
            # Initialize model
            model = self.genai.GenerativeModel(model_name)
            
            # Prepare generation config
            generation_config = {
                "temperature": kwargs.pop("temperature", 0.7),
                "top_p": kwargs.pop("top_p", 0.8),
                "top_k": kwargs.pop("top_k", 40),
                "max_output_tokens": kwargs.pop("max_tokens", kwargs.pop("max_output_tokens", 1000)),
            }
            
            # Add any additional config parameters
            generation_config.update({k: v for k, v in kwargs.items() if k not in ["safety_settings"]})
            
            # Prepare safety settings
            safety_settings = kwargs.get("safety_settings", self._prepare_safety_settings())
            
            def _stream():
                return model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    stream=True
                )
            
            stream = self._retry_with_backoff(_stream)
            
            for chunk in stream:
                if chunk.candidates and chunk.candidates[0].content.parts:
                    yield chunk.candidates[0].content.parts[0].text
                    
        except Exception as ex:
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg:
                raise GenerationFailed("Invalid Gemini API key. Check your GEMINI_API_KEY environment variable.")
            elif "quota" in error_msg or "rate limit" in error_msg:
                raise GenerationFailed("Gemini quota exceeded or rate limited. Please try again later.")
            elif "safety" in error_msg or "blocked" in error_msg:
                raise GenerationFailed("Content blocked by Gemini safety filters. Try rephrasing your prompt.")
            else:
                raise GenerationFailed(f"Gemini streaming failed: {ex}")
    
    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Generate embeddings using Gemini embedding models."""
        t0 = time.time()
        
        if not self.api_key:
            raise EmbeddingFailed("Gemini API key required")
        
        try:
            # Use embedding model
            model = kwargs.get("embedding_model", "models/embedding-001")
            
            def _embed():
                if isinstance(text, str):
                    result = self.genai.embed_content(
                        model=model,
                        content=text,
                        task_type="retrieval_document"
                    )
                    return result["embedding"]
                else:
                    embeddings = []
                    for t in text:
                        result = self.genai.embed_content(
                            model=model,
                            content=t,
                            task_type="retrieval_document"
                        )
                        embeddings.append(result["embedding"])
                    return embeddings
            
            embeddings = self._retry_with_backoff(_embed)
            
            record_llm_metric("embed", time.time() - t0, True, "gemini")
            return embeddings
            
        except Exception as ex:
            record_llm_metric("embed", time.time() - t0, False, "gemini", error=str(ex))
            
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg:
                raise EmbeddingFailed("Invalid Gemini API key. Check your GEMINI_API_KEY environment variable.")
            elif "quota" in error_msg or "rate limit" in error_msg:
                raise EmbeddingFailed("Gemini quota exceeded or rate limited. Please try again later.")
            else:
                raise EmbeddingFailed(f"Gemini embedding failed: {ex}")
    
    def get_models(self) -> List[str]:
        """Get list of available models from Gemini."""
        try:
            if not self.api_key:
                return self._get_common_models()
            
            def _list_models():
                models = []
                for model in self.genai.list_models():
                    if "generateContent" in model.supported_generation_methods:
                        models.append(model.name.replace("models/", ""))
                return models
            
            return self._retry_with_backoff(_list_models)
            
        except Exception as ex:
            logger.warning(f"Could not fetch Gemini models: {ex}")
            return self._get_common_models()
    
    def _get_common_models(self) -> List[str]:
        """Get list of common Gemini models."""
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-pro-vision"
        ]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        try:
            models = self.get_models()
        except Exception:
            models = []
        
        return {
            "name": "gemini",
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "available_models": models,
            "supports_streaming": True,
            "supports_embeddings": True,
            "supports_multimodal": True,
            "safety_settings": self.safety_settings,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Gemini API."""
        if not self.api_key:
            return {
                "status": "unhealthy",
                "error": "No API key provided"
            }
        
        try:
            start_time = time.time()
            
            # Simple test request
            model = self.genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                "Hello",
                generation_config={"max_output_tokens": 1}
            )
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "model_tested": "gemini-1.5-flash"
            }
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": str(ex)
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
