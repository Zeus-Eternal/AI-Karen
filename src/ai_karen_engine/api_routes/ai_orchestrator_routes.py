"""
FastAPI routes for AI Orchestrator service integration.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..services.ai_orchestrator import (
    AIOrchestrator,
    FlowType,
    FlowInput,
    FlowOutput
)
from ..core.dependencies import get_ai_orchestrator_service
# Temporarily disable auth imports for web UI integration
# from ..core.auth import get_current_user, get_tenant_id

router = APIRouter(prefix="/api/ai", tags=["ai-orchestrator"])


# Request/Response Models
class ProcessFlowRequest(BaseModel):
    """Request model for processing AI flows."""
    flow_type: FlowType = Field(..., description="Type of flow to process")
    prompt: str = Field(..., description="User prompt")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    user_settings: Dict[str, Any] = Field(default_factory=dict, description="User settings")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session ID")


class DecideActionRequest(BaseModel):
    """Request model for decide action flow."""
    prompt: str = Field(..., description="User prompt")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    user_settings: Dict[str, Any] = Field(default_factory=dict, description="User settings")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session ID")


class ConversationProcessingRequest(BaseModel):
    """Request model for conversation processing flow."""
    prompt: str = Field(..., description="User prompt")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    user_settings: Dict[str, Any] = Field(default_factory=dict, description="User settings")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session ID")
    include_memories: bool = Field(True, description="Include memory integration")
    include_insights: bool = Field(True, description="Include AI insights")


class FlowResponse(BaseModel):
    """Response model for AI flow processing."""
    response: str
    requires_plugin: bool = False
    plugin_to_execute: Optional[str] = None
    plugin_parameters: Optional[Dict[str, Any]] = None
    memory_to_store: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = None
    ai_data: Optional[Dict[str, Any]] = None
    proactive_suggestion: Optional[str] = None
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    confidence_score: Optional[float] = None


class AvailableFlowsResponse(BaseModel):
    """Response model for available flows."""
    flows: List[Dict[str, Any]]
    total_count: int


class FlowMetricsResponse(BaseModel):
    """Response model for flow metrics."""
    total_flows_processed: int
    flows_by_type: Dict[str, int]
    average_processing_time: float
    success_rate: float
    error_rate: float
    recent_activity: List[Dict[str, Any]]


@router.post("/process-flow", response_model=FlowResponse)
async def process_flow(
    request: ProcessFlowRequest,
    ai_orchestrator: AIOrchestrator = Depends(get_ai_orchestrator_service)
):
    """Process an AI flow with the given input."""
    try:
        # Create flow input
        flow_input = FlowInput(
            prompt=request.prompt,
            conversation_history=request.conversation_history,
            user_settings=request.user_settings,
            context=request.context,
            user_id="anonymous",
            session_id=request.session_id
        )
        
        # Process the flow
        start_time = datetime.utcnow()
        result = await ai_orchestrator.process_flow(request.flow_type, flow_input)
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return FlowResponse(
            response=result.response,
            requires_plugin=result.requires_plugin,
            plugin_to_execute=result.plugin_to_execute,
            plugin_parameters=result.plugin_parameters,
            memory_to_store=result.memory_to_store,
            suggested_actions=result.suggested_actions,
            ai_data=result.ai_data,
            proactive_suggestion=result.proactive_suggestion,
            processing_time_ms=int(processing_time),
            model_used=result.ai_data.get("model_used") if result.ai_data else None,
            confidence_score=result.ai_data.get("confidence") if result.ai_data else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process flow: {str(e)}")


@router.post("/decide-action", response_model=FlowResponse)
async def decide_action(
    request: DecideActionRequest,
    
    
    ai_orchestrator: AIOrchestrator = Depends(get_ai_orchestrator_service)
):
    """Process decision-making flow."""
    try:
        # Create flow input
        flow_input = FlowInput(
            prompt=request.prompt,
            conversation_history=request.conversation_history,
            user_settings=request.user_settings,
            context=request.context,
            user_id="anonymous",
            session_id=request.session_id
        )
        
        # Process decide action flow
        start_time = datetime.utcnow()
        result = await ai_orchestrator.decide_action(flow_input)
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return FlowResponse(
            response=result.response,
            requires_plugin=result.requires_plugin,
            plugin_to_execute=result.plugin_to_execute,
            plugin_parameters=result.plugin_parameters,
            memory_to_store=result.memory_to_store,
            suggested_actions=result.suggested_actions,
            ai_data=result.ai_data,
            proactive_suggestion=result.proactive_suggestion,
            processing_time_ms=int(processing_time),
            model_used=result.ai_data.get("model_used") if result.ai_data else None,
            confidence_score=result.ai_data.get("confidence") if result.ai_data else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process decide action: {str(e)}")


@router.post("/conversation-processing", response_model=FlowResponse)
async def conversation_processing(
    request: ConversationProcessingRequest,
    
    
    ai_orchestrator: AIOrchestrator = Depends(get_ai_orchestrator_service)
):
    """Process conversation with memory integration and AI insights."""
    try:
        # Create flow input with additional context
        context = request.context or {}
        context.update({
            "include_memories": request.include_memories,
            "include_insights": request.include_insights,
            "tenant_id": tenant_id
        })
        
        flow_input = FlowInput(
            prompt=request.prompt,
            conversation_history=request.conversation_history,
            user_settings=request.user_settings,
            context=context,
            user_id="anonymous",
            session_id=request.session_id
        )
        
        # Process conversation flow
        start_time = datetime.utcnow()
        result = await ai_orchestrator.conversation_processing_flow(flow_input)
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return FlowResponse(
            response=result.response,
            requires_plugin=result.requires_plugin,
            plugin_to_execute=result.plugin_to_execute,
            plugin_parameters=result.plugin_parameters,
            memory_to_store=result.memory_to_store,
            suggested_actions=result.suggested_actions,
            ai_data=result.ai_data,
            proactive_suggestion=result.proactive_suggestion,
            processing_time_ms=int(processing_time),
            model_used=result.ai_data.get("model_used") if result.ai_data else None,
            confidence_score=result.ai_data.get("confidence") if result.ai_data else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process conversation: {str(e)}")


@router.get("/flows", response_model=AvailableFlowsResponse)
async def get_available_flows(
    ai_orchestrator: AIOrchestrator = Depends(get_ai_orchestrator_service)
):
    """Get list of available AI flows."""
    try:
        flows = []
        
        # Add available flow types
        for flow_type in FlowType:
            flow_info = {
                "type": flow_type.value,
                "name": flow_type.value.replace("_", " ").title(),
                "description": _get_flow_description(flow_type),
                "parameters": _get_flow_parameters(flow_type)
            }
            flows.append(flow_info)
        
        return AvailableFlowsResponse(
            flows=flows,
            total_count=len(flows)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available flows: {str(e)}")


@router.get("/metrics", response_model=FlowMetricsResponse)
async def get_flow_metrics(
    ai_orchestrator: AIOrchestrator = Depends(get_ai_orchestrator_service)
):
    """Get AI orchestrator metrics."""
    try:
        metrics = ai_orchestrator.get_metrics()
        
        return FlowMetricsResponse(
            total_flows_processed=metrics.get("total_flows_processed", 0),
            flows_by_type=metrics.get("flows_by_type", {}),
            average_processing_time=metrics.get("average_processing_time", 0.0),
            success_rate=metrics.get("success_rate", 0.0),
            error_rate=metrics.get("error_rate", 0.0),
            recent_activity=metrics.get("recent_activity", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/generate-starter")
async def generate_starter_prompts():
    """Generate starter prompts for the web UI."""
    try:
        # Return some default starter prompts for now
        starter_prompts = [
            "What's the weather like today?",
            "Tell me about the latest news",
            "Help me organize my tasks",
            "What can you help me with?",
            "Show me my recent conversations"
        ]
        
        return {
            "prompts": starter_prompts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate starter prompts: {str(e)}")


@router.get("/health")
async def health_check(
    ai_orchestrator: AIOrchestrator = Depends(get_ai_orchestrator_service)
):
    """Health check for AI orchestrator service."""
    try:
        if hasattr(ai_orchestrator, 'health_check'):
            health_result = await ai_orchestrator.health_check()
            return health_result
        else:
            return {
                "status": "healthy",
                "service": "ai_orchestrator",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ai_orchestrator",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def _get_flow_description(flow_type: FlowType) -> str:
    """Get description for a flow type."""
    descriptions = {
        FlowType.DECIDE_ACTION: "Analyzes user input and decides what action to take, including tool/plugin execution",
        FlowType.CONVERSATION_PROCESSING: "Processes conversations with memory integration and proactive suggestions",
        FlowType.CONVERSATION_SUMMARY: "Generates summaries of conversation history"
    }
    return descriptions.get(flow_type, "AI processing flow")


def _get_flow_parameters(flow_type: FlowType) -> Dict[str, Any]:
    """Get parameters for a flow type."""
    base_params = {
        "prompt": {"type": "string", "required": True, "description": "User input prompt"},
        "conversation_history": {"type": "array", "required": False, "description": "Previous conversation messages"},
        "user_settings": {"type": "object", "required": False, "description": "User preferences and settings"},
        "context": {"type": "object", "required": False, "description": "Additional context data"},
        "session_id": {"type": "string", "required": False, "description": "Session identifier"}
    }
    
    if flow_type == FlowType.CONVERSATION_PROCESSING:
        base_params.update({
            "include_memories": {"type": "boolean", "required": False, "description": "Include memory integration"},
            "include_insights": {"type": "boolean", "required": False, "description": "Include AI insights"}
        })
   
    
    return base_params