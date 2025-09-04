"""
API Routes for Dynamic Provider System

This module provides REST API endpoints for:
- Dynamic provider discovery and management
- API key validation with real-time feedback
- LLM profile management and switching
- Provider health monitoring
- Model discovery and management
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, ConfigDict, Field

from ai_karen_engine.integrations.dynamic_provider_system import get_dynamic_provider_manager
from ai_karen_engine.integrations.llm_profile_system import (
    get_profile_manager,
    RouterPolicy,
    GuardrailLevel,
    ProviderPreference,
    GuardrailConfig,
    MemoryBudget
)

logger = logging.getLogger(__name__)

# NOTE: Do not include a leading '/api' here because the app mounts
# routers under '/api' already. Using '/providers' ensures final paths
# are '/api/providers/...'.
router = APIRouter(prefix="/providers", tags=["Dynamic Providers"])

# -----------------------------
# Request/Response Models
# -----------------------------

class ProviderInfo(BaseModel):
    """Provider information response model."""
    name: str
    description: str
    category: str
    requires_api_key: bool
    capabilities: List[str]
    is_llm_provider: bool
    provider_type: str
    health_status: str
    error_message: Optional[str] = None
    last_health_check: Optional[float] = None
    cached_models_count: int
    last_discovery: Optional[float] = None
    api_base_url: Optional[str] = None


class ModelInfo(BaseModel):
    """Model information response model."""
    id: str
    name: str
    family: str
    format: Optional[str] = None
    size: Optional[int] = None
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    capabilities: List[str] = Field(default_factory=list)
    local_path: Optional[str] = None
    download_url: Optional[str] = None
    downloads: Optional[int] = None
    likes: Optional[int] = None


class ApiKeyValidationRequest(BaseModel):
    """API key validation request model."""
    provider: str
    api_key: str


class ApiKeyValidationResponse(BaseModel):
    """API key validation response model."""
    valid: bool
    message: str
    provider: str


class ModelDiscoveryRequest(BaseModel):
    """Model discovery request model."""
    provider: str
    force_refresh: bool = False


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    provider: str
    status: str
    message: str
    response_time: float


class LLMProfileResponse(BaseModel):
    """LLM profile response model."""
    id: str
    name: str
    description: str
    router_policy: str
    providers: Dict[str, Dict[str, Any]]
    fallback_provider: str
    fallback_model: Optional[str] = None
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    created_at: float
    updated_at: float


class CreateProfileRequest(BaseModel):
    """Create profile request model."""
    name: str
    description: str = ""
    router_policy: str = "balanced"
    providers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    fallback_provider: str = "local"
    fallback_model: Optional[str] = None
    enable_streaming: bool = True
    enable_function_calling: bool = True
    enable_vision: bool = False
    temperature: float = 0.7
    max_tokens: int = 1000


class UpdateProfileRequest(BaseModel):
    """Update profile request model."""
    name: Optional[str] = None
    description: Optional[str] = None
    router_policy: Optional[str] = None
    providers: Optional[Dict[str, Dict[str, Any]]] = None
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    enable_streaming: Optional[bool] = None
    enable_function_calling: Optional[bool] = None
    enable_vision: Optional[bool] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


# -----------------------------
# Provider Management Endpoints
# -----------------------------

@router.get("/", response_model=List[ProviderInfo])
async def list_providers(
    llm_only: bool = True,
    healthy_only: bool = False
) -> List[ProviderInfo]:
    """
    List available providers.
    
    Args:
        llm_only: Only return LLM providers (excludes CopilotKit, etc.)
        healthy_only: Only return healthy providers
    """
    try:
        provider_manager = get_dynamic_provider_manager()
        
        # Try to get providers with error handling
        try:
            if llm_only:
                # Use the registry's LLM-only method to exclude UI frameworks like CopilotKit
                from ai_karen_engine.integrations.registry import get_registry
                registry = get_registry()
                provider_names = registry.list_llm_providers(healthy_only=healthy_only)
            else:
                # Get all providers and filter by health if requested
                from ai_karen_engine.integrations.registry import get_registry
                registry = get_registry()
                provider_names = registry.list_providers(healthy_only=healthy_only)
        except AttributeError as attr_error:
            logger.warning(f"Registry method not available: {attr_error}. Using fallback.")
            # Fallback to basic provider list
            provider_names = ["openai", "gemini", "deepseek", "huggingface", "local"]
            if not llm_only:
                # Only include CopilotKit when explicitly requesting all providers (not LLM-only)
                provider_names.append("copilotkit")
        
        providers = []
        for name in provider_names:
            try:
                provider_info = provider_manager.get_provider_info(name)
                if provider_info:
                    providers.append(ProviderInfo(**provider_info))
            except Exception as info_error:
                logger.warning(f"Failed to get info for provider {name}: {info_error}")
                # Add basic provider info as fallback
                providers.append(ProviderInfo(
                    name=name,
                    description=f"{name.title()} provider",
                    category="LLM",
                    requires_api_key=True,
                    capabilities=["streaming"],
                    is_llm_provider=name != "copilotkit",
                    provider_type="remote",
                    health_status="unknown",
                    cached_models_count=0
                ))
        
        return providers
        
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        # Return minimal fallback response instead of error
        fallback_providers = [
            ProviderInfo(
                name="openai",
                description="OpenAI GPT models",
                category="LLM",
                requires_api_key=True,
                capabilities=["streaming", "vision"],
                is_llm_provider=True,
                provider_type="remote",
                health_status="unknown",
                cached_models_count=0
            ),
            ProviderInfo(
                name="local",
                description="Local models",
                category="LLM",
                requires_api_key=False,
                capabilities=["streaming"],
                is_llm_provider=True,
                provider_type="local",
                health_status="unknown",
                cached_models_count=0
            )
        ]
        logger.info("Returning fallback provider list")
        return fallback_providers


@router.get("/{provider_name}", response_model=ProviderInfo)
async def get_provider(provider_name: str) -> ProviderInfo:
    """Get detailed information about a specific provider."""
    try:
        provider_manager = get_dynamic_provider_manager()
        provider_info = provider_manager.get_provider_info(provider_name)
        
        if not provider_info:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        return ProviderInfo(**provider_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider {provider_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider: {str(e)}")


@router.post("/validate-api-key", response_model=ApiKeyValidationResponse)
async def validate_api_key(request: ApiKeyValidationRequest) -> ApiKeyValidationResponse:
    """Validate an API key for a provider."""
    try:
        provider_manager = get_dynamic_provider_manager()
        
        config = {"api_key": request.api_key}
        result = await provider_manager.validate_api_key(request.provider, config)
        
        return ApiKeyValidationResponse(
            valid=result["valid"],
            message=result["message"],
            provider=request.provider
        )
        
    except Exception as e:
        logger.error(f"Failed to validate API key for {request.provider}: {e}")
        return ApiKeyValidationResponse(
            valid=False,
            message=f"Validation failed: {str(e)}",
            provider=request.provider
        )


@router.post("/{provider_name}/health-check", response_model=HealthCheckResponse)
async def health_check_provider(provider_name: str) -> HealthCheckResponse:
    """Perform health check on a specific provider."""
    try:
        provider_manager = get_dynamic_provider_manager()
        result = provider_manager.health_check(provider_name)
        
        return HealthCheckResponse(
            provider=provider_name,
            status=result["status"],
            message=result["message"],
            response_time=result.get("response_time", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Health check failed for {provider_name}: {e}")
        return HealthCheckResponse(
            provider=provider_name,
            status="error",
            message=f"Health check failed: {str(e)}",
            response_time=0.0
        )


@router.post("/health-check-all")
async def health_check_all_providers() -> Dict[str, HealthCheckResponse]:
    """Perform health check on all providers."""
    try:
        provider_manager = get_dynamic_provider_manager()
        provider_names = provider_manager.get_llm_providers()
        
        results = {}
        for provider_name in provider_names:
            try:
                result = provider_manager.health_check(provider_name)
                results[provider_name] = HealthCheckResponse(
                    provider=provider_name,
                    status=result["status"],
                    message=result["message"],
                    response_time=result.get("response_time", 0.0)
                )
            except Exception as e:
                results[provider_name] = HealthCheckResponse(
                    provider=provider_name,
                    status="error",
                    message=f"Health check failed: {str(e)}",
                    response_time=0.0
                )
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to perform health check on all providers: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# -----------------------------
# Model Discovery Endpoints
# -----------------------------

@router.get("/{provider_name}/models", response_model=List[ModelInfo])
async def get_provider_models(
    provider_name: str,
    force_refresh: bool = False
) -> List[ModelInfo]:
    """Get available models from a provider."""
    try:
        provider_manager = get_dynamic_provider_manager()
        models = await provider_manager.discover_models(provider_name, force_refresh=force_refresh)
        
        model_infos = []
        for model in models:
            model_infos.append(ModelInfo(**model))
        
        return model_infos
        
    except Exception as e:
        logger.error(f"Failed to get models for {provider_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.post("/discover-models", response_model=List[ModelInfo])
async def discover_models(
    request: ModelDiscoveryRequest,
    background_tasks: BackgroundTasks
) -> List[ModelInfo]:
    """Discover models from a provider (with background refresh option)."""
    try:
        provider_manager = get_dynamic_provider_manager()
        
        if request.force_refresh:
            # Run discovery in background for better UX
            background_tasks.add_task(
                provider_manager.discover_models,
                request.provider,
                force_refresh=True
            )
        
        models = await provider_manager.discover_models(request.provider, force_refresh=False)
        
        model_infos = []
        for model in models:
            model_infos.append(ModelInfo(**model))
        
        return model_infos
        
    except Exception as e:
        logger.error(f"Failed to discover models for {request.provider}: {e}")
        raise HTTPException(status_code=500, detail=f"Model discovery failed: {str(e)}")


# -----------------------------
# LLM Profile Management Endpoints
# -----------------------------

@router.get("/profiles", response_model=List[LLMProfileResponse])
async def list_profiles() -> List[LLMProfileResponse]:
    """List all LLM profiles."""
    try:
        profile_manager = get_profile_manager()
        profiles = profile_manager.list_profiles()
        
        profile_responses = []
        for profile in profiles:
            # Convert providers to dict format for API response
            providers_dict = {}
            for use_case, pref in profile.providers.items():
                providers_dict[use_case] = {
                    "provider": pref.provider,
                    "model": pref.model,
                    "priority": pref.priority,
                    "max_cost_per_1k_tokens": pref.max_cost_per_1k_tokens,
                    "required_capabilities": list(pref.required_capabilities),
                    "excluded_capabilities": list(pref.excluded_capabilities)
                }
            
            profile_responses.append(LLMProfileResponse(
                id=profile.id,
                name=profile.name,
                description=profile.description,
                router_policy=profile.router_policy.value,
                providers=providers_dict,
                fallback_provider=profile.fallback_provider,
                fallback_model=profile.fallback_model,
                is_valid=profile.is_valid,
                validation_errors=profile.validation_errors,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            ))
        
        return profile_responses
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list profiles: {str(e)}")


@router.get("/profiles/active", response_model=Optional[LLMProfileResponse])
async def get_active_profile() -> Optional[LLMProfileResponse]:
    """Get the currently active profile."""
    try:
        profile_manager = get_profile_manager()
        profile = profile_manager.get_active_profile()
        
        if not profile:
            return None
        
        # Convert providers to dict format
        providers_dict = {}
        for use_case, pref in profile.providers.items():
            providers_dict[use_case] = {
                "provider": pref.provider,
                "model": pref.model,
                "priority": pref.priority,
                "max_cost_per_1k_tokens": pref.max_cost_per_1k_tokens,
                "required_capabilities": list(pref.required_capabilities),
                "excluded_capabilities": list(pref.excluded_capabilities)
            }
        
        return LLMProfileResponse(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            router_policy=profile.router_policy.value,
            providers=providers_dict,
            fallback_provider=profile.fallback_provider,
            fallback_model=profile.fallback_model,
            is_valid=profile.is_valid,
            validation_errors=profile.validation_errors,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except Exception as e:
        logger.error(f"Failed to get active profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active profile: {str(e)}")


@router.post("/profiles", response_model=LLMProfileResponse)
async def create_profile(request: CreateProfileRequest) -> LLMProfileResponse:
    """Create a new LLM profile."""
    try:
        profile_manager = get_profile_manager()
        
        # Convert providers dict to ProviderPreference objects
        providers = {}
        for use_case, pref_data in request.providers.items():
            providers[use_case] = ProviderPreference(
                provider=pref_data["provider"],
                model=pref_data.get("model"),
                priority=pref_data.get("priority", 50),
                max_cost_per_1k_tokens=pref_data.get("max_cost_per_1k_tokens"),
                required_capabilities=set(pref_data.get("required_capabilities", [])),
                excluded_capabilities=set(pref_data.get("excluded_capabilities", []))
            )
        
        profile = profile_manager.create_profile(
            name=request.name,
            description=request.description,
            router_policy=RouterPolicy(request.router_policy),
            providers=providers,
            fallback_provider=request.fallback_provider,
            fallback_model=request.fallback_model,
            enable_streaming=request.enable_streaming,
            enable_function_calling=request.enable_function_calling,
            enable_vision=request.enable_vision,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Convert back to response format
        providers_dict = {}
        for use_case, pref in profile.providers.items():
            providers_dict[use_case] = {
                "provider": pref.provider,
                "model": pref.model,
                "priority": pref.priority,
                "max_cost_per_1k_tokens": pref.max_cost_per_1k_tokens,
                "required_capabilities": list(pref.required_capabilities),
                "excluded_capabilities": list(pref.excluded_capabilities)
            }
        
        return LLMProfileResponse(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            router_policy=profile.router_policy.value,
            providers=providers_dict,
            fallback_provider=profile.fallback_provider,
            fallback_model=profile.fallback_model,
            is_valid=profile.is_valid,
            validation_errors=profile.validation_errors,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {str(e)}")


@router.put("/profiles/{profile_id}", response_model=LLMProfileResponse)
async def update_profile(profile_id: str, request: UpdateProfileRequest) -> LLMProfileResponse:
    """Update an existing LLM profile."""
    try:
        profile_manager = get_profile_manager()
        
        # Prepare updates
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.router_policy is not None:
            updates["router_policy"] = RouterPolicy(request.router_policy)
        if request.fallback_provider is not None:
            updates["fallback_provider"] = request.fallback_provider
        if request.fallback_model is not None:
            updates["fallback_model"] = request.fallback_model
        if request.enable_streaming is not None:
            updates["enable_streaming"] = request.enable_streaming
        if request.enable_function_calling is not None:
            updates["enable_function_calling"] = request.enable_function_calling
        if request.enable_vision is not None:
            updates["enable_vision"] = request.enable_vision
        if request.temperature is not None:
            updates["temperature"] = request.temperature
        if request.max_tokens is not None:
            updates["max_tokens"] = request.max_tokens
        
        # Convert providers if provided
        if request.providers is not None:
            providers = {}
            for use_case, pref_data in request.providers.items():
                providers[use_case] = ProviderPreference(
                    provider=pref_data["provider"],
                    model=pref_data.get("model"),
                    priority=pref_data.get("priority", 50),
                    max_cost_per_1k_tokens=pref_data.get("max_cost_per_1k_tokens"),
                    required_capabilities=set(pref_data.get("required_capabilities", [])),
                    excluded_capabilities=set(pref_data.get("excluded_capabilities", []))
                )
            updates["providers"] = providers
        
        profile = profile_manager.update_profile(profile_id, **updates)
        
        # Convert back to response format
        providers_dict = {}
        for use_case, pref in profile.providers.items():
            providers_dict[use_case] = {
                "provider": pref.provider,
                "model": pref.model,
                "priority": pref.priority,
                "max_cost_per_1k_tokens": pref.max_cost_per_1k_tokens,
                "required_capabilities": list(pref.required_capabilities),
                "excluded_capabilities": list(pref.excluded_capabilities)
            }
        
        return LLMProfileResponse(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            router_policy=profile.router_policy.value,
            providers=providers_dict,
            fallback_provider=profile.fallback_provider,
            fallback_model=profile.fallback_model,
            is_valid=profile.is_valid,
            validation_errors=profile.validation_errors,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str) -> Dict[str, str]:
    """Delete an LLM profile."""
    try:
        profile_manager = get_profile_manager()
        success = profile_manager.delete_profile(profile_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
        
        return {"message": f"Profile {profile_id} deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")


@router.post("/profiles/{profile_id}/activate", response_model=LLMProfileResponse)
async def activate_profile(profile_id: str) -> LLMProfileResponse:
    """Activate a profile (switch to it)."""
    try:
        profile_manager = get_profile_manager()
        profile = profile_manager.switch_profile(profile_id)
        
        # Convert to response format
        providers_dict = {}
        for use_case, pref in profile.providers.items():
            providers_dict[use_case] = {
                "provider": pref.provider,
                "model": pref.model,
                "priority": pref.priority,
                "max_cost_per_1k_tokens": pref.max_cost_per_1k_tokens,
                "required_capabilities": list(pref.required_capabilities),
                "excluded_capabilities": list(pref.excluded_capabilities)
            }
        
        return LLMProfileResponse(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            router_policy=profile.router_policy.value,
            providers=providers_dict,
            fallback_provider=profile.fallback_provider,
            fallback_model=profile.fallback_model,
            is_valid=profile.is_valid,
            validation_errors=profile.validation_errors,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to activate profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate profile: {str(e)}")


@router.get("/profiles/{profile_id}/validate")
async def validate_profile_compatibility(profile_id: str) -> Dict[str, Any]:
    """Validate profile compatibility with available providers."""
    try:
        profile_manager = get_profile_manager()
        profile = profile_manager.get_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
        
        result = profile_manager.validate_profile_compatibility(profile)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Profile validation failed: {str(e)}")


# Add the router to the main application
def get_router() -> APIRouter:
    """Get the dynamic provider routes."""
    return router
