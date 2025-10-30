"""
Response Core API Routes

This module provides API endpoints for the Response Core Orchestrator system,
maintaining backward compatibility with existing chat orchestrator while
adding new capabilities for model management and training operations.
"""

import asyncio
import json
import logging
import shutil
import time
import uuid
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from ..core.response.factory import (
    create_response_orchestrator,
    create_local_only_orchestrator,
    create_enhanced_orchestrator,
    get_global_orchestrator,
    create_autonomous_learner,
    create_scheduler_manager,
    rebuild_global_orchestrator,
)
from ..core.response.scheduler_manager import AutonomousConfig
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


def _compose_ui_caps(request: ResponseCoreRequest, current_user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge UI capability overrides with request context for the orchestrator."""

    ui_caps = dict(request.ui_caps or {})

    contextual_fields = {
        "conversation_id": request.conversation_id,
        "session_id": request.session_id,
        "tenant_id": request.tenant_id or current_user.get("tenant_id"),
        "user_id": request.user_id or current_user.get("id"),
        "include_context": request.include_context,
        "attachments": request.attachments or None,
        "request_metadata": request.metadata or None,
    }

    for key, value in contextual_fields.items():
        if value in (None, {}, []):
            continue
        ui_caps[key] = value

    ui_caps.setdefault("stream", request.stream)
    return ui_caps


def _normalize_response_payload(
    payload: Any,
    default_persona: str,
    measured_duration: Optional[float] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Normalize orchestrator output into the schema expected by the API."""

    if not isinstance(payload, dict):
        payload = {"content": "" if payload is None else str(payload), "metadata": {}}

    metadata = dict(payload.get("metadata") or {})
    if extra_metadata:
        for key, value in extra_metadata.items():
            if value not in (None, {}, []):
                metadata[key] = value

    correlation_id = metadata.get("correlation_id") or str(uuid.uuid4())
    metadata["correlation_id"] = correlation_id

    used_fallback = bool(metadata.get("fallback_used")) or metadata.get("routing_decision") == "fallback"
    metadata["fallback_used"] = used_fallback
    metadata.setdefault("orchestrator", "response_core")

    context_tokens = metadata.get("context_tokens")
    context_used = bool(context_tokens) and context_tokens > 0

    generation_ms = metadata.get("generation_time_ms")
    if isinstance(generation_ms, (int, float)) and generation_ms >= 0:
        processing_time = float(generation_ms) / 1000.0
    else:
        processing_time = measured_duration or 0.0
        metadata["generation_time_ms"] = int(processing_time * 1000)

    intent = payload.get("intent") or "general_assist"
    persona = payload.get("persona") or default_persona
    mood = payload.get("mood") or "neutral"
    content = payload.get("content")
    if content is None:
        content = ""

    return {
        "intent": intent,
        "persona": persona,
        "mood": mood,
        "content": content,
        "metadata": metadata,
        "correlation_id": correlation_id,
        "processing_time": processing_time,
        "used_fallback": used_fallback,
        "context_used": context_used,
    }


REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_REGISTRY_FILE = REPO_ROOT / "model_registry.json"
MODEL_OVERRIDES_FILE = REPO_ROOT / "config" / "model_overrides.json"


def _resolve_model_path(raw_path: str) -> Path:
    """Resolve a model path from the registry to an absolute path."""

    path = Path(raw_path)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    return path


def _compute_model_stats(model_path: Path) -> Dict[str, Any]:
    """Gather file system statistics for a model path."""

    if not model_path.exists():
        return {"size_bytes": 0, "last_modified": None}

    if model_path.is_file():
        stat = model_path.stat()
        return {
            "size_bytes": stat.st_size,
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    total_size = 0
    latest_mtime = 0.0
    for file in model_path.rglob("*"):
        if not file.is_file():
            continue
        stat = file.stat()
        total_size += stat.st_size
        latest_mtime = max(latest_mtime, stat.st_mtime)

    if latest_mtime == 0.0:
        latest_mtime = model_path.stat().st_mtime

    return {
        "size_bytes": total_size,
        "last_modified": datetime.fromtimestamp(latest_mtime).isoformat(),
    }


def _load_model_registry() -> List[Dict[str, Any]]:
    """Load the production model registry from disk."""

    try:
        raw_registry = json.loads(MODEL_REGISTRY_FILE.read_text())
    except FileNotFoundError as exc:
        logger.error("Model registry file is missing: %s", MODEL_REGISTRY_FILE)
        raise HTTPException(status_code=500, detail="Model registry is unavailable") from exc
    except json.JSONDecodeError as exc:
        logger.error("Model registry file is corrupted: %s", exc)
        raise HTTPException(status_code=500, detail="Model registry is invalid") from exc

    registry: List[Dict[str, Any]] = []
    for entry in raw_registry:
        if isinstance(entry, dict) and entry.get("name"):
            registry.append(entry)
    return registry


def _load_model_overrides() -> Dict[str, Any]:
    """Load persisted model configuration overrides."""

    if not MODEL_OVERRIDES_FILE.exists():
        return {}

    try:
        return json.loads(MODEL_OVERRIDES_FILE.read_text())
    except json.JSONDecodeError as exc:
        logger.warning("Model overrides file is invalid, ignoring: %s", exc)
        return {}


def _store_model_overrides(overrides: Dict[str, Any]) -> None:
    """Persist model overrides atomically."""

    MODEL_OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
    MODEL_OVERRIDES_FILE.write_text(json.dumps(overrides, indent=2, sort_keys=True))


def _summarize_model_entry(entry: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Build a structured summary for a registry entry."""

    model_id = entry["name"]
    resolved_path = _resolve_model_path(entry.get("path", model_id))
    exists = resolved_path.exists()
    stats = _compute_model_stats(resolved_path)

    summary = {
        "id": model_id,
        "name": entry.get("display_name") or model_id,
        "path": str(resolved_path),
        "source": entry.get("source", "local"),
        "type": entry.get("type", "unknown"),
        "status": "available" if exists else "missing",
        "size_bytes": stats["size_bytes"],
        "last_modified": stats["last_modified"],
        "managed": bool(entry.get("managed", True)),
    }

    if model_id in overrides:
        summary["config_override"] = overrides[model_id]

    return summary


def _categorize_models(models: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Categorize models into system, custom, and huggingface buckets."""

    categories = {
        "system_models": [],
        "custom_models": [],
        "huggingface_models": [],
    }

    for model in models:
        source = (model.get("source") or "").lower()
        model_type = (model.get("type") or "").lower()

        if source == "huggingface":
            categories["huggingface_models"].append(model)
        elif source in {"custom", "user"} or model_type == "custom":
            categories["custom_models"].append(model)
        else:
            categories["system_models"].append(model)

    categories["total"] = len(models)
    return categories


def _apply_model_filters(model: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    """Check whether a model summary matches the provided filters."""

    if not filters:
        return True

    for key, expected in filters.items():
        value = model.get(key)
        if isinstance(expected, (list, tuple, set)):
            if value not in expected:
                return False
        else:
            if str(value).lower() != str(expected).lower():
                return False

    return True


def _find_registry_entry(model_id: str, registry: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Locate a model entry by identifier."""

    for entry in registry:
        if entry.get("name") == model_id:
            return entry
    return None


def _remove_model_path(model_path: Path) -> None:
    """Remove model files from disk."""

    if not model_path.exists():
        return

    if model_path.is_dir():
        shutil.rmtree(model_path)
    else:
        model_path.unlink()


TRAINING_JOBS: Dict[str, Dict[str, Any]] = {}


def _schedule_training_job(
    job_id: str,
    user_id: str,
    tenant_id: Optional[str],
    model_id: str,
    config: Optional[Dict[str, Any]],
):
    """Launch an autonomous learning cycle in the background."""

    job_record: Dict[str, Any] = {
        "job_id": job_id,
        "model_id": model_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id or "default",
        "user_id": user_id,
        "config": config or {},
    }

    async def runner() -> None:
        try:
            learner = create_autonomous_learner(user_id=user_id, tenant_id=tenant_id)
            force_training = bool(job_record["config"].get("force_training"))
            result = await learner.trigger_learning_cycle(
                job_record["tenant_id"],
                force_training=force_training
            )

            job_record["result"] = result.to_dict()
            job_record["status"] = "completed" if not result.error_message else "failed"

        except asyncio.CancelledError:
            job_record["status"] = "cancelled"
            job_record["error"] = "Training job cancelled"
            job_record["completed_at"] = datetime.utcnow().isoformat()
            job_record["task"] = None
            raise
        except Exception as exc:
            job_record["status"] = "failed"
            job_record["error"] = str(exc)
            job_record["completed_at"] = datetime.utcnow().isoformat()
            job_record["task"] = None
            logger.error("Training job %s failed: %s", job_id, exc, exc_info=True)
        else:
            job_record["completed_at"] = datetime.utcnow().isoformat()
        finally:
            job_record["task"] = None

    task = asyncio.create_task(runner())
    job_record["task"] = task
    TRAINING_JOBS[job_id] = job_record

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

    try:
        user_id = request.user_id or current_user.get("id", "anonymous")
        tenant_id = request.tenant_id or current_user.get("tenant_id")

        orchestrator = get_response_orchestrator(
            user_id=user_id,
            tenant_id=tenant_id,
            config_overrides=request.config_overrides
        )

        ui_caps = _compose_ui_caps(request, current_user)
        raw_response = orchestrator.respond(
            user_text=request.message,
            ui_caps=ui_caps
        )

        measured_duration = time.time() - start_time
        normalized = _normalize_response_payload(
            raw_response,
            orchestrator.config.persona_default,
            measured_duration=measured_duration,
            extra_metadata={
                "conversation_id": request.conversation_id or ui_caps.get("conversation_id"),
                "session_id": request.session_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "request_metadata": request.metadata or None,
                "attachments": request.attachments or None,
            }
        )

        return ResponseCoreResponse(
            intent=normalized["intent"],
            persona=normalized["persona"],
            mood=normalized["mood"],
            content=normalized["content"],
            metadata=normalized["metadata"],
            correlation_id=normalized["correlation_id"],
            processing_time=normalized["processing_time"],
            used_fallback=normalized["used_fallback"],
            context_used=normalized["context_used"]
        )

    except Exception as e:
        logger.error(f"Response Core chat error: {e}")
        processing_time = time.time() - start_time
        error_correlation_id = str(uuid.uuid4())

        return ResponseCoreResponse(
            intent="error",
            persona="assistant",
            mood="apologetic",
            content=f"I apologize, but I encountered an error: {str(e)}",
            metadata={"error": str(e)},
            correlation_id=error_correlation_id,
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

            start_time = time.time()
            ui_caps = _compose_ui_caps(request, current_user)
            raw_response = orchestrator.respond(
                user_text=request.message,
                ui_caps=ui_caps
            )

            normalized = _normalize_response_payload(
                raw_response,
                orchestrator.config.persona_default,
                measured_duration=time.time() - start_time,
                extra_metadata={
                    "conversation_id": request.conversation_id or ui_caps.get("conversation_id"),
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                }
            )

            response_metadata = {
                **normalized["metadata"],
                "intent": normalized["intent"],
                "persona": normalized["persona"],
                "mood": normalized["mood"],
                "version": "1.0",
            }

            return {
                "response": normalized["content"],
                "correlation_id": normalized["correlation_id"],
                "processing_time": normalized["processing_time"],
                "used_fallback": normalized["used_fallback"],
                "context_used": normalized["context_used"],
                "metadata": response_metadata,
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

            orchestrator = get_response_orchestrator(
                user_id=user_id,
                tenant_id=tenant_id,
                config_overrides=request.config_overrides
            )

            start_time = time.time()
            ui_caps = _compose_ui_caps(request, current_user)
            raw_response = orchestrator.respond(
                user_text=request.message,
                ui_caps=ui_caps
            )

            normalized = _normalize_response_payload(
                raw_response,
                orchestrator.config.persona_default,
                measured_duration=time.time() - start_time,
                extra_metadata={
                    "conversation_id": request.conversation_id or ui_caps.get("conversation_id"),
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                }
            )

            metadata_chunk = {
                "type": "metadata",
                "content": "",
                "correlation_id": normalized["correlation_id"],
                "metadata": {
                    **normalized["metadata"],
                    "intent": normalized["intent"],
                    "persona": normalized["persona"],
                    "mood": normalized["mood"],
                    "status": "processing",
                },
            }
            yield f"data: {json.dumps(metadata_chunk)}\n\n"

            words = normalized["content"].split()
            for index, word in enumerate(words):
                content = word + (" " if index < len(words) - 1 else "")
                chunk = {
                    "type": "content",
                    "content": content,
                    "correlation_id": normalized["correlation_id"],
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)

            completion = {
                "type": "complete",
                "correlation_id": normalized["correlation_id"],
                "metadata": {
                    **normalized["metadata"],
                    "processing_time": normalized["processing_time"],
                    "used_fallback": normalized["used_fallback"],
                    "context_used": normalized["context_used"],
                },
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
            registry = _load_model_registry()
            overrides = _load_model_overrides()

            summaries = [
                _summarize_model_entry(entry, overrides)
                for entry in registry
            ]

            filtered = [
                summary for summary in summaries
                if _apply_model_filters(summary, request.filters)
            ]

            categorized = _categorize_models(filtered)
            categorized["filters"] = request.filters or {}

            return ModelManagementResponse(
                success=True,
                data=categorized,
                message="Models listed successfully"
            )

        elif request.operation == "configure":
            if not request.model_id or not request.config:
                raise HTTPException(status_code=400, detail="Model ID and config required for configuration")

            registry = _load_model_registry()
            overrides = _load_model_overrides()
            entry = _find_registry_entry(request.model_id, registry)

            if not entry:
                raise HTTPException(status_code=404, detail=f"Model {request.model_id} is not registered")

            overrides[request.model_id] = {
                "config": request.config,
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": current_user.get("id", "system"),
            }
            _store_model_overrides(overrides)

            summary = _summarize_model_entry(entry, overrides)

            return ModelManagementResponse(
                success=True,
                data=summary,
                message=f"Model {request.model_id} configured successfully"
            )

        elif request.operation == "download":
            if not request.model_id:
                raise HTTPException(status_code=400, detail="Model ID required for download")

            registry = _load_model_registry()
            entry = _find_registry_entry(request.model_id, registry)

            if not entry:
                raise HTTPException(status_code=404, detail=f"Model {request.model_id} is not registered")

            source = (entry.get("source") or "").lower()
            if source not in {"huggingface", "remote"}:
                raise HTTPException(status_code=400, detail="Only remote models support managed downloads")

            try:
                from ai_karen_engine.inference.huggingface_service import download_model as hf_download_model

                job = hf_download_model(request.model_id)
            except Exception as download_error:
                logger.error("Failed to start download for %s: %s", request.model_id, download_error)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to start download for model {request.model_id}"
                ) from download_error

            return ModelManagementResponse(
                success=True,
                data={
                    "model_id": request.model_id,
                    "job_id": job.id,
                    "status": job.status,
                    "queued_at": job.created_at,
                },
                message=f"Download started for model {request.model_id}"
            )

        elif request.operation == "delete":
            if not request.model_id:
                raise HTTPException(status_code=400, detail="Model ID required for deletion")

            registry = _load_model_registry()
            entry = _find_registry_entry(request.model_id, registry)

            if not entry:
                raise HTTPException(status_code=404, detail=f"Model {request.model_id} is not registered")

            model_path = _resolve_model_path(entry.get("path", request.model_id))
            if not model_path.exists():
                raise HTTPException(status_code=404, detail=f"Model {request.model_id} is not present on disk")

            _remove_model_path(model_path)

            overrides = _load_model_overrides()
            if overrides.pop(request.model_id, None) is not None:
                _store_model_overrides(overrides)

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

        operation = request.operation.lower()
        tenant_id = current_user.get("tenant_id")
        user_id = current_user.get("id", "system")

        if operation == "start":
            if not request.model_id:
                raise HTTPException(status_code=400, detail="Model ID required for training")

            job_id = str(uuid.uuid4())
            _schedule_training_job(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                model_id=request.model_id,
                config=request.config,
            )

            return TrainingResponse(
                success=True,
                job_id=job_id,
                status="running",
                data={"model_id": request.model_id},
                message=f"Training started for model {request.model_id}"
            )

        elif operation == "stop":
            job_id = (request.config or {}).get("job_id")
            if not job_id:
                raise HTTPException(status_code=400, detail="job_id required to stop training")

            job = TRAINING_JOBS.get(job_id)
            if not job:
                raise HTTPException(status_code=404, detail=f"Training job {job_id} not found")

            task: Optional[asyncio.Task] = job.get("task")
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            job["status"] = "cancelled"
            job["completed_at"] = datetime.utcnow().isoformat()

            return TrainingResponse(
                success=True,
                job_id=job_id,
                status="cancelled",
                data={"model_id": job.get("model_id")},
                message=f"Training job {job_id} cancelled"
            )

        elif operation == "status":
            job_id = (request.config or {}).get("job_id")
            if job_id:
                job = TRAINING_JOBS.get(job_id)
                if not job:
                    raise HTTPException(status_code=404, detail=f"Training job {job_id} not found")

                job_info = {k: v for k, v in job.items() if k != "task"}
                return TrainingResponse(
                    success=True,
                    job_id=job_id,
                    status=job_info.get("status", "unknown"),
                    data=job_info,
                    message="Training status retrieved"
                )

            summary = [
                {k: v for k, v in job.items() if k != "task"}
                for job in TRAINING_JOBS.values()
            ]
            return TrainingResponse(
                success=True,
                job_id=None,
                status="summary",
                data={"jobs": summary},
                message="Training status retrieved"
            )

        elif operation == "schedule":
            if not request.schedule:
                raise HTTPException(status_code=400, detail="Schedule required for autonomous training")

            scheduler = create_scheduler_manager(user_id=user_id, tenant_id=tenant_id)

            config_data = request.config or {}
            if config_data:
                autonomous_config = AutonomousConfig.from_dict(config_data)
            else:
                autonomous_config = AutonomousConfig()

            schedule_name = config_data.get("name") if config_data else None
            schedule_description = config_data.get("description") if config_data else ""

            schedule_id = scheduler.create_training_schedule(
                tenant_id or "default",
                schedule_name or f"Autonomous training for {request.model_id or 'global'}",
                request.schedule,
                autonomous_config,
                description=schedule_description,
            )

            if not scheduler.running:
                asyncio.create_task(scheduler.start_scheduler())

            return TrainingResponse(
                success=True,
                job_id=schedule_id,
                status="scheduled",
                data={
                    "schedule_id": schedule_id,
                    "schedule": request.schedule,
                    "config": config_data,
                },
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
        orchestrator = get_global_orchestrator(
            user_id=current_user.get("id", "default"),
            tenant_id=current_user.get("tenant_id")
        )

        config = asdict(orchestrator.config)

        return {
            "success": True,
            "config": config,
            "message": "Configuration retrieved successfully",
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

        if not isinstance(config_updates, dict) or not config_updates:
            raise HTTPException(status_code=400, detail="Configuration updates must be provided")

        orchestrator = get_global_orchestrator(
            user_id=current_user.get("id", "default"),
            tenant_id=current_user.get("tenant_id")
        )

        allowed_fields = {field.name for field in fields(PipelineConfig)}
        invalid_keys = sorted(set(config_updates) - allowed_fields)
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration keys: {', '.join(invalid_keys)}"
            )

        updated_config_data = asdict(orchestrator.config)
        updated_config_data.update(config_updates)
        new_config = PipelineConfig(**updated_config_data)

        rebuild_global_orchestrator(
            new_config,
            user_id=current_user.get("id", "default"),
            tenant_id=current_user.get("tenant_id")
        )

        return {
            "success": True,
            "updates": config_updates,
            "config": asdict(new_config),
            "message": "Configuration updated successfully",
            "updated_at": datetime.utcnow().isoformat(),
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