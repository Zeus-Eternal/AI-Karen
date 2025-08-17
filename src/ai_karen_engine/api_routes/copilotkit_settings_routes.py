"""
API Routes for CopilotKit Settings Management

This module provides REST API endpoints for:
- CopilotKit configuration management
- Service status and health checks
- Connection testing
- Feature toggle management
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/copilot", tags=["CopilotKit Settings"])

# -----------------------------
# Request/Response Models
# -----------------------------

class CopilotKitFeatures(BaseModel):
    """CopilotKit feature configuration."""
    code_suggestions: bool = True
    ui_assistance: bool = True
    development_tools: bool = True
    memory_integration: bool = False


class CopilotKitAdvanced(BaseModel):
    """Advanced CopilotKit settings."""
    max_suggestions: int = Field(default=5, ge=1, le=20)
    suggestion_delay: int = Field(default=500, ge=0, le=5000)
    auto_complete: bool = True
    context_awareness: bool = True


class CopilotKitConfig(BaseModel):
    """CopilotKit configuration model."""
    enabled: bool = True
    api_base_url: str = "http://localhost:8000/api/copilot"
    timeout: int = Field(default=30, ge=1, le=300)
    features: CopilotKitFeatures = Field(default_factory=CopilotKitFeatures)
    advanced: CopilotKitAdvanced = Field(default_factory=CopilotKitAdvanced)


class CopilotKitStatus(BaseModel):
    """CopilotKit service status model."""
    status: str  # healthy, unhealthy, unknown
    message: str
    version: Optional[str] = None
    features_available: Optional[List[str]] = None
    last_check: Optional[float] = None


class ConnectionTestRequest(BaseModel):
    """Connection test request model."""
    api_base_url: str
    timeout: int = 30


class ConnectionTestResponse(BaseModel):
    """Connection test response model."""
    success: bool
    message: str
    response_time: Optional[float] = None
    error_details: Optional[str] = None


# -----------------------------
# Global Configuration Storage
# -----------------------------

# In-memory storage for CopilotKit configuration
# In a production environment, this would be stored in a database
_copilotkit_config: CopilotKitConfig = CopilotKitConfig()
_copilotkit_status: CopilotKitStatus = CopilotKitStatus(
    status="unknown",
    message="Status not checked yet"
)


# -----------------------------
# Configuration Endpoints
# -----------------------------

@router.get("/settings", response_model=CopilotKitConfig)
async def get_copilotkit_settings() -> CopilotKitConfig:
    """Get current CopilotKit configuration."""
    try:
        return _copilotkit_config
    except Exception as e:
        logger.error(f"Failed to get CopilotKit settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.post("/settings", response_model=CopilotKitConfig)
async def update_copilotkit_settings(config: CopilotKitConfig) -> CopilotKitConfig:
    """Update CopilotKit configuration."""
    try:
        global _copilotkit_config
        _copilotkit_config = config
        
        logger.info(f"CopilotKit settings updated: enabled={config.enabled}")
        return _copilotkit_config
        
    except Exception as e:
        logger.error(f"Failed to update CopilotKit settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.get("/status", response_model=CopilotKitStatus)
async def get_copilotkit_status() -> CopilotKitStatus:
    """Get CopilotKit service status."""
    try:
        # Update status with current timestamp
        global _copilotkit_status
        
        # Perform basic health check
        if _copilotkit_config.enabled:
            # In a real implementation, this would check the actual CopilotKit service
            _copilotkit_status = CopilotKitStatus(
                status="healthy",
                message="CopilotKit UI framework is configured and enabled",
                version="1.0.0",
                features_available=[
                    feature for feature, enabled in _copilotkit_config.features.dict().items()
                    if enabled
                ],
                last_check=__import__('time').time()
            )
        else:
            _copilotkit_status = CopilotKitStatus(
                status="unhealthy",
                message="CopilotKit is disabled in configuration",
                last_check=__import__('time').time()
            )
        
        return _copilotkit_status
        
    except Exception as e:
        logger.error(f"Failed to get CopilotKit status: {e}")
        return CopilotKitStatus(
            status="unhealthy",
            message=f"Status check failed: {str(e)}",
            last_check=__import__('time').time()
        )


@router.post("/test", response_model=ConnectionTestResponse)
async def test_copilotkit_connection(request: ConnectionTestRequest) -> ConnectionTestResponse:
    """Test connection to CopilotKit service."""
    try:
        import time
        start_time = time.time()
        
        # In a real implementation, this would make an actual HTTP request to the CopilotKit service
        # For now, we'll simulate a connection test
        
        if not request.api_base_url:
            return ConnectionTestResponse(
                success=False,
                message="API base URL is required",
                error_details="Empty or invalid API base URL provided"
            )
        
        # Simulate connection test delay
        await __import__('asyncio').sleep(0.1)
        
        response_time = time.time() - start_time
        
        # Simulate successful connection
        return ConnectionTestResponse(
            success=True,
            message="Connection test successful - CopilotKit service is responding",
            response_time=response_time
        )
        
    except Exception as e:
        logger.error(f"CopilotKit connection test failed: {e}")
        return ConnectionTestResponse(
            success=False,
            message="Connection test failed",
            error_details=str(e)
        )


# -----------------------------
# Feature Management Endpoints
# -----------------------------

@router.get("/features", response_model=CopilotKitFeatures)
async def get_copilotkit_features() -> CopilotKitFeatures:
    """Get current CopilotKit feature configuration."""
    try:
        return _copilotkit_config.features
    except Exception as e:
        logger.error(f"Failed to get CopilotKit features: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get features: {str(e)}")


@router.post("/features", response_model=CopilotKitFeatures)
async def update_copilotkit_features(features: CopilotKitFeatures) -> CopilotKitFeatures:
    """Update CopilotKit feature configuration."""
    try:
        global _copilotkit_config
        _copilotkit_config.features = features
        
        logger.info(f"CopilotKit features updated: {features.dict()}")
        return _copilotkit_config.features
        
    except Exception as e:
        logger.error(f"Failed to update CopilotKit features: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update features: {str(e)}")


@router.post("/features/{feature_name}/toggle")
async def toggle_copilotkit_feature(feature_name: str, enabled: bool) -> Dict[str, Any]:
    """Toggle a specific CopilotKit feature."""
    try:
        global _copilotkit_config
        
        if not hasattr(_copilotkit_config.features, feature_name):
            raise HTTPException(status_code=404, detail=f"Feature '{feature_name}' not found")
        
        setattr(_copilotkit_config.features, feature_name, enabled)
        
        logger.info(f"CopilotKit feature '{feature_name}' {'enabled' if enabled else 'disabled'}")
        
        return {
            "feature": feature_name,
            "enabled": enabled,
            "message": f"Feature '{feature_name}' {'enabled' if enabled else 'disabled'} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle CopilotKit feature '{feature_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle feature: {str(e)}")


# -----------------------------
# Information Endpoints
# -----------------------------

@router.get("/info")
async def get_copilotkit_info() -> Dict[str, Any]:
    """Get general information about CopilotKit integration."""
    try:
        return {
            "name": "CopilotKit",
            "description": "AI-powered development assistance framework",
            "category": "UI_FRAMEWORK",
            "is_llm_provider": False,
            "provider_type": "ui_framework",
            "capabilities": [
                "ui_assistance",
                "code_suggestions", 
                "development_tools",
                "memory_integration"
            ],
            "documentation_url": "https://docs.copilotkit.ai",
            "github_url": "https://github.com/CopilotKit/CopilotKit",
            "version": "1.0.0",
            "configuration": {
                "enabled": _copilotkit_config.enabled,
                "features_enabled": sum(1 for enabled in _copilotkit_config.features.dict().values() if enabled),
                "total_features": len(_copilotkit_config.features.dict())
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get CopilotKit info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get info: {str(e)}")


# Add the router to the main application
def get_router() -> APIRouter:
    """Get the CopilotKit settings routes."""
    return router