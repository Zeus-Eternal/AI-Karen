"""
Response Core API Routes

This module provides API endpoints for the Response Core Orchestrator system,
maintaining backward compatibility with existing chat orchestrator while
adding new capabilities for model management and training operations.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from ..core.response.factory import (
    create_response_orchestrator,
    create_local_only_orchestrator,
    create_enhanced_orchestrator,
    get_global_orchestrator
)
from ..core.response.config import PipelineConfig
from ..chat.chat_orchestrator import ChatOrchestrator, ChatRequest as LegacyChatRequest, ChatResponse as LegacyChatResponse
from ..services.auth_utils import get_current_user
from ..core.dependencies import get_current_user_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/response-core", tags=["response-core"])


# Request/Response Models
class ResponseCoreRequest(BaseModel):
    """Request model for Response Core orchestrator"""
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(None, description="User identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # UI capabilities
    ui_caps: Dict[str, Any] = Field(
        default_factory=dict,
        description="UI capabilities (copilotkit, persona_set, project_name, etc.)"
    )
    
    # Configuration overrides
    config_overrides: Optional[Dict[str, Any]] = Field(
        None,
        description="Pipeline configuration overrides"
    )
    
    # Compatibility with existing chat orchestrator
    stream: bool = Field(True, description="Enable streaming response")
    include_context: bool = Field(True, description="Include memory context")
    attachments: List[str] = Field(default_factory=list, description="File attachments")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ResponseCoreResponse(BaseModel):
    """Response model for Response Core orchestrator"""
    intent: str = Field(..., description="Detected user intent")
    persona: str = Field(..., description="Selected persona")
    mood: str = Field(..., description="Sentiment analysis result")
    content: str = Field(..., description="Formatted response content")
    
    # Processing metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Processing metadata (model_used, context_tokens, etc.)"
    )
    
    # Compatibility fields
    correlation_id: str = Field(..., description="Request correlation ID")
    processing_time: float = Field(..., description="Total processing time in seconds")
    used_fallback: bool = Field(False, description="Whether fallback processing was used")
    context_used: bool = Field(False, description="Whether memory context was used")


class ModelManagementRequest(BaseModel):
    """Request model for model management operations"""
    operation: str = Field(..., description="Operation type: list, configure, download, delete")
    model_id: Optional[str] = Field(None, description="Model identifier")
    config: Optional[Dict[str, Any]] = Field(None, description="Model configuration")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters for listing")


class ModelManagementResponse(BaseModel):
    """Response model for model management operations"""
    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Operation result data")
    message: str = Field(..., description="Operation result message")


class TrainingRequest(BaseModel):
    """Request model for training operations"""
    operation: str = Field(..., description="Operation type: start, stop, status, schedule")
    model_id: Optional[str] = Field(None, description="Model to train")
    dataset_id: Optional[str] = Field(None, description="Training dataset")
    config: Optional[Dict[str, Any]] = Field(None, description="Training configuration")
    schedule: Optional[str] = Field(None, description="Cron schedule for autonomous training")


class TrainingResponse(BaseModel):
    """Response model for training operations"""
    success: bool = Field(..., description="Operation success status")
    job_id: Optional[str] = Field(None, description="Training job ID")
    status: str = Field(..., description="Training status")
    data: Dict[str, Any] = Field(default_factory=dict, description="Training data")
    message: str = Field(..., description="Operation result message")


# Dependency functions
def get_chat_orchestrator() -> ChatOrchestrator:
    """Get existing chat orchestrator instance"""
    # Import here to avoid circular dependencies
    from ..chat.chat_orchestrator import ChatOrchestrator
    from ..chat.memory_processor import MemoryProcessor
    
    # Create with default dependencies
    memory_processor = MemoryProcessor()
    return ChatOrchestrator(memory_processor=memory_processor)


def get_response_orchestrator(
    user_id: str = "default",
    tenant_id: Optional[str] = None,
    config_overrides: Optional[Dict[str, Any]] = None
):
    """Get Response Core orchestrator instance"""
    try:
        if config_overrides:
            # Create custom config
            config = PipelineConfig(**config_overrides)
            return create_response_orchestrator(user_id, tenant_id, config)
        else:
            # Use global instance
            return get_global_orchestrator(user_id, tenant_id)
    except Exception as e:
        logger.error(f"Failed to create ResponseOrchestrator: {e}")
        # Fallback to local-only orchestrator
        return create_local_only_orchestrator(user_id, tenant_id)


# API Endpoints

@router.post("/chat", response_model=ResponseCoreResponse)
async def chat_with_response_core(
    request: ResponseCoreRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process chat message using Response Core orchestrator
    
    This endpoint uses the new ResponseOrchestrator while maintaining
    compatibility with existing chat functionality.
    """
    start_time = time.time()
    correlation_id = str(uuid.uuid4())
    
    try:
        user_id = request.user_id or current_user.get("id", "anonymous")
        tenant_id = request.tenant_id or current_user.get("tenant_id")
        
        # Get orchestrator instance
        orchestrator = get_response_orchestrator(
            user_id=user_id,
            tenant_id=tenant_id,
            config_overrides=request.config_overrides
        )
        
        # Process through Response Core
        result = orchestrator.respond(
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            user_input=request.message,
            correlation_id=correlation_id
        )
        
        processing_time = time.time() - start_time
        
        # For now, return a structured response based on the formatted result
        # TODO: Update ResponseOrchestrator to return structured data
        return ResponseCoreResponse(
            intent="general_assist",  # TODO: Extract from orchestrator
            persona="assistant",      # TODO: Extract from orchestrator
            mood="neutral",          # TODO: Extract from orchestrator
            content=result,
            metadata={
                "model_used": "local",  # TODO: Extract from orchestrator
                "context_tokens": 0,    # TODO: Extract from orchestrator
                "generation_time_ms": int(processing_time * 1000)
            },
            correlation_id=correlation_id,
            processing_time=processing_time,
            used_fallback=False,  # TODO: Extract from orchestrator
            context_used=True     # TODO: Extract from orchestrator
        )
        
    except Exception as e:
        logger.error(f"Response Core chat error: {e}")
        processing_time = time.time() - start_time
        
        return ResponseCoreResponse(
            intent="error",
            persona="assistant",
            mood="apologetic",
            content=f"I apologize, but I encountered an error: {str(e)}",
            metadata={"error": str(e)},
            correlation_id=correlation_id,
            processing_time=processing_time,
            used_fallback=True,
            context_used=False
        )


