"""
Profile Management API Routes

Provides REST API endpoints for LLM profile management, switching, and validation.
"""

import logging
from typing import Any, Dict, List, Optional

from ai_karen_engine.core.error_handler import handle_api_exception
from ai_karen_engine.services.profile_manager import get_profile_manager
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, Depends, HTTPException = import_fastapi(
    "APIRouter", "Depends", "HTTPException"
)
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.profile_routes")

router = APIRouter(tags=["profiles"])


# Request/Response Models
class LLMProfileModel(BaseModel):
    """LLM profile model."""
    name: str
    description: str = ""
    router_policy: Dict[str, Any] = Field(default_factory=dict)
    guardrails: Dict[str, Any] = Field(default_factory=dict)
    memory_budget: Dict[str, Any] = Field(default_factory=dict)
    provider_preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    is_active: bool = False
    is_system: bool = False


class CreateProfileRequest(BaseModel):
    """Create profile request model."""
    profile: LLMProfileModel


class UpdateProfileRequest(BaseModel):
    """Update profile request model."""
    updates: Dict[str, Any]


class SwitchProfileRequest(BaseModel):
    """Switch profile request model."""
    profile_name: str


# Dependency to get profile manager
def get_profile_mgr():
    """Get the global profile manager instance."""
    return get_profile_manager()


@router.get("/", response_model=List[LLMProfileModel])
async def list_profiles(profile_manager=Depends(get_profile_mgr)):
    """
    Get list of all LLM profiles.
    
    Returns:
        List of LLM profiles
    """
    try:
        profiles = profile_manager.list_profiles()
        return [LLMProfileModel(
            name=profile.name,
            description=profile.description,
            router_policy={
                "privacy_level": profile.router_policy.privacy_level,
                "performance_preference": profile.router_policy.performance_preference,
                "cost_preference": profile.router_policy.cost_preference,
                "context_awareness": profile.router_policy.context_awareness,
                "fallback_strategy": profile.router_policy.fallback_strategy
            },
            guardrails={
                "content_filtering": profile.guardrails.content_filtering,
                "pii_detection": profile.guardrails.pii_detection,
                "toxicity_filtering": profile.guardrails.toxicity_filtering,
                "code_execution_safety": profile.guardrails.code_execution_safety,
                "max_tokens_per_request": profile.guardrails.max_tokens_per_request,
                "rate_limit_per_minute": profile.guardrails.rate_limit_per_minute,
                "allowed_capabilities": list(profile.guardrails.allowed_capabilities)
            },
            memory_budget={
                "max_context_length": profile.memory_budget.max_context_length,
                "max_concurrent_requests": profile.memory_budget.max_concurrent_requests,
                "memory_limit_mb": profile.memory_budget.memory_limit_mb,
                "gpu_memory_fraction": profile.memory_budget.gpu_memory_fraction,
                "enable_kv_cache": profile.memory_budget.enable_kv_cache,
                "cache_size_mb": profile.memory_budget.cache_size_mb
            },
            provider_preferences={
                "chat": profile.provider_preferences.chat,
                "code": profile.provider_preferences.code,
                "reasoning": profile.provider_preferences.reasoning,
                "embedding": profile.provider_preferences.embedding,
                "vision": profile.provider_preferences.vision,
                "local_fallback": profile.provider_preferences.local_fallback,
                "privacy_tasks": profile.provider_preferences.privacy_tasks
            },
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            is_active=profile.is_active,
            is_system=profile.is_system
        ) for profile in profiles]
        
    except Exception as ex:
        logger.error(f"Failed to list profiles: {ex}")
        raise handle_api_exception(ex, "Failed to retrieve profile list")


@router.get("/active", response_model=Optional[LLMProfileModel])
async def get_active_profile(profile_manager=Depends(get_profile_mgr)):
    """
    Get the currently active LLM profile.
    
    Returns:
        Active LLM profile or None if no profile is active
    """
    try:
        active_profile = profile_manager.get_active_profile()
        if active_profile:
            return LLMProfileModel(
                name=active_profile.name,
                description=active_profile.description,
                is_active=active_profile.is_active,
                is_system=active_profile.is_system
            )
        return None
        
    except Exception as ex:
        logger.error(f"Failed to get active profile: {ex}")
        raise handle_api_exception(ex, "Failed to get active profile")


@router.post("/switch", response_model=Dict[str, Any])
async def switch_profile(
    request: SwitchProfileRequest,
    profile_manager=Depends(get_profile_mgr)
):
    """
    Switch to a different LLM profile.
    
    Args:
        request: Switch profile request
        
    Returns:
        Success confirmation
    """
    try:
        success = profile_manager.switch_profile(request.profile_name)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Profile '{request.profile_name}' not found"
            )
        
        return {
            "success": True,
            "message": f"Switched to profile '{request.profile_name}'",
            "active_profile": request.profile_name
        }
        
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"Failed to switch profile: {ex}")
        raise handle_api_exception(ex, "Failed to switch profile")


# Export the router
__all__ = ["router"]