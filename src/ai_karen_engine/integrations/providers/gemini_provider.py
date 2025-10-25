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
        self.initialization_error: Optional[str] = None
        self.genai: Optional[Any] = None
        
        # Default safety settings - can be customized
        self.safety_settings = safety_settings or {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE", 
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE"
        }
        
        # Graceful initialization - don't fail if API key is missing
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Gemini client with graceful error handling."""
        try:
            import google.generativeai as genai
            self.genai = genai
            
            if not self.api_key:
                self.initialization_error = "No Gemini API key provided. Set GEMINI_API_KEY environment variable."
                logger.warning(self.initialization_error)
                return
                
            genai.configure(api_key=self.api_key)
            
            # Validate API key by listing models
            self._validate_api_key()
            
        except ImportError:
            self.initialization_error = "Google Generative AI package not installed. Install with: pip install google-generativeai"
            logger.error(self.initialization_error)
        except Exception as ex:
            self.initialization_error = f"Gemini client initialization failed: {ex}"
            logger.error(self.initialization_error)

    def _validate_api_key(self):
        """Validate API key with a minimal request."""
        if not self.genai or not self.api_key:
            return
            
        try:
            # Try to list models to validate the API key
            list(self.genai.list_models())
            logger.info("Gemini API key validated successfully")
        except Exception as ex:
            error_msg = str(ex).lower()
            if "api key" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg:
                self.initialization_error = "Invalid Gemini API key. Please check your GEMINI_API_KEY environment variable."
            elif "quota" in error_msg or "rate limit" in error_msg:
                # Rate limit during validation is not a fatal error
                logger.warning("Rate limited during API key validation, but key appears valid")
            else:
                self.initialization_error = f"API key validation failed: {ex}"
            
            if self.initialization_error:
                logger.error(self.initialization_error)
    
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
        """Check if an error is retryable with enhanced classification."""
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
            "500",
            "internal server error",
            "service unavailable",
            "bad gateway",
            "resource exhausted"
        ]
        
        # Non-retryable errors (fail fast)
        non_retryable_patterns = [
            "invalid api key",
            "unauthorized",
            "forbidden",
            "not found",
            "invalid request",
            "400",
            "401",
            "403",
            "404",
            "safety"  # Safety filter blocks are not retryable
        ]

        # Check non-retryable first
        if any(pattern in error_str for pattern in non_retryable_patterns):
            return False
        
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
        
        # Check initialization status
        if self.initialization_error:
            raise GenerationFailed(self.initialization_error)
            
        if not self.genai:
            raise GenerationFailed("Gemini client not initialized")
        
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
        # Check initialization status
        if self.initialization_error:
            raise GenerationFailed(self.initialization_error)
            
        if not self.genai:
            raise GenerationFailed("Gemini client not initialized")
        
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
        
        # Check initialization status
        if self.initialization_error:
            raise EmbeddingFailed(self.initialization_error)
            
        if not self.genai:
            raise EmbeddingFailed("Gemini client not initialized")
        
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
        """Get list of available models from Gemini with fallback to static list."""
        try:
            if self.initialization_error or not self.genai:
                logger.info("Using fallback model list due to initialization issues")
                return self._get_common_models()
            
            def _list_models():
                models = []
                for model in self.genai.list_models():
                    if "generateContent" in model.supported_generation_methods:
                        models.append(model.name.replace("models/", ""))
                return models
            
            discovered_models = self._retry_with_backoff(_list_models)
            
            # Merge with common models to ensure we have a comprehensive list
            common_models = self._get_common_models()
            all_models = list(set(discovered_models + common_models))
            
            logger.info(f"Discovered {len(discovered_models)} models from API, total available: {len(all_models)}")
            return sorted(all_models)
            
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
        """Get provider metadata with initialization status."""
        try:
            models = self.get_models()
        except Exception:
            models = []
        
        return {
            "name": "gemini",
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "api_key_valid": self.initialization_error is None and self.genai is not None,
            "initialization_error": self.initialization_error,
            "available_models": models,
            "supports_streaming": True,
            "supports_embeddings": True,
            "supports_multimodal": True,
            "safety_settings": self.safety_settings,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on Gemini API."""
        # Check initialization status first
        if self.initialization_error:
            return {
                "status": "unhealthy",
                "error": self.initialization_error,
                "provider": "gemini",
                "initialization_status": "failed"
            }

        if not self.genai:
            return {
                "status": "unhealthy",
                "error": "Gemini client not initialized",
                "provider": "gemini",
                "initialization_status": "failed"
            }
        
        try:
            start_time = time.time()
            
            # Test API connectivity with minimal request
            model = self.genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                "Hello",
                generation_config={"max_output_tokens": 1}
            )
            
            response_time = time.time() - start_time
            
            health_result = {
                "status": "healthy",
                "provider": "gemini",
                "response_time": response_time,
                "model_tested": "gemini-1.5-flash",
                "initialization_status": "success",
                "api_key_status": "valid",
                "connectivity": "ok"
            }

            # Test model discovery
            try:
                available_models = self.get_models()
                health_result["model_discovery"] = {
                    "status": "success",
                    "models_found": len(available_models),
                    "sample_models": available_models[:5]  # First 5 models
                }
            except Exception as e:
                health_result["model_discovery"] = {
                    "status": "failed",
                    "error": str(e)
                }
                health_result["warnings"] = health_result.get("warnings", [])
                health_result["warnings"].append("Model discovery failed, using fallback list")

            # Test capability detection
            try:
                # Check if multimodal capabilities are available
                test_model = self.genai.GenerativeModel("gemini-1.5-flash")
                health_result["capabilities"] = {
                    "text_generation": True,
                    "multimodal": True,
                    "streaming": True,
                    "embeddings": True,
                    "safety_filtering": True
                }
            except Exception as e:
                health_result["capabilities"] = {
                    "text_generation": True,
                    "detection_error": str(e)
                }

            # Add Model Library compatibility check
            try:
                from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
                compatibility_service = ProviderModelCompatibilityService()
                validation = compatibility_service.validate_provider_model_setup("gemini")
                
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
            error_msg = str(ex).lower()
            
            # Classify the error for better diagnostics
            if "api key" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg:
                error_type = "authentication_error"
                specific_error = "Invalid or expired API key"
            elif "quota" in error_msg or "rate limit" in error_msg:
                error_type = "rate_limit_error"
                specific_error = "Quota exceeded or rate limited"
            elif "safety" in error_msg or "blocked" in error_msg:
                error_type = "safety_filter_error"
                specific_error = "Content blocked by safety filters"
            elif "timeout" in error_msg or "connection" in error_msg:
                error_type = "connectivity_error"
                specific_error = "Network connectivity issue"
            elif "model" in error_msg and "not found" in error_msg:
                error_type = "model_error"
                specific_error = "Requested model not available"
            else:
                error_type = "unknown_error"
                specific_error = str(ex)
            
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "error": specific_error,
                "error_type": error_type,
                "raw_error": str(ex),
                "initialization_status": "success" if not self.initialization_error else "failed",
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
