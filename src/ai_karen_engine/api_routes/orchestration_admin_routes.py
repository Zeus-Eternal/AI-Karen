"""
API Routes for orchestration admin diagnostics and compatibility ingress.

Standard chat lifecycle authority lives with ChatOrchestrator. This module keeps
legacy compatibility endpoints for orchestration callers plus LangGraph-specific
diagnostic/admin surfaces.
"""

import asyncio
import contextlib
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from importlib import metadata
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field
try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - compatibility for 3.10
    import tomli as tomllib  # type: ignore

from ..core.langgraph_orchestrator import (
    get_default_orchestrator,
    LangGraphOrchestrator,
)
from ai_karen_engine.services.auth_utils import get_current_user
from ai_karen_engine.chat.ChatOrchestrator import (
    ChatRequest as CanonicalChatRequest,
    ChatResponse as CanonicalChatResponse,
    ChatStreamChunk,
    ProcessingStatus,
)
from ai_karen_engine.chat.factory import get_chat_orchestrator
from ai_karen_engine.services.metrics_service import get_metrics_service

logger = logging.getLogger(__name__)

compatibility_router = APIRouter(
    prefix="/api/orchestration", tags=["orchestration-compat"]
)
admin_router = APIRouter(
    prefix="/api/admin/orchestration", tags=["orchestration-admin"]
)

_METRICS_INTERVAL_SECONDS = 30
_metrics_task: Optional[asyncio.Task] = None


async def _start_orchestration_runtime() -> None:
    """Initialize LangGraph orchestration runtime support for admin diagnostics."""
    global _metrics_task
    logger.info("Initializing LangGraph orchestration system...")
    orchestrator = get_default_orchestrator()
    if _metrics_task is None or _metrics_task.done():
        _metrics_task = asyncio.create_task(collect_metrics(orchestrator))
    logger.info("LangGraph orchestration system initialized successfully")


async def _stop_orchestration_runtime() -> None:
    """Shutdown LangGraph orchestration runtime support for admin diagnostics."""
    global _metrics_task
    logger.info("Shutting down LangGraph orchestration system...")
    if _metrics_task is not None:
        _metrics_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _metrics_task
        _metrics_task = None
    orchestrator = get_default_orchestrator()
    await orchestrator.shutdown()
    logger.info("LangGraph orchestration system shutdown complete")


@asynccontextmanager
async def orchestration_router_lifespan(app):
    """Router lifespan for orchestration diagnostics and compatibility endpoints."""
    try:
        await _start_orchestration_runtime()
    except Exception as e:
        logger.error(f"Orchestration startup error: {e}")
    try:
        yield
    finally:
        try:
            await _stop_orchestration_runtime()
        except Exception as e:
            logger.error(f"Orchestration shutdown error: {e}")


class ChatRequest(BaseModel):
    """Request model for chat conversations"""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    streaming: bool = Field(False, description="Enable streaming response")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Orchestration configuration"
    )


class ChatResponse(BaseModel):
    """Response model for chat conversations"""

    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session identifier")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )
    warnings: List[str] = Field(default_factory=list, description="Any warnings")


class OrchestrationStatus(BaseModel):
    """Status model for orchestration system"""

    status: str = Field(..., description="System status")
    version: str = Field(..., description="Orchestration version")
    active_sessions: int = Field(..., description="Number of active sessions")
    total_processed: int = Field(..., description="Total conversations processed")
    uptime: float = Field(..., description="System uptime in seconds")
    failed_sessions: int = Field(..., description="Sessions that ended with errors")
    average_latency: float = Field(
        ..., description="Average processing latency in seconds"
    )
    p95_latency: float = Field(..., description="95th percentile latency in seconds")
    metrics_backend: str = Field(..., description="Active metrics backend")
    last_error: Optional[str] = Field(None, description="Most recent error message")
    last_error_at: Optional[datetime] = Field(
        None, description="Timestamp of the most recent error"
    )


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


def _build_compatibility_chat_request(
    request: ChatRequest,
    current_user: Dict[str, Any],
    *,
    streaming: bool = False,
) -> CanonicalChatRequest:
    """Normalize legacy orchestration route payloads into the canonical chat request."""
    user_id = current_user.get("id") or current_user.get("user_id", "anonymous")
    context = dict(request.context or {})
    conversation_id = str(
        request.session_id
        or context.get("conversation_id")
        or context.get("thread_id")
        or context.get("session_id")
        or f"session_{user_id}"
    )
    session_id = str(request.session_id or context.get("session_id") or conversation_id)
    correlation_id = str(
        context.get("correlation_id") or f"orchestration-{conversation_id}"
    )

    return CanonicalChatRequest(
        correlation_id=correlation_id,
        message=request.message,
        user_id=user_id,
        tenant_id=context.get("tenant_id"),
        org_id=context.get("org_id"),
        conversation_id=conversation_id,
        session_id=session_id,
        streaming=streaming,
        stream=streaming,
        metadata={
            "source": "orchestration_routes",
            "compatibility_route": "orchestration",
            "legacy_config": request.config or {},
            **context,
        },
    )


