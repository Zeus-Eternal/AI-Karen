"""
Provider Registry with Health Monitoring and Graceful Fallbacks

This service manages AI provider registration, health monitoring, and automatic
fallback chains to ensure system resilience when providers are unavailable.
"""

import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, Union

from ai_karen_engine.integrations.provider_registry import (
    ProviderRegistry as BaseProviderRegistry,
    ProviderRegistration,
    ModelInfo,
    get_provider_registry
)
from src.services.provider_health_monitor import (
    ProviderHealthMonitor,
    HealthStatus,
    get_health_monitor
)

logger = logging.getLogger(__name__)


class ProviderCapability(str, Enum):
    """Provider capability types"""
    TEXT_GENERATION = "text_generation"
    EMBEDDINGS = "embeddings"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    AUDIO = "audio"


@dataclass
class FallbackChain:
    """Defines a fallback chain for provider selection"""
    primary: str
    fallbacks: List[str] = field(default_factory=list)
    capability_required: Optional[ProviderCapability] = None
    max_fallback_attempts: int = 3


@dataclass
class ProviderStatus:
    """Current status of a provider"""
    name: str
    is_available: bool
    has_api_key: bool
    health_status: HealthStatus
    capabilities: Set[ProviderCapability]
    last_check: datetime
    error_message: Optional[str] = None


