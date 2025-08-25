"""
Public API Routes

These routes provide basic system information without requiring authentication.
Used for initial frontend loading and system status checks.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["public"])


class SystemInfo(BaseModel):
    """Basic system information."""
    name: str = "AI Karen Engine"
    version: str = "1.0.0"
    status: str = "operational"
    authentication_required: bool = True
    features: List[str] = []


class PublicProviderInfo(BaseModel):
    """Public provider information (no sensitive data)."""
    name: str
    description: str
    category: str
    provider_type: str  # local, remote, hybrid
    requires_api_key: bool
    documentation_url: Optional[str] = None


@router.get("/system/info", response_model=SystemInfo)
async def get_system_info():
    """Get basic system information without authentication."""
    try:
        return SystemInfo(
            name="AI Karen Engine",
            version="1.0.0",
            status="operational",
            authentication_required=True,
            features=[
                "Multi-provider LLM support",
                "Intelligent error responses", 
                "Session persistence",
                "Role-based access control",
                "Training orchestration",
                "Model management"
            ]
        )
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


@router.get("/providers/basic", response_model=List[PublicProviderInfo])
async def get_basic_provider_info():
    """Get basic provider information without authentication."""
    try:
        # Return basic provider info that doesn't require authentication
        basic_providers = [
            PublicProviderInfo(
                name="openai",
                description="OpenAI GPT models",
                category="LLM",
                provider_type="remote",
                requires_api_key=True,
                documentation_url="https://platform.openai.com/docs"
            ),
            PublicProviderInfo(
                name="gemini",
                description="Google Gemini models",
                category="LLM", 
                provider_type="remote",
                requires_api_key=True,
                documentation_url="https://ai.google.dev/docs"
            ),
            PublicProviderInfo(
                name="local",
                description="Local model execution",
                category="LLM",
                provider_type="local",
                requires_api_key=False
            ),
            PublicProviderInfo(
                name="huggingface",
                description="Hugging Face models",
                category="LLM",
                provider_type="hybrid",
                requires_api_key=False,
                documentation_url="https://huggingface.co/docs"
            )
        ]
        
        return basic_providers
        
    except Exception as e:
        logger.error(f"Failed to get basic provider info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider information")


@router.get("/health", response_model=Dict[str, Any])
async def public_health_check():
    """Public health check endpoint."""
    try:
        return {
            "status": "healthy",
            "timestamp": "2025-08-25T20:00:00Z",
            "services": {
                "api": "operational",
                "authentication": "operational"
            },
            "message": "System is operational. Authentication required for full access."
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": "2025-08-25T20:00:00Z", 
            "error": str(e),
            "message": "System is experiencing issues."
        }