def _translate_chat_response(
    chat_response: CanonicalChatResponse,
    *,
    session_id: str,
    compatibility_route: str,
) -> ChatResponse:
    """Translate canonical chat output into the legacy orchestration route envelope."""
    warnings = list(chat_response.metadata.get("warnings", []))
    warnings.append(
        "Legacy /api/orchestration/chat* compatibility routes are deprecated; migrate to the canonical chat API."
    )
    if compatibility_route == "response_core":
        warnings.append("Legacy response-core route now delegates to ChatOrchestrator.")
    if chat_response.status == ProcessingStatus.DEGRADED:
        warnings.append("Response completed in degraded mode.")

    errors = list(chat_response.metadata.get("errors", []))
    if chat_response.error:
        errors.append(chat_response.error)

    return ChatResponse(
        response=chat_response.response,
        session_id=session_id,
        metadata={
            **chat_response.metadata,
            "authority": "chat_orchestrator",
            "compatibility_route": compatibility_route,
            "status": chat_response.status.value,
            "execution_path": chat_response.execution_path,
            "assistant_message_id": chat_response.assistant_message_id,
            "correlation_id": chat_response.correlation_id,
            "structured_content": chat_response.structured_content,
            "actions": chat_response.actions,
            "telemetry": chat_response.telemetry,
        },
        processing_time=chat_response.processing_time,
        errors=errors,
        warnings=warnings,
    )


async def _execute_canonical_chat(
    request: ChatRequest,
    current_user: Dict[str, Any],
    *,
    compatibility_route: str,
) -> ChatResponse:
    """Run a legacy compatibility request through the canonical chat orchestrator."""
    orchestrator = await get_chat_orchestrator()
    canonical_request = _build_compatibility_chat_request(
        request, current_user, streaming=False
    )
    chat_response = await orchestrator.handle_chat(canonical_request)
    return _translate_chat_response(
        chat_response,
        session_id=canonical_request.session_id or canonical_request.conversation_id,
        compatibility_route=compatibility_route,
    )


@compatibility_router.post("/chat", response_model=ChatResponse, deprecated=True)
async def chat(
    request: ChatRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Legacy compatibility ingress for standard chat.

    The authoritative standard chat lifecycle runs through ChatOrchestrator.
    """
    try:
        return await _execute_canonical_chat(
            request,
            current_user,
            compatibility_route="orchestration.chat",
        )
    except Exception as e:
        logger.error(f"Compatibility chat processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@compatibility_router.post("/chat/stream", deprecated=True)
async def chat_stream(
    request: ChatRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Legacy compatibility ingress for streaming standard chat.

    Streaming authority runs through ChatOrchestrator; this endpoint only adapts
    canonical chunks into the older SSE envelope.
    """
    try:
        orchestrator = await get_chat_orchestrator()
        canonical_request = _build_compatibility_chat_request(
            request, current_user, streaming=True
        )
        chunk_stream = await orchestrator.handle_chat_stream(canonical_request)

        async def generate_stream():
            """Generate SSE chunks from canonical streaming chat output."""
            try:
                async for chunk in chunk_stream:
                    payload = {
                        "type": chunk.type,
                        "content": chunk.content,
                        "correlation_id": chunk.correlation_id,
                        "metadata": {
                            **(chunk.metadata or {}),
                            "authority": "chat_orchestrator",
                            "compatibility_route": "orchestration.chat.stream",
                            "deprecated": True,
                            "deprecation_message": "Legacy /api/orchestration/chat* compatibility routes are deprecated; migrate to the canonical chat API.",
                        },
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {
                    "type": "error",
                    "content": f"Streaming error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )

    except Exception as e:
        logger.error(f"Stream setup error: {e}")
        raise HTTPException(status_code=500, detail=f"Stream setup error: {str(e)}")


async def _get_langgraph_status(
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator),
) -> OrchestrationStatus:
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


@admin_router.get("/status", response_model=OrchestrationStatus)
async def get_status(orchestrator: LangGraphOrchestrator = Depends(get_orchestrator)):
    """Get LangGraph orchestration status from the explicit admin namespace."""
    return await _get_langgraph_status(orchestrator)


async def _update_langgraph_config(
    request: ConfigUpdateRequest,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
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
            key: value for key, value in config_updates.items() if value is not None
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


@admin_router.post("/config")
async def update_config(
    request: ConfigUpdateRequest,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update LangGraph orchestration configuration from the admin namespace."""
    return await _update_langgraph_config(request, orchestrator, current_user)


async def _langgraph_health_check():
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
            "streaming": "available",
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@admin_router.get("/health")
async def health_check():
    """Get LangGraph orchestration health from the explicit admin namespace."""
    return await _langgraph_health_check()


@compatibility_router.post(
    "/chat/response-core", response_model=ChatResponse, deprecated=True
)
async def chat_with_response_core(
    request: ChatRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Legacy alias retained for older callers.

    This endpoint no longer owns a parallel response-core lifecycle; it delegates
    to the canonical chat runtime and reports its compatibility role in metadata.
    """
    try:
        return await _execute_canonical_chat(
            request,
            current_user,
            compatibility_route="response_core",
        )
    except Exception as e:
        logger.error(f"Response-core compatibility chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Response-core compatibility error: {str(e)}"
        )


async def _debug_langgraph_dry_run(
    request: ChatRequest,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dry-run error: {e}")
        raise HTTPException(status_code=500, detail=f"Dry-run error: {str(e)}")


@admin_router.post("/debug/dry-run")
async def debug_dry_run(
    request: ChatRequest,
    orchestrator: LangGraphOrchestrator = Depends(get_orchestrator),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Run LangGraph dry-run analysis from the explicit admin namespace."""
    return await _debug_langgraph_dry_run(request, orchestrator, current_user)


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


router = APIRouter(lifespan=orchestration_router_lifespan)
router.include_router(compatibility_router)
router.include_router(admin_router)
