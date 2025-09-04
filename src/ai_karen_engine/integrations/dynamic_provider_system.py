"""
Dynamic Provider System with API Key Validation and Live Model Discovery

This module implements a dynamic provider system that:
- Discovers available models from provider APIs in real-time
- Validates API keys with live provider endpoints
- Falls back to curated model lists when APIs are unavailable
- Provides health monitoring and automatic failover
- Excludes non-LLM providers like CopilotKit from LLM settings
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_karen_engine.integrations.registry import (
    ProviderSpec, 
    ModelMetadata, 
    HealthStatus, 
    get_registry
)

logger = logging.getLogger(__name__)

# -----------------------------
# Enhanced Provider Specs
# -----------------------------

@dataclass
class DynamicProviderSpec(ProviderSpec):
    """Enhanced provider specification with dynamic discovery capabilities."""
    
    # API configuration
    api_base_url: Optional[str] = None
    api_key_env_var: Optional[str] = None
    api_key_validation_endpoint: Optional[str] = None
    
    # Model discovery
    model_discovery_endpoint: Optional[str] = None
    model_list_parser: Optional[callable] = None
    
    # Rate limiting and caching
    discovery_cache_ttl: int = 3600  # 1 hour
    last_discovery: Optional[float] = None
    cached_models: List[Dict[str, Any]] = field(default_factory=list)
    
    # Provider categorization
    is_llm_provider: bool = True  # False for CopilotKit, etc.
    provider_type: str = "remote"  # remote, local, hybrid
    
    # Validation settings
    validation_timeout: int = 10
    max_validation_retries: int = 2


class DynamicProviderManager:
    """
    Manager for dynamic provider discovery and validation.
    
    Features:
    - Real-time model discovery from provider APIs
    - API key validation with immediate feedback
    - Intelligent fallback to curated model lists
    - Health monitoring and automatic failover
    - Provider categorization (LLM vs non-LLM)
    """
    
    def __init__(self):
        self.registry = get_registry()
        self._executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="provider-discovery")
        self._validation_cache: Dict[str, Dict[str, Any]] = {}
        self._discovery_locks: Dict[str, asyncio.Lock] = {}
        
        # Register enhanced provider specs
        self._register_dynamic_providers()
    
    def _register_dynamic_providers(self) -> None:
        """Register enhanced provider specifications with dynamic capabilities."""
        
        # OpenAI Provider
        openai_spec = DynamicProviderSpec(
            name="openai",
            requires_api_key=True,
            description="OpenAI GPT models via API",
            category="LLM",
            capabilities={"streaming", "embeddings", "function_calling", "vision"},
            api_base_url="https://api.openai.com/v1",
            api_key_env_var="OPENAI_API_KEY",
            api_key_validation_endpoint="/models",
            model_discovery_endpoint="/models",
            model_list_parser=self._parse_openai_models,
            fallback_models=[
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "family": "gpt",
                    "capabilities": ["text", "vision"],
                    "context_length": 128000,
                    "parameters": "Unknown"
                },
                {
                    "id": "gpt-4o-mini", 
                    "name": "GPT-4o Mini",
                    "family": "gpt",
                    "capabilities": ["text"],
                    "context_length": 128000,
                    "parameters": "Unknown"
                },
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo", 
                    "family": "gpt",
                    "capabilities": ["text"],
                    "context_length": 16385,
                    "parameters": "Unknown"
                },
            ],
            discover=lambda: self.discover_models("openai"),
            validate=lambda config: self.validate_api_key("openai", config),
            health_check=lambda: self.health_check("openai"),
            is_llm_provider=True,
            provider_type="remote"
        )
        self.registry.register_provider(openai_spec)
        
        # Gemini Provider
        gemini_spec = DynamicProviderSpec(
            name="gemini",
            requires_api_key=True,
            description="Google Gemini models via API",
            category="LLM",
            capabilities={"streaming", "embeddings", "vision"},
            api_base_url="https://generativelanguage.googleapis.com/v1beta",
            api_key_env_var="GEMINI_API_KEY",
            api_key_validation_endpoint="/models",
            model_discovery_endpoint="/models",
            model_list_parser=self._parse_gemini_models,
            fallback_models=[
                {
                    "id": "gemini-1.5-pro",
                    "name": "Gemini 1.5 Pro",
                    "family": "gemini",
                    "capabilities": ["text", "vision"],
                    "context_length": 2097152,
                    "parameters": "Unknown"
                },
                {
                    "id": "gemini-1.5-flash",
                    "name": "Gemini 1.5 Flash",
                    "family": "gemini", 
                    "capabilities": ["text", "vision"],
                    "context_length": 1048576,
                    "parameters": "Unknown"
                },
            ],
            discover=lambda: self.discover_models("gemini"),
            validate=lambda config: self.validate_api_key("gemini", config),
            health_check=lambda: self.health_check("gemini"),
            is_llm_provider=True,
            provider_type="remote"
        )
        self.registry.register_provider(gemini_spec)
        
        # DeepSeek Provider
        deepseek_spec = DynamicProviderSpec(
            name="deepseek",
            requires_api_key=True,
            description="DeepSeek models optimized for coding and reasoning",
            category="LLM",
            capabilities={"streaming", "function_calling"},
            api_base_url="https://api.deepseek.com",
            api_key_env_var="DEEPSEEK_API_KEY",
            api_key_validation_endpoint="/models",
            model_discovery_endpoint="/models",
            model_list_parser=self._parse_deepseek_models,
            fallback_models=[
                {
                    "id": "deepseek-chat",
                    "name": "DeepSeek Chat",
                    "family": "deepseek",
                    "capabilities": ["text", "code"],
                    "context_length": 32768,
                    "parameters": "67B"
                },
                {
                    "id": "deepseek-coder",
                    "name": "DeepSeek Coder",
                    "family": "deepseek",
                    "capabilities": ["code"],
                    "context_length": 16384,
                    "parameters": "33B"
                },
            ],
            discover=lambda: self.discover_models("deepseek"),
            validate=lambda config: self.validate_api_key("deepseek", config),
            health_check=lambda: self.health_check("deepseek"),
            is_llm_provider=True,
            provider_type="remote"
        )
        self.registry.register_provider(deepseek_spec)
        
        # HuggingFace Provider (hybrid - can work with or without API key)
        huggingface_spec = DynamicProviderSpec(
            name="huggingface",
            requires_api_key=False,  # Optional for better rate limits
            description="HuggingFace Hub models and local execution",
            category="LLM",
            capabilities={"local_execution", "model_download", "embeddings"},
            api_base_url="https://huggingface.co/api",
            api_key_env_var="HUGGINGFACE_API_KEY",
            api_key_validation_endpoint="/whoami",
            model_discovery_endpoint="/models",
            model_list_parser=self._parse_huggingface_models,
            fallback_models=[
                {
                    "id": "microsoft/DialoGPT-large",
                    "name": "DialoGPT Large",
                    "family": "gpt",
                    "format": "safetensors",
                    "parameters": "345M",
                    "context_length": 1024
                },
                {
                    "id": "microsoft/DialoGPT-medium",
                    "name": "DialoGPT Medium",
                    "family": "gpt",
                    "format": "safetensors", 
                    "parameters": "117M",
                    "context_length": 1024
                },
            ],
            discover=lambda: self.discover_models("huggingface"),
            validate=lambda config: self.validate_api_key("huggingface", config),
            health_check=lambda: self.health_check("huggingface"),
            is_llm_provider=True,
            provider_type="hybrid"
        )
        self.registry.register_provider(huggingface_spec)
        
        # Local Provider (for local model files)
        local_spec = DynamicProviderSpec(
            name="local",
            requires_api_key=False,
            description="Local model files (GGUF, safetensors, etc.)",
            category="LLM",
            capabilities={"local_execution", "privacy"},
            discover=lambda: self.discover_models("local"),
            validate=lambda config: {"valid": True, "message": "Local provider always available"},
            health_check=lambda: self.health_check("local"),
            fallback_models=[],  # Will be populated by scanning local files
            is_llm_provider=True,
            provider_type="local"
        )
        self.registry.register_provider(local_spec)
        
        # CopilotKit (NOT an LLM provider - UI framework)
        # Note: CopilotKit is registered separately in the UI_FRAMEWORK category
        # and is explicitly excluded from LLM provider lists
        copilotkit_spec = DynamicProviderSpec(
            name="copilotkit",
            requires_api_key=False,
            description="AI-powered development assistance framework (not an LLM provider)",
            category="UI_FRAMEWORK",  # Not LLM!
            capabilities={"ui_assistance", "code_suggestions"},
            discover=lambda: [],  # No models to discover
            validate=lambda config: {"valid": True, "message": "CopilotKit is a UI framework"},
            health_check=lambda: {"status": "healthy", "message": "CopilotKit UI framework available"},
            fallback_models=[],
            is_llm_provider=False,  # Explicitly not an LLM provider
            provider_type="ui_framework"
        )
        self.registry.register_provider(copilotkit_spec)
    
    # ---------- Model Discovery ----------
    
    async def discover_models(self, provider_name: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discover available models from a provider.
        
        Args:
            provider_name: Name of the provider
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            List of model dictionaries
        """
        spec = self.registry.get_provider_spec(provider_name)
        if not isinstance(spec, DynamicProviderSpec):
            logger.warning(f"Provider {provider_name} is not a dynamic provider")
            return []
        
        # Check cache first
        if not force_refresh and self._is_cache_valid(spec):
            logger.debug(f"Using cached models for {provider_name}")
            return spec.cached_models
        
        # Ensure we don't have concurrent discovery for the same provider
        if provider_name not in self._discovery_locks:
            self._discovery_locks[provider_name] = asyncio.Lock()
        
        async with self._discovery_locks[provider_name]:
            # Double-check cache after acquiring lock
            if not force_refresh and self._is_cache_valid(spec):
                return spec.cached_models
            
            try:
                logger.info(f"Discovering models for provider: {provider_name}")
                
                if provider_name == "local":
                    models = await self._discover_local_models()
                else:
                    models = await self._discover_remote_models(spec)
                
                # Update cache
                spec.cached_models = models
                spec.last_discovery = time.time()
                
                logger.info(f"Discovered {len(models)} models for {provider_name}")
                return models
                
            except Exception as e:
                logger.warning(f"Model discovery failed for {provider_name}: {e}")
                logger.info(f"Falling back to curated models for {provider_name}")
                return spec.fallback_models
    
    def _is_cache_valid(self, spec: DynamicProviderSpec) -> bool:
        """Check if the model cache is still valid."""
        if not spec.last_discovery or not spec.cached_models:
            return False
        
        age = time.time() - spec.last_discovery
        return age < spec.discovery_cache_ttl
    
    async def _discover_local_models(self) -> List[Dict[str, Any]]:
        """Discover local model files."""
        try:
            from ai_karen_engine.inference.model_store import ModelStore
            
            model_store = ModelStore()
            local_models = model_store.scan_local_models()
            
            models = []
            for model in local_models:
                models.append({
                    "id": model.id,
                    "name": model.name or model.id,
                    "family": model.family or "unknown",
                    "format": model.format or "unknown",
                    "size": model.size,
                    "parameters": model.parameters,
                    "quantization": model.quantization,
                    "context_length": model.context_length,
                    "local_path": model.local_path,
                    "capabilities": list(model.capabilities) if model.capabilities else []
                })
            
            return models
            
        except Exception as e:
            logger.warning(f"Failed to discover local models: {e}")
            return []
    
    async def _discover_remote_models(self, spec: DynamicProviderSpec) -> List[Dict[str, Any]]:
        """Discover models from a remote provider API."""
        if not spec.model_discovery_endpoint or not spec.model_list_parser:
            logger.debug(f"No discovery endpoint configured for {spec.name}")
            return spec.fallback_models
        
        try:
            import aiohttp
            import os
            
            # Get API key from environment
            api_key = None
            if spec.api_key_env_var:
                api_key = os.getenv(spec.api_key_env_var)
            
            if spec.requires_api_key and not api_key:
                logger.debug(f"No API key available for {spec.name}, using fallback models")
                return spec.fallback_models
            
            # Prepare headers
            headers = {"User-Agent": "Kari-AI/1.0"}
            if api_key:
                if spec.name == "openai":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif spec.name == "gemini":
                    # Gemini uses API key as query parameter
                    pass
                elif spec.name == "deepseek":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif spec.name == "huggingface":
                    headers["Authorization"] = f"Bearer {api_key}"
            
            # Build URL
            url = f"{spec.api_base_url}{spec.model_discovery_endpoint}"
            if spec.name == "gemini" and api_key:
                url += f"?key={api_key}"
            
            # Make request with timeout
            timeout = aiohttp.ClientTimeout(total=spec.validation_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = spec.model_list_parser(data)
                        logger.info(f"Discovered {len(models)} models from {spec.name}")
                        return models
                    else:
                        logger.warning(f"API request failed for {spec.name}: {response.status}")
                        return spec.fallback_models
            
        except ImportError:
            logger.warning("aiohttp not available, using fallback models")
            return spec.fallback_models
        except Exception as e:
            logger.warning(f"Remote model discovery failed for {spec.name}: {e}")
            return spec.fallback_models
    
    # ---------- Model List Parsers ----------
    
    def _parse_openai_models(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse OpenAI models API response."""
        models = []
        
        for model_data in response_data.get("data", []):
            model_id = model_data.get("id", "")
            
            # Filter for GPT models only
            if "gpt" not in model_id.lower():
                continue
            
            models.append({
                "id": model_id,
                "name": model_id.replace("-", " ").title(),
                "family": "gpt",
                "capabilities": ["text"],
                "context_length": self._estimate_context_length(model_id),
                "parameters": "Unknown"
            })
        
        return models
    
    def _parse_gemini_models(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Gemini models API response."""
        models = []
        
        for model_data in response_data.get("models", []):
            model_name = model_data.get("name", "").replace("models/", "")
            
            # Filter for generative models
            if "generateContent" not in model_data.get("supportedGenerationMethods", []):
                continue
            
            models.append({
                "id": model_name,
                "name": model_name.replace("-", " ").title(),
                "family": "gemini",
                "capabilities": ["text", "vision"] if "vision" in model_name else ["text"],
                "context_length": self._estimate_context_length(model_name),
                "parameters": "Unknown"
            })
        
        return models
    
    def _parse_deepseek_models(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse DeepSeek models API response."""
        models = []
        
        for model_data in response_data.get("data", []):
            model_id = model_data.get("id", "")
            
            models.append({
                "id": model_id,
                "name": model_id.replace("-", " ").title(),
                "family": "deepseek",
                "capabilities": ["text", "code"] if "coder" in model_id else ["text"],
                "context_length": self._estimate_context_length(model_id),
                "parameters": "Unknown"
            })
        
        return models
    
    def _parse_huggingface_models(self, response_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse HuggingFace models API response."""
        models = []
        
        for model_data in response_data:
            model_id = model_data.get("id", "")
            
            # Filter for text generation models
            if not any(tag in model_data.get("tags", []) for tag in ["text-generation", "conversational"]):
                continue
            
            models.append({
                "id": model_id,
                "name": model_data.get("id", model_id),
                "family": self._extract_model_family(model_id),
                "format": "safetensors",  # Most HF models use safetensors
                "capabilities": ["text"],
                "context_length": 2048,  # Default assumption
                "parameters": self._extract_parameters(model_data),
                "downloads": model_data.get("downloads", 0),
                "likes": model_data.get("likes", 0)
            })
        
        # Sort by popularity (downloads + likes)
        models.sort(key=lambda m: m.get("downloads", 0) + m.get("likes", 0), reverse=True)
        
        return models[:50]  # Limit to top 50 models
    
    def _estimate_context_length(self, model_id: str) -> int:
        """Estimate context length based on model ID."""
        model_id_lower = model_id.lower()
        
        if "gpt-4" in model_id_lower:
            return 128000 if "turbo" in model_id_lower else 8192
        elif "gpt-3.5" in model_id_lower:
            return 16385 if "16k" in model_id_lower else 4096
        elif "gemini-1.5-pro" in model_id_lower:
            return 2097152
        elif "gemini-1.5-flash" in model_id_lower:
            return 1048576
        elif "deepseek" in model_id_lower:
            return 32768
        else:
            return 4096  # Default
    
    def _extract_model_family(self, model_id: str) -> str:
        """Extract model family from model ID."""
        model_id_lower = model_id.lower()
        
        if "llama" in model_id_lower:
            return "llama"
        elif "mistral" in model_id_lower:
            return "mistral"
        elif "qwen" in model_id_lower:
            return "qwen"
        elif "phi" in model_id_lower:
            return "phi"
        elif "gemma" in model_id_lower:
            return "gemma"
        elif "gpt" in model_id_lower:
            return "gpt"
        else:
            return "unknown"
    
    def _extract_parameters(self, model_data: Dict[str, Any]) -> str:
        """Extract parameter count from model data."""
        # Try to extract from model card or config
        config = model_data.get("config", {})
        if "num_parameters" in config:
            params = config["num_parameters"]
            if params > 1e9:
                return f"{params/1e9:.1f}B"
            elif params > 1e6:
                return f"{params/1e6:.1f}M"
        
        # Try to extract from model ID
        model_id = model_data.get("id", "").lower()
        if "7b" in model_id:
            return "7B"
        elif "13b" in model_id:
            return "13B"
        elif "70b" in model_id:
            return "70B"
        elif "3b" in model_id:
            return "3B"
        
        return "Unknown"
    
    # ---------- API Key Validation ----------
    
    async def validate_api_key(self, provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate API key for a provider.
        
        Args:
            provider_name: Name of the provider
            config: Configuration including API key
            
        Returns:
            Validation result with status and message
        """
        spec = self.registry.get_provider_spec(provider_name)
        if not isinstance(spec, DynamicProviderSpec):
            return {"valid": False, "message": f"Provider {provider_name} is not a dynamic provider"}
        
        api_key = config.get("api_key", "")
        if not api_key and spec.requires_api_key:
            return {"valid": False, "message": "API key is required"}
        
        if not spec.requires_api_key:
            return {"valid": True, "message": "No API key required"}
        
        # Check validation cache
        cache_key = f"{provider_name}:{hash(api_key)}"
        if cache_key in self._validation_cache:
            cached_result = self._validation_cache[cache_key]
            # Cache valid for 5 minutes
            if time.time() - cached_result["timestamp"] < 300:
                return {
                    "valid": cached_result["valid"],
                    "message": cached_result["message"]
                }
        
        try:
            logger.debug(f"Validating API key for {provider_name}")
            
            # Perform actual validation (placeholder for now)
            result = await self._perform_api_key_validation(spec, api_key)
            
            # Cache result
            self._validation_cache[cache_key] = {
                "valid": result["valid"],
                "message": result["message"],
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"API key validation failed for {provider_name}: {e}")
            return {"valid": False, "message": f"Validation failed: {str(e)}"}
    
    async def _perform_api_key_validation(self, spec: DynamicProviderSpec, api_key: str) -> Dict[str, Any]:
        """Perform actual API key validation."""
        if not spec.api_key_validation_endpoint:
            return {"valid": True, "message": "No validation endpoint configured"}
        
        try:
            import aiohttp
            
            # Prepare headers
            headers = {"User-Agent": "Kari-AI/1.0"}
            if spec.name == "openai":
                headers["Authorization"] = f"Bearer {api_key}"
            elif spec.name == "deepseek":
                headers["Authorization"] = f"Bearer {api_key}"
            elif spec.name == "huggingface":
                headers["Authorization"] = f"Bearer {api_key}"
            
            # Build URL
            url = f"{spec.api_base_url}{spec.api_key_validation_endpoint}"
            if spec.name == "gemini":
                url += f"?key={api_key}"
            
            # Make validation request with timeout
            timeout = aiohttp.ClientTimeout(total=spec.validation_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        # Additional validation based on response content
                        if spec.name == "openai":
                            data = await response.json()
                            if "data" in data and isinstance(data["data"], list):
                                return {"valid": True, "message": "API key is valid"}
                        elif spec.name == "gemini":
                            data = await response.json()
                            if "models" in data:
                                return {"valid": True, "message": "API key is valid"}
                        elif spec.name == "deepseek":
                            data = await response.json()
                            if "data" in data:
                                return {"valid": True, "message": "API key is valid"}
                        elif spec.name == "huggingface":
                            data = await response.json()
                            if "name" in data:  # /whoami endpoint returns user info
                                return {"valid": True, "message": "API key is valid"}
                        
                        return {"valid": True, "message": "API key is valid"}
                    
                    elif response.status == 401:
                        return {"valid": False, "message": "Invalid API key"}
                    elif response.status == 403:
                        return {"valid": False, "message": "API key lacks required permissions"}
                    elif response.status == 429:
                        return {"valid": False, "message": "Rate limit exceeded, but API key appears valid"}
                    else:
                        return {"valid": False, "message": f"Validation failed with status {response.status}"}
            
        except ImportError:
            logger.warning("aiohttp not available for API key validation")
            return {"valid": True, "message": "Cannot validate - aiohttp not available"}
        except asyncio.TimeoutError:
            return {"valid": False, "message": "Validation request timed out"}
        except Exception as e:
            return {"valid": False, "message": f"Validation request failed: {str(e)}"}
    
    # ---------- Health Monitoring ----------
    
    def health_check(self, provider_name: str) -> Dict[str, Any]:
        """Perform health check on a provider."""
        spec = self.registry.get_provider_spec(provider_name)
        if not spec:
            return {"status": "not_found", "message": f"Provider {provider_name} not found"}
        
        try:
            start_time = time.time()
            
            if provider_name == "local":
                # Local provider is always healthy if we can scan for models
                try:
                    from ai_karen_engine.inference.model_store import ModelStore
                    model_store = ModelStore()
                    local_models = model_store.scan_local_models()
                    return {
                        "status": "healthy",
                        "message": f"Local provider available with {len(local_models)} models",
                        "response_time": time.time() - start_time,
                        "model_count": len(local_models)
                    }
                except Exception as e:
                    return {
                        "status": "degraded",
                        "message": f"Local provider available but model scanning failed: {e}",
                        "response_time": time.time() - start_time
                    }
            
            elif not isinstance(spec, DynamicProviderSpec):
                return {
                    "status": "unknown",
                    "message": "Not a dynamic provider",
                    "response_time": time.time() - start_time
                }
            
            else:
                # For remote providers, check API availability
                import os
                
                # Check if API key is available
                api_key = None
                if spec.api_key_env_var:
                    api_key = os.getenv(spec.api_key_env_var)
                
                if spec.requires_api_key and not api_key:
                    return {
                        "status": "unavailable",
                        "message": f"API key not configured (set {spec.api_key_env_var})",
                        "response_time": time.time() - start_time
                    }
                
                # Try to make a simple API call to check connectivity
                try:
                    import asyncio
                    
                    async def check_api():
                        if api_key:
                            validation_result = await self._perform_api_key_validation(spec, api_key)
                            if validation_result["valid"]:
                                return {
                                    "status": "healthy",
                                    "message": f"{provider_name} API is accessible",
                                    "response_time": time.time() - start_time
                                }
                            else:
                                return {
                                    "status": "unhealthy",
                                    "message": f"API key validation failed: {validation_result['message']}",
                                    "response_time": time.time() - start_time
                                }
                        else:
                            return {
                                "status": "healthy",
                                "message": f"{provider_name} provider configured (no API key required)",
                                "response_time": time.time() - start_time
                            }
                    
                    # Run async check
                    try:
                        loop = asyncio.get_event_loop()
                        return loop.run_until_complete(check_api())
                    except RuntimeError:
                        # No event loop running, create one
                        return asyncio.run(check_api())
                        
                except ImportError:
                    return {
                        "status": "degraded",
                        "message": f"{provider_name} configured but cannot validate (aiohttp not available)",
                        "response_time": time.time() - start_time
                    }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
                "response_time": time.time() - start_time
            }
    
    # ---------- Provider Filtering ----------
    
    def get_llm_providers(self, healthy_only: bool = False) -> List[str]:
        """Get list of LLM providers (excludes CopilotKit and other non-LLM providers)."""
        llm_providers = []
        
        for provider_name in self.registry.list_providers():
            spec = self.registry.get_provider_spec(provider_name)
            if isinstance(spec, DynamicProviderSpec) and spec.is_llm_provider:
                if healthy_only:
                    health = self.registry.get_health_status(f"provider:{provider_name}")
                    if health and health.status not in ["healthy", "unknown"]:
                        continue
                
                llm_providers.append(provider_name)
        
        return llm_providers
    
    def get_non_llm_providers(self) -> List[str]:
        """Get list of non-LLM providers (like CopilotKit)."""
        non_llm_providers = []
        
        for provider_name in self.registry.list_providers():
            spec = self.registry.get_provider_spec(provider_name)
            if isinstance(spec, DynamicProviderSpec) and not spec.is_llm_provider:
                non_llm_providers.append(provider_name)
        
        return non_llm_providers
    
    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get comprehensive provider information."""
        spec = self.registry.get_provider_spec(provider_name)
        if not isinstance(spec, DynamicProviderSpec):
            return {}
        
        health = self.registry.get_health_status(f"provider:{provider_name}")
        
        return {
            "name": spec.name,
            "description": spec.description,
            "category": spec.category,
            "requires_api_key": spec.requires_api_key,
            "capabilities": list(spec.capabilities),
            "is_llm_provider": spec.is_llm_provider,
            "provider_type": spec.provider_type,
            "health_status": health.status if health else "unknown",
            "error_message": health.error_message if health else None,
            "last_health_check": health.last_check if health else None,
            "cached_models_count": len(spec.cached_models),
            "last_discovery": spec.last_discovery,
            "api_base_url": spec.api_base_url
        }
    
    # ---------- Cleanup ----------
    
    def shutdown(self) -> None:
        """Shutdown the provider manager and cleanup resources."""
        self._executor.shutdown(wait=True)
        logger.info("Dynamic provider manager shutdown complete")


# -----------------------------
# Global Manager Instance
# -----------------------------

_global_manager: Optional[DynamicProviderManager] = None


def get_dynamic_provider_manager() -> DynamicProviderManager:
    """Get the global dynamic provider manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = DynamicProviderManager()
    return _global_manager


__all__ = [
    "DynamicProviderSpec",
    "DynamicProviderManager", 
    "get_dynamic_provider_manager",
]