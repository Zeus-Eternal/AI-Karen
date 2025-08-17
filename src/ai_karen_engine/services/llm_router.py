"""
LLM Router Service
Manages LLM provider selection, routing, and fallback logic with local-first priority
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from enum import Enum

from ai_karen_engine.integrations.llm_registry import get_registry, LLMRegistry
from ai_karen_engine.integrations.llm_utils import LLMProviderBase

logger = logging.getLogger(__name__)


class ProviderPriority(Enum):
    """Provider priority levels"""
    LOCAL = 1      # Ollama, llama.cpp
    REMOTE = 2     # OpenAI, Anthropic, Gemini
    FALLBACK = 3   # Last resort providers


@dataclass
class ProviderHealth:
    """Provider health status"""
    name: str
    is_healthy: bool
    last_check: float
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0


@dataclass
class ChatRequest:
    """Chat request model for LLM Router"""
    message: str
    context: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    memory_context: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    preferred_model: Optional[str] = None
    platform: str = "web"
    conversation_id: Optional[str] = None
    stream: bool = True
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class LLMRouter:
    """
    LLM Router with local-first provider selection and health monitoring
    """
    
    def __init__(self, registry: Optional[LLMRegistry] = None):
        """Initialize LLM Router"""
        self.registry = registry or get_registry()
        self.provider_health: Dict[str, ProviderHealth] = {}
        self.health_check_interval = 300  # 5 minutes
        self.max_consecutive_failures = 3
        self.response_timeout = 30  # seconds
        
        # Provider priority mapping
        self.provider_priorities = {
            "ollama": ProviderPriority.LOCAL,
            "llama_cpp": ProviderPriority.LOCAL,
            "openai": ProviderPriority.REMOTE,
            "anthropic": ProviderPriority.REMOTE,
            "gemini": ProviderPriority.REMOTE,
            "deepseek": ProviderPriority.REMOTE,
            "huggingface": ProviderPriority.FALLBACK,
            "copilotkit": ProviderPriority.REMOTE,
        }
        
        # Initialize health monitoring
        self._initialize_health_monitoring()
    
    def _initialize_health_monitoring(self):
        """Initialize health monitoring for all providers"""
        for provider_name in self.registry.list_providers():
            self.provider_health[provider_name] = ProviderHealth(
                name=provider_name,
                is_healthy=True,  # Assume healthy initially
                last_check=0,
                consecutive_failures=0
            )
    
    async def select_provider(
        self,
        request: ChatRequest,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple[str, Optional[str]]]:
        """Select the best available provider based on local-first priority."""

        user_preferences = user_preferences or {}
        preferred_provider = user_preferences.get("preferred_llm_provider")
        preferred_model = request.preferred_model or user_preferences.get("preferred_model")

        # If model specified with provider prefix, split it
        if preferred_model and ":" in preferred_model:
            provider_part, model_part = preferred_model.split(":", 1)
            preferred_provider = preferred_provider or provider_part
            preferred_model = model_part

        # Validate preferred provider/model combination
        if preferred_provider and preferred_model:
            info = self.registry.get_provider_info(preferred_provider)
            if info and info.get("default_model") == preferred_model and await self._is_provider_healthy(preferred_provider):
                logger.info(
                    "Using user preferred provider/model: %s/%s",
                    preferred_provider,
                    preferred_model,
                )
                return preferred_provider, preferred_model
            else:
                logger.warning(
                    "Preferred model %s not available for provider %s", preferred_model, preferred_provider
                )
                preferred_provider = None
                preferred_model = None

        # If only preferred model specified, find provider by model
        if preferred_model and not preferred_provider:
            for name in self.registry.list_providers():
                info = self.registry.get_provider_info(name)
                if info and info.get("default_model") == preferred_model:
                    if await self._is_provider_healthy(name):
                        logger.info("Selected provider %s for model %s", name, preferred_model)
                        return name, preferred_model
            logger.warning("Preferred model %s not available; falling back", preferred_model)
            preferred_model = None

        # Preferred provider without model
        if preferred_provider and await self._is_provider_healthy(preferred_provider):
            logger.info(f"Using user preferred provider: {preferred_provider}")
            info = self.registry.get_provider_info(preferred_provider)
            model_name = info.get("default_model") if info else None
            return preferred_provider, model_name

        # Get available providers sorted by priority
        available_providers = await self._get_available_providers_by_priority()

        # Filter by requirements
        suitable_providers: List[str] = []
        for provider_name in available_providers:
            if await self._meets_requirements(provider_name, request):
                suitable_providers.append(provider_name)

        if not suitable_providers:
            logger.warning("No suitable providers found for request")
            return None

        selected_provider = suitable_providers[0]
        info = self.registry.get_provider_info(selected_provider)
        model_name = info.get("default_model") if info else None
        logger.info(f"Selected provider: {selected_provider}")
        return selected_provider, model_name
    
    async def _get_available_providers_by_priority(self) -> List[str]:
        """Get available providers sorted by priority (local first)"""
        providers_by_priority = {
            ProviderPriority.LOCAL: [],
            ProviderPriority.REMOTE: [],
            ProviderPriority.FALLBACK: []
        }
        
        # Categorize providers by priority
        for provider_name in self.registry.list_providers():
            if await self._is_provider_healthy(provider_name):
                priority = self.provider_priorities.get(provider_name, ProviderPriority.FALLBACK)
                providers_by_priority[priority].append(provider_name)
        
        # Return sorted list (local first)
        sorted_providers = []
        for priority in [ProviderPriority.LOCAL, ProviderPriority.REMOTE, ProviderPriority.FALLBACK]:
            sorted_providers.extend(providers_by_priority[priority])
        
        return sorted_providers
    
    async def _meets_requirements(self, provider_name: str, request: ChatRequest) -> bool:
        """Check if provider meets request requirements"""
        provider_info = self.registry.get_provider_info(provider_name)
        if not provider_info:
            return False
        
        # Check streaming requirement
        if request.stream and not provider_info.get("supports_streaming", False):
            return False
        
        # Check if API key is required and available
        if provider_info.get("requires_api_key", False):
            # TODO: Check if API key is configured
            pass
        
        return True
    
    async def _is_provider_healthy(self, provider_name: str) -> bool:
        """Check if provider is healthy"""
        if provider_name not in self.provider_health:
            return False
        
        health = self.provider_health[provider_name]
        
        # Check if health check is recent enough
        if time.time() - health.last_check > self.health_check_interval:
            await self._perform_health_check(provider_name)
        
        return health.is_healthy and health.consecutive_failures < self.max_consecutive_failures
    
    async def _perform_health_check(self, provider_name: str):
        """Perform health check on a provider"""
        try:
            start_time = time.time()
            health_result = self.registry.health_check(provider_name)
            response_time = time.time() - start_time
            
            health = self.provider_health[provider_name]
            health.last_check = time.time()
            health.response_time = response_time
            
            if health_result.get("status") == "healthy":
                health.is_healthy = True
                health.consecutive_failures = 0
                health.error_message = None
            else:
                health.is_healthy = False
                health.consecutive_failures += 1
                health.error_message = health_result.get("error", "Unknown error")
            
            logger.debug(f"Health check for {provider_name}: {health_result}")
            
        except Exception as e:
            health = self.provider_health[provider_name]
            health.last_check = time.time()
            health.is_healthy = False
            health.consecutive_failures += 1
            health.error_message = str(e)
            
            logger.error(f"Health check failed for {provider_name}: {e}")
    
    async def process_chat_request(
        self,
        request: ChatRequest,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Process chat request with automatic provider selection and fallback
        """
        selection = await self.select_provider(request, user_preferences)
        if not selection:
            raise RuntimeError("No suitable provider available")
        provider_name, model_name = selection
        
        # Try primary provider
        try:
            async for chunk in self._process_with_provider(provider_name, request, model_name):
                yield chunk
            return
        except Exception as e:
            logger.warning(f"Provider {provider_name} failed: {e}")
            await self._mark_provider_unhealthy(provider_name, str(e))
        
        # Try fallback providers
        fallback_providers = await self._get_fallback_providers(provider_name, request)
        for fallback_provider in fallback_providers:
            try:
                logger.info(f"Trying fallback provider: {fallback_provider}")
                async for chunk in self._process_with_provider(fallback_provider, request):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Fallback provider {fallback_provider} failed: {e}")
                await self._mark_provider_unhealthy(fallback_provider, str(e))
        
        # If all providers failed
        raise RuntimeError("All providers failed to process the request")
    
    async def _process_with_provider(
        self,
        provider_name: str,
        request: ChatRequest,
        model_name: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Process request with a specific provider"""
        if model_name:
            provider = self.registry.get_provider(provider_name, model=model_name)
        else:
            provider = self.registry.get_provider(provider_name)
        if not provider:
            raise RuntimeError(f"Could not get provider instance: {provider_name}")
        
        # Prepare provider-specific parameters
        provider_params = {
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        
        # Remove None values
        provider_params = {k: v for k, v in provider_params.items() if v is not None}
        
        if request.stream:
            # Stream response
            async for chunk in provider.stream_response(request.message, **provider_params):
                yield chunk
        else:
            # Non-streaming response
            response = await provider.generate_response(request.message, **provider_params)
            yield response
    
    async def _get_fallback_providers(
        self,
        failed_provider: str,
        request: ChatRequest
    ) -> List[str]:
        """Get fallback providers excluding the failed one"""
        all_providers = await self._get_available_providers_by_priority()
        fallback_providers = []
        
        for provider_name in all_providers:
            if (provider_name != failed_provider and 
                await self._is_provider_healthy(provider_name) and
                await self._meets_requirements(provider_name, request)):
                fallback_providers.append(provider_name)
        
        return fallback_providers[:2]  # Limit to 2 fallback attempts
    
    async def _mark_provider_unhealthy(self, provider_name: str, error_message: str):
        """Mark provider as unhealthy"""
        if provider_name in self.provider_health:
            health = self.provider_health[provider_name]
            health.is_healthy = False
            health.consecutive_failures += 1
            health.error_message = error_message
            health.last_check = time.time()
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            "providers": {},
            "health_summary": {
                "healthy": 0,
                "unhealthy": 0,
                "total": len(self.provider_health)
            }
        }
        
        for provider_name, health in self.provider_health.items():
            provider_info = self.registry.get_provider_info(provider_name)
            priority = self.provider_priorities.get(provider_name, ProviderPriority.FALLBACK)
            
            status["providers"][provider_name] = {
                "is_healthy": health.is_healthy,
                "consecutive_failures": health.consecutive_failures,
                "last_check": health.last_check,
                "response_time": health.response_time,
                "error_message": health.error_message,
                "priority": priority.name,
                "supports_streaming": provider_info.get("supports_streaming", False) if provider_info else False,
                "requires_api_key": provider_info.get("requires_api_key", False) if provider_info else False,
            }
            
            if health.is_healthy:
                status["health_summary"]["healthy"] += 1
            else:
                status["health_summary"]["unhealthy"] += 1
        
        return status
    
    async def refresh_provider_health(self):
        """Refresh health status for all providers"""
        logger.info("Refreshing provider health status")
        
        tasks = []
        for provider_name in self.provider_health.keys():
            tasks.append(self._perform_health_check(provider_name))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Provider health refresh completed")
    
    @classmethod
    def default(cls) -> 'LLMRouter':
        """Create default LLM Router instance"""
        return cls()


# Global router instance
_router_instance: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get global LLM Router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter.default()
    return _router_instance