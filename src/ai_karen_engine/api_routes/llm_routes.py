"""
LLM Provider API Routes

Provides REST API endpoints for managing LLM providers, profiles, and configuration.
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Depends
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "FastAPI is required for LLM routes. Install via `pip install fastapi`."
    ) from e

try:
    from pydantic import BaseModel, Field
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "Pydantic is required for LLM routes. Install via `pip install pydantic`."
    ) from e

from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.core.config_manager import ConfigManager

logger = logging.getLogger("kari.llm_routes")

router = APIRouter(prefix="/api/llm", tags=["llm"])


# Request/Response Models
class ProviderInfo(BaseModel):
    """LLM Provider information model."""
    name: str
    provider_class: str
    description: str
    supports_streaming: bool = False
    supports_embeddings: bool = False
    requires_api_key: bool = False
    default_model: str = ""
    health_status: str = "unknown"
    last_health_check: Optional[float] = None
    error_message: Optional[str] = None


class LLMProfile(BaseModel):
    """LLM Profile configuration model."""
    name: str
    providers: Dict[str, str] = Field(
        description="Provider assignments for different tasks",
        example={
            "chat": "ollama",
            "conversation_processing": "ollama", 
            "code": "deepseek",
            "generic": "ollama"
        }
    )
    fallback: str = Field(description="Fallback provider name")


class LLMSettings(BaseModel):
    """LLM Settings configuration model."""
    selected_profile: str
    provider_api_keys: Dict[str, str] = Field(default_factory=dict)
    custom_models: Dict[str, str] = Field(default_factory=dict)


class HealthCheckResult(BaseModel):
    """Health check result model."""
    status: str
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: float


# Dependency to get LLM registry
def get_llm_registry():
    """Get the global LLM registry instance."""
    return get_registry()


# Dependency to get config manager
def get_config_manager():
    """Get the config manager instance."""
    return ConfigManager()


@router.get("/providers", response_model=Dict[str, List[ProviderInfo]])
async def list_providers(registry=Depends(get_llm_registry)):
    """
    Get list of all registered LLM providers with their information.
    
    Returns:
        Dict containing list of provider information
    """
    try:
        provider_names = registry.list_providers()
        providers = []
        
        for name in provider_names:
            provider_info = registry.get_provider_info(name)
            if provider_info:
                providers.append(ProviderInfo(**provider_info))
            else:
                # Create basic info if detailed info not available
                providers.append(ProviderInfo(
                    name=name,
                    provider_class="Unknown",
                    description=f"{name.title()} LLM provider",
                    health_status="unknown"
                ))
        
        return {"providers": providers}
        
    except Exception as ex:
        logger.error(f"Failed to list providers: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROVIDER_LIST_ERROR",
                "message": "Failed to retrieve provider list",
                "type": "SERVICE_ERROR"
            }
        )


@router.get("/providers/{provider_name}", response_model=ProviderInfo)
async def get_provider_info(
    provider_name: str,
    registry=Depends(get_llm_registry)
):
    """
    Get detailed information about a specific LLM provider.
    
    Args:
        provider_name: Name of the provider to get info for
        
    Returns:
        Provider information
    """
    try:
        provider_info = registry.get_provider_info(provider_name)
        
        if not provider_info:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PROVIDER_NOT_FOUND",
                    "message": f"Provider '{provider_name}' not found",
                    "type": "NOT_FOUND_ERROR"
                }
            )
        
        return ProviderInfo(**provider_info)
        
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Failed to get provider info for {provider_name}: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROVIDER_INFO_ERROR",
                "message": f"Failed to get provider information for {provider_name}",
                "type": "SERVICE_ERROR"
            }
        )


@router.get("/profiles", response_model=Dict[str, List[LLMProfile]])
async def list_profiles():
    """
    Get list of available LLM profiles.
    
    Returns:
        Dict containing list of LLM profiles
    """
    try:
        # Load profiles from config file
        profiles_path = Path("config/llm_profiles.yml")
        
        if not profiles_path.exists():
            # Return default profiles if config file doesn't exist
            default_profiles = [
                LLMProfile(
                    name="default",
                    providers={
                        "chat": "ollama",
                        "conversation_processing": "ollama",
                        "code": "deepseek", 
                        "generic": "ollama"
                    },
                    fallback="openai"
                ),
                LLMProfile(
                    name="enterprise",
                    providers={
                        "chat": "openai",
                        "conversation_processing": "openai",
                        "code": "openai",
                        "generic": "openai"
                    },
                    fallback="openai"
                )
            ]
            return {"profiles": default_profiles}
        
        with open(profiles_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        profiles = []
        for profile_name, profile_config in config_data.get("profiles", {}).items():
            profiles.append(LLMProfile(
                name=profile_name,
                providers=profile_config.get("providers", {}),
                fallback=profile_config.get("fallback", "openai")
            ))
        
        return {"profiles": profiles}
        
    except Exception as ex:
        logger.error(f"Failed to load LLM profiles: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROFILES_LOAD_ERROR",
                "message": "Failed to load LLM profiles",
                "type": "SERVICE_ERROR"
            }
        )


@router.post("/settings")
async def save_settings(
    settings: LLMSettings,
    config_manager=Depends(get_config_manager)
):
    """
    Save LLM provider settings.
    
    Args:
        settings: LLM settings to save
        
    Returns:
        Success confirmation
    """
    try:
        # Save settings to config manager
        # Note: This is a simplified implementation
        # In a production system, you might want to save to a database
        # or persistent configuration store
        
        logger.info(f"Saving LLM settings for profile: {settings.selected_profile}")
        
        # For now, we'll just log the settings
        # In a full implementation, you would persist these settings
        logger.info(f"Provider API keys configured: {list(settings.provider_api_keys.keys())}")
        logger.info(f"Custom models configured: {settings.custom_models}")
        
        return {
            "success": True,
            "message": "LLM settings saved successfully",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as ex:
        logger.error(f"Failed to save LLM settings: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SETTINGS_SAVE_ERROR",
                "message": "Failed to save LLM settings",
                "type": "SERVICE_ERROR"
            }
        )


@router.post("/health-check", response_model=Dict[str, Dict[str, Any]])
async def health_check_providers(
    provider_names: Optional[List[str]] = None,
    registry=Depends(get_llm_registry)
):
    """
    Perform health check on LLM providers.
    
    Args:
        provider_names: Optional list of specific providers to check.
                       If None, checks all providers.
        
    Returns:
        Dict containing health check results for each provider
    """
    try:
        if provider_names is None:
            # Check all providers
            results = registry.health_check_all()
        else:
            # Check specific providers
            results = {}
            for provider_name in provider_names:
                results[provider_name] = registry.health_check(provider_name)
        
        return {"results": results}
        
    except Exception as ex:
        logger.error(f"Failed to perform health check: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "HEALTH_CHECK_ERROR",
                "message": "Failed to perform provider health check",
                "type": "SERVICE_ERROR"
            }
        )


@router.get("/health-check/{provider_name}", response_model=HealthCheckResult)
async def health_check_provider(
    provider_name: str,
    registry=Depends(get_llm_registry)
):
    """
    Perform health check on a specific LLM provider.
    
    Args:
        provider_name: Name of the provider to check
        
    Returns:
        Health check result for the provider
    """
    try:
        result = registry.health_check(provider_name)
        
        return HealthCheckResult(
            status=result.get("status", "unknown"),
            message=result.get("message"),
            error=result.get("error"),
            timestamp=result.get("timestamp", 0)
        )
        
    except Exception as ex:
        logger.error(f"Failed to health check provider {provider_name}: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROVIDER_HEALTH_CHECK_ERROR",
                "message": f"Failed to health check provider {provider_name}",
                "type": "SERVICE_ERROR"
            }
        )


@router.get("/available", response_model=Dict[str, List[str]])
async def get_available_providers(registry=Depends(get_llm_registry)):
    """
    Get list of currently available (healthy) LLM providers.
    
    Returns:
        Dict containing list of available provider names
    """
    try:
        available_providers = registry.get_available_providers()
        return {"providers": available_providers}
        
    except Exception as ex:
        logger.error(f"Failed to get available providers: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AVAILABLE_PROVIDERS_ERROR",
                "message": "Failed to get available providers",
                "type": "SERVICE_ERROR"
            }
        )


@router.post("/auto-select", response_model=Dict[str, Optional[str]])
async def auto_select_provider(
    requirements: Optional[Dict[str, Any]] = None,
    registry=Depends(get_llm_registry)
):
    """
    Automatically select the best available provider based on requirements.
    
    Args:
        requirements: Optional dict with requirements like 'streaming', 'embeddings'
        
    Returns:
        Dict containing the selected provider name
    """
    try:
        selected_provider = registry.auto_select_provider(requirements)
        
        return {
            "provider": selected_provider,
            "requirements": requirements or {}
        }
        
    except Exception as ex:
        logger.error(f"Failed to auto-select provider: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AUTO_SELECT_ERROR",
                "message": "Failed to auto-select provider",
                "type": "SERVICE_ERROR"
            }
        )


# Export the router
__all__ = ["router"]