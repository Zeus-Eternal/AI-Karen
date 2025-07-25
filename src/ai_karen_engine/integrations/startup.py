"""
LLM Provider Startup Initialization

Ensures all providers are registered and performs initial health checks on startup.
"""

import logging
import asyncio
from typing import Dict, Any

from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.integrations.llm_utils import get_llm_manager

logger = logging.getLogger("kari.llm_startup")


def initialize_llm_providers() -> Dict[str, Any]:
    """
    Initialize LLM providers on startup.
    
    Returns:
        Dict with initialization results
    """
    logger.info("Initializing LLM providers...")
    
    try:
        # Get registry instance (this will auto-register built-in providers)
        registry = get_registry()
        
        # Get list of registered providers
        providers = registry.list_providers()
        logger.info(f"Found {len(providers)} registered providers: {', '.join(providers)}")
        
        # Perform health checks on all providers
        health_results = registry.health_check_all()
        
        # Log health check results
        healthy_count = 0
        for provider_name, health in health_results.items():
            status = health.get("status", "unknown")
            if status == "healthy":
                healthy_count += 1
                logger.info(f"✓ Provider '{provider_name}' is healthy")
            elif status == "unhealthy":
                error = health.get("error", "Unknown error")
                logger.warning(f"✗ Provider '{provider_name}' is unhealthy: {error}")
            else:
                logger.info(f"? Provider '{provider_name}' status unknown")
        
        # Get available providers
        available_providers = registry.get_available_providers()
        
        result = {
            "status": "success",
            "total_providers": len(providers),
            "healthy_providers": healthy_count,
            "available_providers": available_providers,
            "health_results": health_results
        }
        
        logger.info(f"LLM provider initialization complete. {healthy_count}/{len(providers)} providers healthy.")
        
        return result
        
    except Exception as ex:
        logger.error(f"Failed to initialize LLM providers: {ex}")
        return {
            "status": "error",
            "error": str(ex),
            "total_providers": 0,
            "healthy_providers": 0,
            "available_providers": []
        }


def get_default_llm_manager():
    """Get default LLM manager with registry-based providers."""
    return get_llm_manager(use_registry=True)


async def async_health_check_all() -> Dict[str, Dict[str, Any]]:
    """Perform async health check on all providers."""
    registry = get_registry()
    
    # Run health checks concurrently
    providers = registry.list_providers()
    tasks = []
    
    async def check_provider(name: str) -> tuple[str, Dict[str, Any]]:
        # Run health check in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, registry.health_check, name)
        return name, result
    
    tasks = [check_provider(name) for name in providers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    health_results = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Health check failed: {result}")
        else:
            name, health = result
            health_results[name] = health
    
    return health_results


def validate_provider_configuration() -> Dict[str, Any]:
    """
    Validate provider configurations and API keys.
    
    Returns:
        Dict with validation results
    """
    logger.info("Validating provider configurations...")
    
    registry = get_registry()
    validation_results = {}
    
    for provider_name in registry.list_providers():
        try:
            provider_info = registry.get_provider_info(provider_name)
            if not provider_info:
                validation_results[provider_name] = {
                    "status": "error",
                    "message": "Provider info not available"
                }
                continue
            
            # Check if API key is required and available
            if provider_info.get("requires_api_key", False):
                # Try to create provider instance to check API key
                provider = registry.get_provider(provider_name)
                if provider:
                    provider_runtime_info = provider.get_provider_info()
                    has_api_key = provider_runtime_info.get("has_api_key", False)
                    
                    if has_api_key:
                        validation_results[provider_name] = {
                            "status": "valid",
                            "message": "API key configured"
                        }
                    else:
                        validation_results[provider_name] = {
                            "status": "warning",
                            "message": "API key not configured - provider may not work"
                        }
                else:
                    validation_results[provider_name] = {
                        "status": "error",
                        "message": "Could not create provider instance"
                    }
            else:
                validation_results[provider_name] = {
                    "status": "valid",
                    "message": "No API key required"
                }
                
        except Exception as ex:
            validation_results[provider_name] = {
                "status": "error",
                "message": f"Validation failed: {ex}"
            }
    
    # Log validation results
    for provider_name, result in validation_results.items():
        status = result["status"]
        message = result["message"]
        
        if status == "valid":
            logger.info(f"✓ {provider_name}: {message}")
        elif status == "warning":
            logger.warning(f"⚠ {provider_name}: {message}")
        else:
            logger.error(f"✗ {provider_name}: {message}")
    
    return validation_results


# Auto-initialize on import (can be disabled by setting environment variable)
import os
if os.getenv("KARI_AUTO_INIT_LLM", "true").lower() == "true":
    try:
        initialize_llm_providers()
    except Exception as ex:
        logger.warning(f"Auto-initialization failed: {ex}")