@router.post("/chat/compatible")
async def chat_compatible(
    request: ResponseCoreRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Compatible chat endpoint that can use either ResponseOrchestrator or ChatOrchestrator
    
    This endpoint provides backward compatibility by falling back to the existing
    ChatOrchestrator if ResponseOrchestrator fails.
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        # Try Response Core first
        try:
            user_id = request.user_id or current_user.get("id", "anonymous")
            tenant_id = request.tenant_id or current_user.get("tenant_id")
            
            orchestrator = get_response_orchestrator(
                user_id=user_id,
                tenant_id=tenant_id,
                config_overrides=request.config_overrides
            )
            
            result = orchestrator.respond(
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                user_input=request.message,
                correlation_id=correlation_id
            )
            
            # Return in legacy format for compatibility
            return {
                "response": result,
                "correlation_id": correlation_id,
                "processing_time": 0.0,  # TODO: Get from orchestrator
                "used_fallback": False,
                "context_used": True,
                "metadata": {
                    "orchestrator": "response_core",
                    "version": "1.0"
                }
            }
            
        except Exception as e:
            logger.warning(f"Response Core failed, falling back to ChatOrchestrator: {e}")
            
            # Fallback to existing ChatOrchestrator
            chat_orchestrator = get_chat_orchestrator()
            
            # Convert request format
            legacy_request = LegacyChatRequest(
                message=request.message,
                user_id=request.user_id or current_user.get("id", "anonymous"),
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                session_id=request.session_id,
                stream=False,  # Force non-streaming for compatibility
                include_context=request.include_context,
                attachments=request.attachments,
                metadata=request.metadata
            )
            
            # Process with legacy orchestrator
            legacy_response = await chat_orchestrator.process_message(legacy_request)
            
            # Convert response format
            if isinstance(legacy_response, LegacyChatResponse):
                return {
                    "response": legacy_response.response,
                    "correlation_id": legacy_response.correlation_id,
                    "processing_time": legacy_response.processing_time,
                    "used_fallback": True,
                    "context_used": legacy_response.context_used,
                    "metadata": {
                        **legacy_response.metadata,
                        "orchestrator": "chat_orchestrator",
                        "fallback_reason": str(e)
                    }
                }
            else:
                # Handle streaming response (shouldn't happen with stream=False)
                return {
                    "response": "Streaming response not supported in compatible mode",
                    "correlation_id": correlation_id,
                    "processing_time": 0.0,
                    "used_fallback": True,
                    "context_used": False,
                    "metadata": {"error": "Unexpected streaming response"}
                }
                
    except Exception as e:
        logger.error(f"Compatible chat error: {e}")
        return {
            "response": f"I apologize, but I encountered an error: {str(e)}",
            "correlation_id": correlation_id,
            "processing_time": 0.0,
            "used_fallback": True,
            "context_used": False,
            "metadata": {"error": str(e)}
        }


@router.post("/chat/stream")
async def chat_stream(
    request: ResponseCoreRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Streaming chat endpoint using Response Core orchestrator
    
    Falls back to existing ChatOrchestrator streaming if Response Core fails.
    """
    correlation_id = str(uuid.uuid4())
    
    async def generate_response_core_stream():
        """Generate streaming response using Response Core"""
        try:
            user_id = request.user_id or current_user.get("id", "anonymous")
            tenant_id = request.tenant_id or current_user.get("tenant_id")
            
            # For now, use non-streaming Response Core and simulate streaming
            orchestrator = get_response_orchestrator(
                user_id=user_id,
                tenant_id=tenant_id,
                config_overrides=request.config_overrides
            )
            
            # Send initial metadata
            yield f"data: {json.dumps({'type': 'metadata', 'correlation_id': correlation_id, 'status': 'processing'})}\n\n"
            
            # Generate response
            result = orchestrator.respond(
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                user_input=request.message,
                correlation_id=correlation_id
            )
            
            # Stream the response word by word
            words = result.split()
            for i, word in enumerate(words):
                content = word + (" " if i < len(words) - 1 else "")
                chunk = {
                    "type": "content",
                    "content": content,
                    "correlation_id": correlation_id
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Simulate streaming delay
            
            # Send completion
            completion = {
                "type": "complete",
                "correlation_id": correlation_id,
                "metadata": {
                    "orchestrator": "response_core",
                    "used_fallback": False
                }
            }
            yield f"data: {json.dumps(completion)}\n\n"
            
        except Exception as e:
            logger.error(f"Response Core streaming error: {e}")
            error_chunk = {
                "type": "error",
                "content": f"Response Core error: {str(e)}",
                "correlation_id": correlation_id
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    async def generate_fallback_stream():
        """Generate streaming response using existing ChatOrchestrator"""
        try:
            chat_orchestrator = get_chat_orchestrator()
            
            # Convert request format
            legacy_request = LegacyChatRequest(
                message=request.message,
                user_id=request.user_id or current_user.get("id", "anonymous"),
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                session_id=request.session_id,
                stream=True,
                include_context=request.include_context,
                attachments=request.attachments,
                metadata=request.metadata
            )
            
            # Process with legacy orchestrator
            stream_generator = await chat_orchestrator.process_message(legacy_request)
            
            # Forward stream chunks
            async for chunk in stream_generator:
                chunk_data = {
                    "type": chunk.type,
                    "content": chunk.content,
                    "correlation_id": chunk.correlation_id,
                    "metadata": {
                        **chunk.metadata,
                        "orchestrator": "chat_orchestrator",
                        "used_fallback": True
                    }
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
        except Exception as e:
            logger.error(f"Fallback streaming error: {e}")
            error_chunk = {
                "type": "error",
                "content": f"Fallback streaming error: {str(e)}",
                "correlation_id": correlation_id
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    try:
        # Try Response Core streaming first
        return StreamingResponse(
            generate_response_core_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        logger.warning(f"Response Core streaming failed, using fallback: {e}")
        # Fallback to existing streaming
        return StreamingResponse(
            generate_fallback_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )


@router.post("/models", response_model=ModelManagementResponse)
async def manage_models(
    request: ModelManagementRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Model management endpoint for system models, HuggingFace models, and training
    """
    try:
        # Check admin permissions for model management
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin permissions required for model management")
        
        if request.operation == "list":
            # List available models
            # TODO: Implement actual model listing
            models = {
                "system_models": [
                    {"id": "llama-cpp", "status": "available", "type": "llm"},
                    {"id": "distilbert-base-uncased", "status": "available", "type": "transformer"},
                    {"id": "basic_cls", "status": "available", "type": "classifier"}
                ],
                "huggingface_models": [],
                "custom_models": []
            }
            
            return ModelManagementResponse(
                success=True,
                data=models,
                message="Models listed successfully"
            )
            
        elif request.operation == "configure":
            if not request.model_id or not request.config:
                raise HTTPException(status_code=400, detail="Model ID and config required for configuration")
            
            # TODO: Implement model configuration
            return ModelManagementResponse(
                success=True,
                data={"model_id": request.model_id, "config": request.config},
                message=f"Model {request.model_id} configured successfully"
            )
            
        elif request.operation == "download":
            if not request.model_id:
                raise HTTPException(status_code=400, detail="Model ID required for download")
            
            # TODO: Implement model download
            return ModelManagementResponse(
                success=True,
                data={"model_id": request.model_id, "status": "downloading"},
                message=f"Download started for model {request.model_id}"
            )
            
        elif request.operation == "delete":
            if not request.model_id:
                raise HTTPException(status_code=400, detail="Model ID required for deletion")
            
            # TODO: Implement model deletion
            return ModelManagementResponse(
                success=True,
                data={"model_id": request.model_id},
                message=f"Model {request.model_id} deleted successfully"
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model management error: {e}")
        return ModelManagementResponse(
            success=False,
            data={},
            message=f"Model management error: {str(e)}"
        )


@router.post("/training", response_model=TrainingResponse)
async def manage_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Training management endpoint for autonomous learning and model training
    """
    try:
        # Check admin permissions for training operations
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin permissions required for training operations")
        
        if request.operation == "start":
            if not request.model_id:
                raise HTTPException(status_code=400, detail="Model ID required for training")
            
            job_id = str(uuid.uuid4())
            
            # TODO: Implement actual training start
            # background_tasks.add_task(start_training_job, job_id, request.model_id, request.config)
            
            return TrainingResponse(
                success=True,
                job_id=job_id,
                status="started",
                data={"model_id": request.model_id},
                message=f"Training started for model {request.model_id}"
            )
            
        elif request.operation == "stop":
            if not request.model_id:
                raise HTTPException(status_code=400, detail="Model ID required to stop training")
            
            # TODO: Implement training stop
            return TrainingResponse(
                success=True,
                job_id=None,
                status="stopped",
                data={"model_id": request.model_id},
                message=f"Training stopped for model {request.model_id}"
            )
            
        elif request.operation == "status":
            # TODO: Implement training status check
            return TrainingResponse(
                success=True,
                job_id=None,
                status="idle",
                data={"active_jobs": 0},
                message="Training status retrieved"
            )
            
        elif request.operation == "schedule":
            if not request.schedule:
                raise HTTPException(status_code=400, detail="Schedule required for autonomous training")
            
            # TODO: Implement training scheduling
            return TrainingResponse(
                success=True,
                job_id=None,
                status="scheduled",
                data={"schedule": request.schedule},
                message="Autonomous training scheduled"
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training management error: {e}")
        return TrainingResponse(
            success=False,
            job_id=None,
            status="error",
            data={},
            message=f"Training management error: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Response Core system
    """
    try:
        # Check Response Core orchestrator health
        orchestrator = get_global_orchestrator()
        diagnostics = orchestrator.diagnostics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "response_core": "available",
            "diagnostics": diagnostics,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }


@router.get("/config")
async def get_config(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current Response Core configuration
    """
    try:
        # TODO: Get actual configuration from orchestrator
        config = {
            "local_only": True,
            "enable_copilotkit": True,
            "enable_onboarding": True,
            "enable_persona_detection": True,
            "enable_memory_persistence": True,
            "enable_metrics": True,
            "enable_audit_logging": True,
            "max_context_tokens": 8192,
            "persona_default": "assistant"
        }
        
        return {
            "success": True,
            "config": config,
            "message": "Configuration retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        return {
            "success": False,
            "config": {},
            "message": f"Config retrieval error: {str(e)}"
        }


@router.post("/config")
async def update_config(
    config_updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update Response Core configuration
    """
    try:
        # Check admin permissions
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin permissions required for configuration updates")
        
        # TODO: Implement actual configuration updates
        logger.info(f"Configuration update requested: {config_updates}")
        
        return {
            "success": True,
            "updates": config_updates,
            "message": "Configuration updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config update error: {e}")
        return {
            "success": False,
            "updates": {},
            "message": f"Config update error: {str(e)}"
        }