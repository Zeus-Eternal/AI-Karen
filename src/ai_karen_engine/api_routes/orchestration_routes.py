"""
API Routes for LangGraph Orchestration

This module provides REST API endpoints for the LangGraph orchestration system
with support for both synchronous and streaming responses.
"""

import asyncio
import contextlib
import json
import logging
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from importlib import metadata
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - compatibility for 3.10
    import tomli as tomllib  # type: ignore

from ..core.langgraph_orchestrator import (
    get_default_orchestrator,
    OrchestrationConfig,
    LangGraphOrchestrator
)
from ..core.streaming_integration import get_streaming_manager, StreamingManager
from ..core.response.factory import get_global_orchestrator, create_response_orchestrator
from ..services.auth_utils import get_current_user
from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.services.metrics_service import get_metrics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])

_METRICS_INTERVAL_SECONDS = 30
_metrics_task: Optional[asyncio.Task] = None


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
    failed_sessions: int = Field(..., description="Sessions that ended with errors")
    average_latency: float = Field(..., description="Average processing latency in seconds")
    p95_latency: float = Field(..., description="95th percentile latency in seconds")
    metrics_backend: str = Field(..., description="Active metrics backend")
    last_error: Optional[str] = Field(None, description="Most recent error message")
    last_error_at: Optional[datetime] = Field(None, description="Timestamp of the most recent error")


def _resolve_version() -> str:
    """Resolve Kari orchestration version from package metadata or pyproject."""

    package_candidates = ("ai-karen", "ai_karen", "ai-karen-engine")
    for candidate in package_candidates:
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue

    project_root = Path(__file__).resolve().parents[3]
    pyproject_path = project_root / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as handle:
            data = tomllib.load(handle)
    except Exception:
        return "0.0.0"

    if "tool" in data and "poetry" in data["tool"]:
        return data["tool"]["poetry"].get("version", "0.0.0")
    if "project" in data:
        return data["project"].get("version", "0.0.0")
    return "0.0.0"


