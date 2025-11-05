"""
API Routes for KRO (Kari Reasoning Orchestrator)

Provides REST API endpoints for:
- Processing user requests through KRO
- Getting available models
- Routing decisions
- System status and health checks
"""

from typing import Any, Dict, List, Optional
import logging

try:
    from fastapi import APIRouter, HTTPException, Body, Query
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Stub classes for when FastAPI is not available
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass

        def post(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def get(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    class BaseModel:
        pass

    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/kro", tags=["kro"])


# ===================================
# REQUEST/RESPONSE MODELS
# ===================================

if FASTAPI_AVAILABLE:
    class UserRequestModel(BaseModel):
        """User request model."""
        user_input: str = Field(..., description="User's message or query")
        user_id: str = Field(default="anon", description="User identifier")
        conversation_history: Optional[List[Dict[str, Any]]] = Field(
            default=None,
            description="Recent conversation history"
        )
        context: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Additional context (session_id, tenant_id, etc.)"
        )

    class RoutingRequestModel(BaseModel):
        """Routing decision request."""
        user_input: str = Field(..., description="User's message or query")
        user_id: str = Field(default="anon", description="User identifier")
        task_type: Optional[str] = Field(default=None, description="Task type hint")
        context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


# ===================================
# API ENDPOINTS
# ===================================

@router.post("/process")
async def process_user_request(request: UserRequestModel):
    """
    Process user request through KRO orchestrator.

    This endpoint provides the complete AI-Karen pipeline:
    - Intent classification
    - Intelligent routing via KIRE
    - Model selection and execution
    - Content optimization
    - Dynamic prompt suggestions

    Returns complete response envelope with metadata.
    """
    try:
        from ai_karen_engine.core.kire_kro_integration import get_integration

        integration = get_integration()

        response = await integration.process_user_request(
            user_input=request.user_input,
            user_id=request.user_id,
            conversation_history=request.conversation_history,
            context=request.context,
        )

        return response

    except Exception as e:
        logger.error(f"KRO processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/models")
async def get_available_models():
    """
    Get list of all available models discovered by the system.

    Returns comprehensive model information including:
    - Model names and providers
    - Capabilities and modalities
    - Resource requirements
    - Health status
    """
    try:
        from ai_karen_engine.core.kire_kro_integration import get_integration

        integration = get_integration()
        models = await integration.get_available_models()

        return {
            "success": True,
            "models": models,
            "count": len(models),
        }

    except Exception as e:
        logger.error(f"Model listing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.post("/routing")
async def get_routing_decision(request: RoutingRequestModel):
    """
    Get routing decision for a query without executing it.

    Useful for:
    - Debugging routing logic
    - Previewing model selection
    - Understanding routing reasoning

    Returns routing decision with provider, model, reasoning, and confidence.
    """
    try:
        from ai_karen_engine.core.kire_kro_integration import get_integration

        integration = get_integration()

        decision = await integration.get_routing_decision(
            user_input=request.user_input,
            user_id=request.user_id,
            task_type=request.task_type,
            context=request.context,
        )

        return {
            "success": True,
            "decision": decision,
        }

    except Exception as e:
        logger.error(f"Routing decision failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.get("/status")
async def get_system_status():
    """
    Get comprehensive system status.

    Returns:
    - Component initialization status
    - Configuration settings
    - CUDA availability
    - Model discovery statistics
    - Provider information
    """
    try:
        from ai_karen_engine.core.kire_kro_integration import get_integration

        integration = get_integration()
        status = await integration.get_system_status()

        return {
            "success": True,
            "status": status,
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
    - Overall system health status
    - Individual component health
    - Provider health statistics
    """
    try:
        from ai_karen_engine.core.kire_kro_integration import get_integration

        integration = get_integration()
        health = await integration.health_check()

        if health.get("status") == "healthy":
            return health
        else:
            raise HTTPException(status_code=503, detail=health)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


# ===================================
# REGISTRATION FUNCTION
# ===================================

def register_kro_routes(app):
    """Register KRO routes with FastAPI app."""
    if FASTAPI_AVAILABLE:
        app.include_router(router)
        logger.info("KRO routes registered")
    else:
        logger.warning("FastAPI not available, KRO routes not registered")