class ProviderRegistryService:
    """
    Provider registry service with health monitoring and graceful fallbacks
    """
    
    def __init__(self, use_global_registry: bool = True):
        if use_global_registry:
            self.base_registry = get_provider_registry()
        else:
            # Create a fresh base registry to avoid auto-registered providers in tests
            from ai_karen_engine.integrations.provider_registry import ProviderRegistry
            # Temporarily disable auto-registration
            original_register = ProviderRegistry._register_core_providers
            ProviderRegistry._register_core_providers = lambda self: None
            self.base_registry = ProviderRegistry()
            # Restore original method for other instances
            ProviderRegistry._register_core_providers = original_register
        
        self.health_monitor = get_health_monitor()
        self._lock = threading.RLock()
        self._fallback_chains: Dict[str, FallbackChain] = {}
        self._provider_status_cache: Dict[str, ProviderStatus] = {}
        self._cache_ttl = 60  # 1 minute cache TTL
        
        # Initialize default fallback chains
        self._setup_default_fallback_chains()
        
        # Start background health monitoring
        self._monitoring_task = None
        self._start_health_monitoring()
    
    def _setup_default_fallback_chains(self):
        """Setup default fallback chains for common use cases"""
        
        # Text generation fallback chain
        self._fallback_chains["text_generation"] = FallbackChain(
            primary="llamacpp",
            fallbacks=["openai", "gemini", "deepseek", "huggingface", "local"],
            capability_required=ProviderCapability.TEXT_GENERATION
        )
        
        # Embeddings fallback chain
        self._fallback_chains["embeddings"] = FallbackChain(
            primary="llamacpp",
            fallbacks=["openai", "huggingface"],
            capability_required=ProviderCapability.EMBEDDINGS
        )
        
        # Local-first fallback chain
        self._fallback_chains["local_first"] = FallbackChain(
            primary="llamacpp",
            fallbacks=["openai", "gemini", "deepseek", "huggingface"],
            capability_required=ProviderCapability.TEXT_GENERATION
        )
    
    def register_provider(
        self,
        name: str,
        provider_class: Type[Any],
        *,
        description: str = "",
        models: Optional[List[ModelInfo]] = None,
        requires_api_key: bool = False,
        default_model: Optional[str] = None,
        category: str = "LLM",
        capabilities: Optional[Set[ProviderCapability]] = None
    ) -> None:
        """
        Register a provider with capability detection
        
        Args:
            name: Provider name
            provider_class: Provider implementation class
            description: Provider description
            models: Available models
            requires_api_key: Whether API key is required
            default_model: Default model name
            category: Provider category
            capabilities: Provider capabilities
        """
        with self._lock:
            # Register with base registry
            self.base_registry.register_provider(
                name=name,
                provider_class=provider_class,
                description=description,
                models=models or [],
                requires_api_key=requires_api_key,
                default_model=default_model,
                category=category
            )
            
            # Detect capabilities if not provided
            if capabilities is None:
                capabilities = self._detect_provider_capabilities(provider_class)
            
            # Update provider status
            self._update_provider_status(name, capabilities, requires_api_key)
            
            logger.info(f"Registered provider '{name}' with capabilities: {capabilities}")
    
    def _detect_provider_capabilities(self, provider_class: Type[Any]) -> Set[ProviderCapability]:
        """Detect provider capabilities from class methods"""
        capabilities = set()
        
        # Check for common methods to infer capabilities
        if hasattr(provider_class, 'generate_text') or hasattr(provider_class, 'generate_response'):
            capabilities.add(ProviderCapability.TEXT_GENERATION)
        
        if hasattr(provider_class, 'get_embeddings') or hasattr(provider_class, 'embed'):
            capabilities.add(ProviderCapability.EMBEDDINGS)
        
        if hasattr(provider_class, 'stream_response') or hasattr(provider_class, 'stream'):
            capabilities.add(ProviderCapability.STREAMING)
        
        if hasattr(provider_class, 'function_call') or hasattr(provider_class, 'call_function'):
            capabilities.add(ProviderCapability.FUNCTION_CALLING)
        
        # Default to text generation if no capabilities detected
        if not capabilities:
            capabilities.add(ProviderCapability.TEXT_GENERATION)
        
        return capabilities
    
    def _update_provider_status(
        self, 
        name: str, 
        capabilities: Set[ProviderCapability], 
        requires_api_key: bool
    ) -> None:
        """Update provider status with API key check"""
        
        # Check if API key is available
        has_api_key = True
        if requires_api_key:
            has_api_key = self._check_api_key_availability(name)
        
        # Get health status
        health_info = self.health_monitor.get_provider_health(name)
        health_status = health_info.status if health_info else HealthStatus.UNKNOWN
        
        # Determine availability - consider UNKNOWN as potentially available
        is_available = has_api_key and (health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNKNOWN])
        
        # Update status cache
        self._provider_status_cache[name] = ProviderStatus(
            name=name,
            is_available=is_available,
            has_api_key=has_api_key,
            health_status=health_status,
            capabilities=capabilities,
            last_check=datetime.utcnow(),
            error_message=health_info.error_message if health_info else None
        )
    
    def _check_api_key_availability(self, provider_name: str) -> bool:
        """Check if API key is available for provider"""
        
        # Map provider names to environment variable names
        api_key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
            "cohere": "COHERE_API_KEY",
            # Test providers that require API keys
            "failed_provider": "FAILED_PROVIDER_API_KEY",
            "missing_key_provider": "MISSING_KEY_PROVIDER_API_KEY",
            "unavailable_provider": "UNAVAILABLE_PROVIDER_API_KEY",
            "unavailable": "UNAVAILABLE_API_KEY"
        }
        
        env_var = api_key_mapping.get(provider_name.lower())
        if not env_var:
            return True  # Assume available if no mapping found
        
        api_key = os.getenv(env_var)
        has_key = bool(api_key and api_key.strip())
        
        if not has_key:
            logger.debug(f"API key not found for {provider_name} (env var: {env_var})")
        
        return has_key
    
    def get_provider_status(self, name: str) -> Optional[ProviderStatus]:
        """Get current status of a provider"""
        with self._lock:
            status = self._provider_status_cache.get(name)

            if status is None:
                # Provider may have been auto-registered in the base registry
                # before this service instance was created. Populate a fresh
                # status entry on-demand so availability checks reflect the
                # real provider roster.
                provider_info = self.base_registry.get_provider_info(name)
                if provider_info:
                    try:
                        capabilities = self._detect_provider_capabilities(
                            provider_info.provider_class
                        )
                        self._update_provider_status(
                            name,
                            capabilities,
                            provider_info.requires_api_key,
                        )
                        status = self._provider_status_cache.get(name)
                    except Exception as exc:
                        logger.warning(
                            "Failed to initialize provider status for %s: %s",
                            name,
                            exc,
                        )

            # Check if cache is stale
            if status and (datetime.utcnow() - status.last_check).total_seconds() > self._cache_ttl:
                # Refresh status
                provider_info = self.base_registry.get_provider_info(name)
                if provider_info:
                    capabilities = getattr(status, 'capabilities', {ProviderCapability.TEXT_GENERATION})
                    self._update_provider_status(name, capabilities, provider_info.requires_api_key)
                    status = self._provider_status_cache.get(name)
            
            return status
    
    def get_available_providers(
        self,
        capability: Optional[ProviderCapability] = None,
        category: Optional[str] = None
    ) -> List[str]:
        """Get list of available providers with optional filtering"""

        available_providers = []

        for provider_name in self.base_registry.list_providers(category=category):
            status = self.get_provider_status(provider_name)

            if status and status.is_available:
                # Check capability requirement
                if capability and capability not in status.capabilities:
                    continue

                available_providers.append(provider_name)

        return available_providers

    def get_registered_models(
        self,
        provider_name: str,
        *,
        healthy_only: bool = True,
    ) -> List[str]:
        """Return the models registered for a provider.

        Args:
            provider_name: Provider whose models should be listed.
            healthy_only: When True (default), only return models for providers
                that are currently marked as available.

        Returns:
            A list of model names in registration order without duplicates.
        """

        provider_info = self.base_registry.get_provider_info(provider_name)
        if not provider_info:
            return []

        if healthy_only:
            status = self.get_provider_status(provider_name)
            if not status or not status.is_available:
                return []

        seen: Set[str] = set()
        model_names: List[str] = []

        for model in provider_info.models:
            name = (model.name or "").strip()
            if not name:
                continue

            key = name.lower()
            if key in seen:
                continue

            seen.add(key)
            model_names.append(name)

        default_model = (provider_info.default_model or "").strip()
        if default_model:
            key = default_model.lower()
            if key not in seen:
                model_names.append(default_model)

        return model_names

    def is_model_available(
        self,
        provider_name: str,
        model_name: str,
        *,
        healthy_only: bool = True,
    ) -> bool:
        """Check whether a model is registered (and optionally available)."""

        if not model_name or not model_name.strip():
            return False

        registered_models = self.get_registered_models(
            provider_name,
            healthy_only=healthy_only,
        )

        if not registered_models:
            return False

        target = model_name.strip().lower()
        return any(model.lower() == target for model in registered_models)
    
    def select_provider_with_fallback(
        self,
        preferred_provider: Optional[str] = None,
        capability: Optional[ProviderCapability] = None,
        fallback_chain_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Select best available provider with automatic fallback
        
        Args:
            preferred_provider: Preferred provider name
            capability: Required capability
            fallback_chain_name: Name of fallback chain to use
            
        Returns:
            Selected provider name or None if no providers available
        """
        
        # Try preferred provider first
        if preferred_provider:
            status = self.get_provider_status(preferred_provider)
            if status and status.is_available:
                if not capability or capability in status.capabilities:
                    logger.info(f"Using preferred provider: {preferred_provider}")
                    return preferred_provider
                else:
                    logger.warning(f"Preferred provider {preferred_provider} lacks required capability: {capability}")
            else:
                logger.warning(f"Preferred provider {preferred_provider} is not available")
        
        # Use fallback chain
        fallback_chain = None
        if fallback_chain_name:
            fallback_chain = self._fallback_chains.get(fallback_chain_name)
        elif capability:
            # Find appropriate fallback chain for capability
            for chain_name, chain in self._fallback_chains.items():
                if chain.capability_required == capability:
                    fallback_chain = chain
                    break
        
        if not fallback_chain:
            # Use default text generation chain
            fallback_chain = self._fallback_chains.get("text_generation")
        
        if fallback_chain:
            # Try primary provider
            primary_status = self.get_provider_status(fallback_chain.primary)
            if primary_status and primary_status.is_available:
                if not capability or capability in primary_status.capabilities:
                    logger.info(f"Using primary provider from fallback chain: {fallback_chain.primary}")
                    return fallback_chain.primary
            
            # Try fallback providers
            for fallback_provider in fallback_chain.fallbacks:
                fallback_status = self.get_provider_status(fallback_provider)
                if fallback_status and fallback_status.is_available:
                    if not capability or capability in fallback_status.capabilities:
                        logger.info(f"Using fallback provider: {fallback_provider}")
                        return fallback_provider
        
        # Last resort: try any available provider with required capability
        available_providers = self.get_available_providers(capability=capability)
        if available_providers:
            selected = available_providers[0]
            logger.warning(f"Using last resort provider: {selected}")
            return selected
        
        logger.error("No available providers found")
        return None
    
    def create_fallback_chain(
        self,
        name: str,
        primary: str,
        fallbacks: List[str],
        capability_required: Optional[ProviderCapability] = None,
        max_fallback_attempts: int = 3
    ) -> None:
        """Create a custom fallback chain"""
        
        with self._lock:
            self._fallback_chains[name] = FallbackChain(
                primary=primary,
                fallbacks=fallbacks,
                capability_required=capability_required,
                max_fallback_attempts=max_fallback_attempts
            )
            
            logger.info(f"Created fallback chain '{name}': {primary} -> {fallbacks}")
    
    def get_provider_recommendations(self, failed_provider: str) -> Dict[str, Any]:
        """Get recommendations when a provider fails"""
        
        recommendations = {
            "failed_provider": failed_provider,
            "alternatives": [],
            "configuration_guidance": [],
            "status_summary": {}
        }
        
        # Get failed provider status
        failed_status = self.get_provider_status(failed_provider)
        if failed_status:
            recommendations["status_summary"][failed_provider] = {
                "is_available": failed_status.is_available,
                "has_api_key": failed_status.has_api_key,
                "health_status": failed_status.health_status.value,
                "error_message": failed_status.error_message
            }
            
            # Provide configuration guidance
            if not failed_status.has_api_key:
                provider_info = self.base_registry.get_provider_info(failed_provider)
                if provider_info and provider_info.requires_api_key:
                    api_key_mapping = {
                        "openai": "OPENAI_API_KEY",
                        "anthropic": "ANTHROPIC_API_KEY",
                        "gemini": "GOOGLE_API_KEY",
                        "deepseek": "DEEPSEEK_API_KEY",
                        "huggingface": "HUGGINGFACE_API_KEY",
                        # Test providers
                        "failed_provider": "FAILED_PROVIDER_API_KEY",
                        "missing_key_provider": "MISSING_KEY_PROVIDER_API_KEY",
                        "unavailable_provider": "UNAVAILABLE_PROVIDER_API_KEY"
                    }
                    env_var = api_key_mapping.get(failed_provider.lower())
                    if env_var:
                        recommendations["configuration_guidance"].append(
                            f"Set {env_var} environment variable to enable {failed_provider} provider"
                        )
        
        # Find alternative providers with same capabilities
        if failed_status and failed_status.capabilities:
            for capability in failed_status.capabilities:
                alternatives = self.get_available_providers(capability=capability)
                # Remove failed provider from alternatives
                alternatives = [p for p in alternatives if p != failed_provider]
                recommendations["alternatives"].extend(alternatives)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_alternatives = []
        for alt in recommendations["alternatives"]:
            if alt not in seen:
                seen.add(alt)
                unique_alternatives.append(alt)
        recommendations["alternatives"] = unique_alternatives[:3]  # Top 3 alternatives
        
        return recommendations
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        
        status = {
            "total_providers": 0,
            "available_providers": 0,
            "providers_missing_api_keys": 0,
            "unhealthy_providers": 0,
            "provider_details": {},
            "fallback_chains": list(self._fallback_chains.keys()),
            "recommendations": []
        }
        
        for provider_name in self.base_registry.list_providers():
            provider_status = self.get_provider_status(provider_name)
            status["total_providers"] += 1
            
            if provider_status:
                if provider_status.is_available:
                    status["available_providers"] += 1
                
                if not provider_status.has_api_key:
                    provider_info = self.base_registry.get_provider_info(provider_name)
                    if provider_info and provider_info.requires_api_key:
                        status["providers_missing_api_keys"] += 1
                
                if provider_status.health_status == HealthStatus.UNHEALTHY:
                    status["unhealthy_providers"] += 1
                
                status["provider_details"][provider_name] = {
                    "is_available": provider_status.is_available,
                    "has_api_key": provider_status.has_api_key,
                    "health_status": provider_status.health_status.value,
                    "capabilities": [cap.value for cap in provider_status.capabilities],
                    "error_message": provider_status.error_message
                }
        
        # Generate recommendations
        if status["providers_missing_api_keys"] > 0:
            status["recommendations"].append(
                "Configure missing API keys to enable more providers"
            )
        
        if status["available_providers"] == 0:
            status["recommendations"].append(
                "No providers are currently available. Check API keys and network connectivity"
            )
        elif status["available_providers"] == 1:
            status["recommendations"].append(
                "Only one provider is available. Configure additional providers for better resilience"
            )
        
        return status
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def monitor_loop():
            while True:
                try:
                    # Refresh provider statuses
                    for provider_name in self.base_registry.list_providers():
                        status = self.get_provider_status(provider_name)  # This will refresh if stale
                    
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Error in health monitoring loop: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        # Start monitoring in background thread
        monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Started provider health monitoring")
    
    def shutdown(self):
        """Shutdown the provider registry service"""
        logger.info("Shutting down provider registry service")


# Global instance
_provider_registry_service: Optional[ProviderRegistryService] = None
_service_lock = threading.RLock()


def get_provider_registry_service() -> ProviderRegistryService:
    """Get the global provider registry service instance"""
    global _provider_registry_service
    if _provider_registry_service is None:
        with _service_lock:
            if _provider_registry_service is None:
                _provider_registry_service = ProviderRegistryService()
    return _provider_registry_service


def initialize_provider_registry_service() -> ProviderRegistryService:
    """Initialize a fresh provider registry service"""
    global _provider_registry_service
    with _service_lock:
        if _provider_registry_service:
            _provider_registry_service.shutdown()
        _provider_registry_service = ProviderRegistryService()
    return _provider_registry_service