ORCHESTRATION_VERSION = _resolve_version()


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
    metrics_service = get_metrics_service()
    start_time = datetime.now(timezone.utc)
    
    try:
        user_id = current_user.get("id") or current_user.get("user_id", "anonymous")
        
        # Convert message to LangChain format
        messages = [HumanMessage(content=request.message)]
        
        # Precompute KIRE decision via LLMRegistry (observability + metadata)
        kire_meta = {}
        try:
            reg = get_registry()
            routed = await reg.get_provider_with_routing(
                user_ctx={"user_id": user_id},
                query=request.message,
                task_type="chat",
                khrp_step="output_rendering",
                requirements={}
            )
            decision = routed.get("decision")
            if decision:
                kire_meta = {
                    "provider": decision.provider,
                    "model": decision.model,
                    "reason": decision.reasoning,
                    "confidence": decision.confidence,
                    "fallback_chain": decision.fallback_chain,
                }
        except Exception:
            # Non-fatal: proceed without KIRE metadata if routing fails
            kire_meta = {}

        # Process through orchestration
        result = await orchestrator.process(
            messages=messages,
            user_id=user_id,
            session_id=request.session_id,
            config=request.config
        )

        # Extract response
        response_text = result.get("response", "I apologize, but I couldn't generate a response.")
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        metrics_service.record_total_turn_time(
            processing_time,
            endpoint="orchestration.chat",
            status="success" if not result.get("errors") else "error",
        )

        runtime_status = await orchestrator.get_runtime_status()
        success_rate = (
            1 - (runtime_status["failed_sessions"] / runtime_status["total_processed"])
            if runtime_status["total_processed"]
            else 1.0
        )
        metrics_service.update_turn_health(
            success_rate=success_rate,
            error_rate=1 - success_rate,
            endpoint="orchestration.chat",
            error_type="orchestration_error",
        )

        return ChatResponse(
            response=response_text,
            session_id=result.get("session_id", request.session_id or "unknown"),
            metadata={
                **result.get("response_metadata", {}),
                "kire_metadata": kire_meta,
            },
            processing_time=processing_time,
            errors=result.get("errors", []),
            warnings=result.get("warnings", [])
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        metrics_service.record_total_turn_time(
            processing_time,
            endpoint="orchestration.chat",
            status="error",
        )

        runtime_status = await orchestrator.get_runtime_status()
        success_rate = (
            1 - (runtime_status["failed_sessions"] / runtime_status["total_processed"])
            if runtime_status["total_processed"]
            else 0.0
        )
        metrics_service.update_turn_health(
            success_rate=success_rate,
            error_rate=1 - success_rate,
            endpoint="orchestration.chat",
            error_type="orchestration_error",
        )

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
                    # Attach KIRE metadata in the first metadata chunk if possible
                    if isinstance(chunk, dict) and chunk.get("type") == "metadata":
                        try:
                            reg = get_registry()
                            routed = await reg.get_provider_with_routing(
                                user_ctx={"user_id": user_id},
                                query=request.message,
                                task_type="chat",
                                khrp_step="output_rendering",
                                requirements={}
                            )
                            decision = routed.get("decision")
                            if decision:
                                meta = chunk.get("data") or chunk.get("metadata") or {}
                                meta = {**meta, "kire": {
                                    "provider": decision.provider,
                                    "model": decision.model,
                                    "reason": decision.reasoning,
                                    "confidence": decision.confidence,
                                }}
                                chunk["data"] = meta
                        except Exception:
                            pass
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
                # End of stream
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {
                    "type": "error",
                    "content": f"Streaming error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
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
        runtime_status = await orchestrator.get_runtime_status()
        metrics_service = get_metrics_service()

        success_rate = (
            1 - (runtime_status["failed_sessions"] / runtime_status["total_processed"])
            if runtime_status["total_processed"]
            else 1.0
        )
        metrics_service.update_system_health(
            active_connections=runtime_status["active_sessions"],
            service="orchestration",
        )
        metrics_service.update_turn_health(
            success_rate=success_rate,
            error_rate=1 - success_rate,
            endpoint="orchestration",
            error_type="orchestration_error",
        )

        metrics_summary = metrics_service.get_stats_summary()
        last_error = runtime_status.get("last_error")

        status_label = "healthy"
        if last_error and last_error.get("timestamp"):
            error_age = datetime.now(timezone.utc) - last_error["timestamp"]
            if error_age <= timedelta(minutes=5):
                status_label = "degraded"

        return OrchestrationStatus(
            status=status_label,
            version=ORCHESTRATION_VERSION,
            active_sessions=runtime_status["active_sessions"],
            total_processed=runtime_status["total_processed"],
            uptime=runtime_status["uptime"],
            failed_sessions=runtime_status["failed_sessions"],
            average_latency=runtime_status["average_latency"],
            p95_latency=runtime_status["p95_latency"],
            metrics_backend=metrics_summary.get("metrics_backend", "unknown"),
            last_error=last_error.get("message") if last_error else None,
            last_error_at=last_error.get("timestamp") if last_error else None,
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
        
        config_updates = request.dict(exclude_unset=True)
        sanitized_updates = {
            key: value
            for key, value in config_updates.items()
            if value is not None
        }

        if not sanitized_updates:
            return {
                "message": "No configuration changes provided",
                "updates": {},
            }

        updated_config = await orchestrator.update_configuration(sanitized_updates)
        metrics_service = get_metrics_service()
        runtime_status = await orchestrator.get_runtime_status()

        metrics_service.update_system_health(
            active_connections=runtime_status["active_sessions"],
            service="orchestration",
        )

        logger.info(
            "Configuration updated for LangGraph orchestrator",
            extra={"updates": sanitized_updates},
        )

        return {
            "message": "Configuration updated successfully",
            "updates": asdict(updated_config),
        }
        
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
        
        analysis = await orchestrator.run_dry_run_analysis(
            message=request.message,
            session_id=request.session_id,
            user=current_user,
            context=request.context,
        )

        return {
            "dry_run": True,
            "analysis": analysis,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dry-run error: {e}")
        raise HTTPException(status_code=500, detail=f"Dry-run error: {str(e)}")


# Background task for metrics collection
async def collect_metrics(orchestrator: LangGraphOrchestrator) -> None:
    """Background task to collect orchestration metrics"""

    metrics_service = get_metrics_service()

    while True:
        try:
            snapshot = await orchestrator.get_runtime_status()
            metrics_service.record_orchestrator_snapshot(snapshot)
            await asyncio.sleep(_METRICS_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Metrics collection task cancelled")
            raise
        except Exception as exc:
            logger.error(f"Metrics collection error: {exc}")
            await asyncio.sleep(_METRICS_INTERVAL_SECONDS)


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

        global _metrics_task
        if _metrics_task is None or _metrics_task.done():
            _metrics_task = asyncio.create_task(collect_metrics(orchestrator))

        logger.info("LangGraph orchestration system initialized successfully")

    except Exception as e:
        logger.error(f"Orchestration startup error: {e}")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup orchestration system on shutdown"""
    try:
        logger.info("Shutting down LangGraph orchestration system...")

        global _metrics_task
        if _metrics_task is not None:
            _metrics_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await _metrics_task
            _metrics_task = None

        orchestrator = get_default_orchestrator()
        await orchestrator.shutdown()

        logger.info("LangGraph orchestration system shutdown complete")

    except Exception as e:
        logger.error(f"Orchestration shutdown error: {e}")
