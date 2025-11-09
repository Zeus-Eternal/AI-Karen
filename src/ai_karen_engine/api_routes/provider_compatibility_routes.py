"""
Provider Compatibility API Routes

This module provides API endpoints for provider-model compatibility checking,
recommendations, and validation.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
try:
    from pydantic import BaseModel
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel
from typing import Dict, Any, Optional

from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService

logger = logging.getLogger("kari.provider_compatibility_routes")

# Create router
router = APIRouter()

# Initialize service
compatibility_service = ProviderModelCompatibilityService()

# Request models
class CompatibilityCheckRequest(BaseModel):
    model_id: str
    provider: str

class LoadModelRequest(BaseModel):
    model_id: str

@router.post('/api/providers/compatibility/check')
async def check_model_compatibility(request: CompatibilityCheckRequest):
    """Check if a model is compatible with a specific provider."""
    try:
        compatibility = compatibility_service.check_model_compatibility(
            request.model_id, request.provider
        )
        
        return {
            "model_id": compatibility.model_id,
            "provider": compatibility.provider,
            "compatible": compatibility.compatible,
            "compatibility_score": compatibility.compatibility_score,
            "reasons": compatibility.reasons,
            "requirements": compatibility.requirements,
            "recommendations": compatibility.recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to check model compatibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/api/providers/{provider_name}/recommendations')
async def get_provider_recommendations(provider_name: str, limit: int = Query(10, ge=1, le=50)):
    """Get recommended models for a specific provider."""
    try:
        recommendations = compatibility_service.get_recommended_models_for_provider(
            provider_name, limit=limit
        )
        
        return {
            "provider": provider_name,
            "recommendations": [
                {
                    "model_id": rec.model_id,
                    "compatible": rec.compatible,
                    "compatibility_score": rec.compatibility_score,
                    "reasons": rec.reasons,
                    "recommendations": rec.recommendations
                }
                for rec in recommendations
            ],
            "total_recommendations": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get provider recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/api/providers/{provider_name}/suggestions')
async def get_provider_suggestions(provider_name: str):
    """Get comprehensive model suggestions for a provider."""
    try:
        suggestions = compatibility_service.get_provider_model_suggestions(provider_name)
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to get provider suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/api/providers/{provider_name}/validate')
async def validate_provider_setup(provider_name: str):
    """Validate that a provider has compatible models available."""
    try:
        validation = compatibility_service.validate_provider_model_setup(provider_name)
        return validation
        
    except Exception as e:
        logger.error(f"Failed to validate provider setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/api/providers/compatibility/statistics')
async def get_compatibility_statistics():
    """Get statistics about model compatibility across providers."""
    try:
        stats = compatibility_service.get_compatibility_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get compatibility statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/api/providers/compatibility/cache/clear')
async def clear_compatibility_cache():
    """Clear the compatibility cache."""
    try:
        compatibility_service.clear_compatibility_cache()
        return {"message": "Compatibility cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear compatibility cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/api/providers/capabilities')
async def get_provider_capabilities():
    """Get capabilities information for all providers."""
    try:
        capabilities = {}
        
        for provider_name, provider_caps in compatibility_service.provider_capabilities.items():
            capabilities[provider_name] = {
                "name": provider_caps.name,
                "supported_formats": provider_caps.supported_formats,
                "required_capabilities": provider_caps.required_capabilities,
                "optional_capabilities": provider_caps.optional_capabilities,
                "memory_requirements": provider_caps.memory_requirements,
                "performance_characteristics": provider_caps.performance_characteristics,
                "model_size_limits": provider_caps.model_size_limits
            }
        
        return {
            "providers": capabilities,
            "total_providers": len(capabilities)
        }
        
    except Exception as e:
        logger.error(f"Failed to get provider capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/api/providers/{provider_name}/models/load')
async def load_model_for_provider(provider_name: str, request: LoadModelRequest):
    """Load a specific model for a provider."""
    try:
        # Check compatibility first
        compatibility = compatibility_service.check_model_compatibility(
            request.model_id, provider_name
        )
        
        if not compatibility.compatible:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Model not compatible with provider",
                    "compatibility": {
                        "compatible": compatibility.compatible,
                        "reasons": compatibility.reasons,
                        "recommendations": compatibility.recommendations
                    }
                }
            )
        
        # Attempt to load model based on provider
        success = False
        error_message = None
        
        try:
            if provider_name == "llama-cpp":
                from ai_karen_engine.integrations.providers.llamacpp_provider import LlamaCppProvider
                # This would typically be done through a provider manager
                # For now, we'll just validate that the model can be loaded
                provider = LlamaCppProvider()
                success = provider.load_model_by_id(request.model_id)
                if not success:
                    error_message = "Failed to load model in LlamaCpp provider"
            else:
                error_message = f"Model loading not implemented for provider: {provider_name}"
        
        except Exception as e:
            error_message = str(e)
        
        if success:
            return {
                "message": f"Model {request.model_id} loaded successfully for {provider_name}",
                "model_id": request.model_id,
                "provider": provider_name,
                "compatibility_score": compatibility.compatibility_score
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": error_message or "Failed to load model",
                    "model_id": request.model_id,
                    "provider": provider_name
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model for provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))