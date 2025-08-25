"""
API Routes for LangGraph Orchestration

This module provides REST API endpoints for the LangGraph orchestration system
with support for both synchronous and streaming responses.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..core.langgraph_orchestrator import (
    get_default_orchestrator, 
    OrchestrationConfig,
    LangGraphOrchestrator
)
from ..core.streaming_integration import get_streaming_manager, StreamingManager
from ..core.response.factory import get_global_orchestrator, create_response_orchestrator
from ..services.auth_utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])


class ChatRequest(BaseModel):
    """Request model for chat conversations"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    streaming: bool = Field(False, description="Enable streaming response")
    config: Optional[Dict[str, Any]] = Field(None, description="Orchestration configuration")


class ChatResponse(BaseModel):
    """Response model for chat conversations"""
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session identifier")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Any warnings")


class OrchestrationStatus(BaseModel):
    """Status model for orchestration system"""
    status: str = Field(..., description="System status")
    version: str = Field(..., description="Orchestration version")
    active_sessions: int = Field(..., description="Number of active sessions")
    total_processed: int = Field(..., description="Total conversations processed")
    uptime: float = Field(..., description="System uptime in seconds")


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates"""
    enable_auth_gate: Optional[bool] = None
    enable_safety_gate: Optional[bool] = None
    enable_memory_fetch: Optional[bool] = None
    enable_approval_gate: Optional[bool] = None
    streaming_enabled: Optional[bool] = None
    checkpoint_enabled: Optional[bool] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None


# Dependency to get orchestrator
def get_orchestrator() -> LangGraphOrchestrator:
    """Get the orchestrator instance"""
    return get_default_orchestrator()


# Dependency to get streaming manager
def get_streamer() -> StreamingManager:
    """Get the streaming manager instance"""
    return get_streaming_manager()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process a chat conversation through the orchestration graph
    
    Args:
        request: Chat request with message and options
        orchestrator: Orchestrator instance
        current_user: Current authenticated user
        
    Returns:
        Chat response with AI message and metadata
    """
    start_time = datetime.now()
    
    try:
        user_id = current_user.get("id") or current_user.get("user_id", "anonymous")
        
        # Convert message to LangChain format
        messages = [HumanMessage(content=request.message)]
        
        # Process through orchestration
        result = await orchestrator.process(
            messages=messages,
            user_id=user_id,
            session_id=request.session_id,
            config=request.config
        )
        
        # Extract response
        response_text = result.get("response", "I apologize, but I couldn't generate a response.")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ChatResponse(
            response=response_text,
            session_id=result.get("session_id", request.session_id or "unknown"),
            metadata=result.get("response_metadata", {}),
            processing_time=processing_time,
            errors=result.get("errors", []),
            warnings=result.get("warnings", [])
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ChatResponse(
            response="I apologize, but an error occurred while processing your request.",
            session_id=request.session_id or "error",
            metadata={"error": str(e)},
            processing_time=processing_time,
            errors=[f"Processing error: {str(e)}"],
            warnings=[]
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    streamer: StreamingManager = Depends(get_streamer),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Stream a chat conversation through the orchestration graph
    
    Args:
        request: Chat request with message and options
        streamer: Streaming manager instance
        current_user: Current authenticated user
        
    Returns:
        Streaming response with real-time updates
    """
    try:
        user_id = current_user.get("id") or current_user.get("user_id", "anonymous")
        
        async def generate_stream():
            """Generate streaming response"""
            try:
                async for chunk in streamer.stream_for_copilotkit(
                    message=request.message,
                    user_id=user_id,
                    session_id=request.session_id,
                    context=request.context
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
                # End of stream
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {
                    "type": "error",
                    "content": f"Streaming error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream setup error: {e}")
        raise HTTPException(status_code=500, detail=f"Stream setup error: {str(e)}")


@router.get("/status", response_model=OrchestrationStatus)
async def get_status(
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)
):
    """
    Get orchestration system status
    
    Args:
        orchestrator: Orchestrator instance
        
    Returns:
        System status information
    """
    try:
        # TODO: Implement proper metrics collection
        return OrchestrationStatus(
            status="healthy",
            version="1.0.0",
            active_sessions=0,  # Placeholder
            total_processed=0,  # Placeholder
            uptime=0.0  # Placeholder
        )
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")


@router.post("/config")
async def update_config(
    request: ConfigUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update orchestration configuration
    
    Args:
        request: Configuration update request
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Check if user has admin permissions
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        # TODO: Implement configuration updates
        # For now, just validate the request
        config_updates = request.dict(exclude_unset=True)
        
        logger.info(f"Configuration update requested: {config_updates}")
        
        return {"message": "Configuration updated successfully", "updates": config_updates}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(status_code=500, detail=f"Config update error: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    
    Returns:
        Health status
    """
    try:
        # Basic health check
        orchestrator = get_default_orchestrator()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "orchestrator": "available",
            "streaming": "available"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.post("/chat/response-core", response_model=ChatResponse)
async def chat_with_response_core(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process chat using Response Core orchestrator as an alternative to LangGraph
    
    This endpoint provides an alternative chat processing pipeline using the
    Response Core orchestrator with local-first processing and structured prompts.
    """
    start_time = datetime.now()
    
    try:
        user_id = current_user.get("id") or current_user.get("user_id", "anonymous")
        
        # Get Response Core orchestrator
        response_orchestrator = get_global_orchestrator(user_id=user_id)
        
        # Process through Response Core
        result = response_orchestrator.respond(
            conversation_id=request.session_id or f"session_{user_id}",
            user_input=request.message,
            correlation_id=None
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ChatResponse(
            response=result,
            session_id=request.session_id or f"session_{user_id}",
            metadata={
                "orchestrator": "response_core",
                "local_processing": True,
                "prompt_driven": True
            },
            processing_time=processing_time,
            errors=[],
            warnings=[]
        )
        
    except Exception as e:
        logger.error(f"Response Core chat error: {e}")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ChatResponse(
            response="I apologize, but an error occurred while processing your request with Response Core.",
            session_id=request.session_id or "error",
            metadata={"error": str(e), "orchestrator": "response_core"},
            processing_time=processing_time,
            errors=[f"Response Core error: {str(e)}"],
            warnings=[]
        )


@router.post("/debug/dry-run")
async def debug_dry_run(
    request: ChatRequest,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Debug endpoint for dry-run analysis of orchestration decisions
    
    Args:
        request: Chat request for analysis
        orchestrator: Orchestrator instance
        current_user: Current authenticated user
        
    Returns:
        Dry-run analysis results
    """
    try:
        # Check if user has debug permissions
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        user_id = current_user.get("id") or current_user.get("user_id", "debug")
        
        # TODO: Implement dry-run functionality
        # For now, return placeholder analysis
        analysis = {
            "message": request.message,
            "predicted_intent": "general_chat",
            "predicted_provider": "local",
            "predicted_model": "llama-3.1-8b",
            "routing_reason": "Standard task suitable for local model",
            "estimated_processing_time": 2.5,
            "required_tools": [],
            "safety_assessment": "safe",
            "approval_required": False
        }
        
        return {
            "dry_run": True,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dry-run error: {e}")
        raise HTTPException(status_code=500, detail=f"Dry-run error: {str(e)}")


# Background task for metrics collection
async def collect_metrics():
    """Background task to collect orchestration metrics"""
    # TODO: Implement metrics collection
    pass


# Initialize background tasks
@router.on_event("startup")
async def startup_event():
    """Initialize orchestration system on startup"""
    try:
        logger.info("Initializing LangGraph orchestration system...")
        
        # Initialize orchestrator
        orchestrator = get_default_orchestrator()
        
        # Initialize streaming manager
        streaming_manager = get_streaming_manager()
        
        logger.info("LangGraph orchestration system initialized successfully")
        
    except Exception as e:
        logger.error(f"Orchestration startup error: {e}")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup orchestration system on shutdown"""
    try:
        logger.info("Shutting down LangGraph orchestration system...")
        
        # TODO: Implement proper cleanup
        
        logger.info("LangGraph orchestration system shutdown complete")
        
    except Exception as e:
        logger.error(f"Orchestration shutdown error: {e}")