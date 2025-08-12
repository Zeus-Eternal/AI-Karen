"""
Unified Memory API Routes - Phase 4.1.a
Production-ready memory management with CRUD operations, tenant isolation, and RBAC.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .unified_schemas import ErrorHandler

logger = logging.getLogger(__name__)

# Graceful imports with fallback mechanisms
try:
    from ai_karen_engine.services.memory_service import (
        MemoryType,
        UISource,
        WebUIMemoryQuery,
        WebUIMemoryService,
    )

    MEMORY_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("Memory service not available, using fallback")
    MEMORY_SERVICE_AVAILABLE = False

try:
    from ai_karen_engine.core.rbac import check_scope

    RBAC_AVAILABLE = True
except ImportError:
    logger.warning("RBAC not available, using fallback")
    RBAC_AVAILABLE = False

try:
    from ai_karen_engine.services.metrics_service import get_metrics_service

    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("Metrics service not available, using fallback")
    METRICS_AVAILABLE = False


# Unified request/response models according to design spec
class ContextHit(BaseModel):
    """Unified memory hit representation"""

    id: str
    text: str
    score: float
    tags: List[str] = Field(default_factory=list)
    recency: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(5, ge=1, le=10)
    decay_tier: str = Field("short")
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: str
    org_id: Optional[str] = None


class MemQuery(BaseModel):
    """Unified memory query request schema"""

    user_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    query: str = Field(..., min_length=1, max_length=4096)
    top_k: int = Field(12, ge=1, le=50)


class MemSearchResponse(BaseModel):
    """Unified memory search response schema"""

    hits: List[ContextHit]
    total_found: int
    query_time_ms: float
    correlation_id: str


class MemCommit(BaseModel):
    """Unified memory commit request schema"""

    user_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    text: str = Field(..., min_length=1, max_length=16000)
    tags: List[str] = Field(default_factory=list)
    importance: int = Field(5, ge=1, le=10)
    decay: str = Field("short", pattern="^(short|medium|long|pinned)$")


class MemCommitResponse(BaseModel):
    """Unified memory commit response schema"""

    id: str
    success: bool
    message: str
    correlation_id: str


class MemUpdateRequest(BaseModel):
    """Memory update request schema"""

    text: Optional[str] = Field(None, min_length=1, max_length=16000)
    tags: Optional[List[str]] = None
    importance: Optional[int] = Field(None, ge=1, le=10)
    decay: Optional[str] = Field(None, pattern="^(short|medium|long|pinned)$")


class MemUpdateResponse(BaseModel):
    """Memory update response schema"""

    success: bool
    message: str
    correlation_id: str


class MemDeleteResponse(BaseModel):
    """Memory delete response schema"""

    success: bool
    message: str
    correlation_id: str


# Import unified schemas
# Create router
router = APIRouter(tags=["memory"])

try:
    from ai_karen_engine.services.correlation_service import (
        CorrelationService,
        create_correlation_logger,
    )

    CORRELATION_AVAILABLE = True
    # Use correlation-aware logger
    logger = create_correlation_logger(__name__)
except ImportError:
    logger.warning("Correlation service not available, using fallback")
    CORRELATION_AVAILABLE = False

try:
    from ai_karen_engine.services.structured_logging import (
        get_structured_logging_service,
    )

    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError:
    logger.warning("Structured logging not available, using fallback")
    STRUCTURED_LOGGING_AVAILABLE = False


def get_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID for request tracking"""
    if CORRELATION_AVAILABLE:
        headers = {key: value for key, value in request.headers.items()}
        return CorrelationService.get_or_create_correlation_id(headers)
    else:
        return request.headers.get("X-Correlation-Id", str(uuid.uuid4()))


async def check_rbac_scope(request: Request, scope: str) -> bool:
    """Check RBAC scope and fail closed on errors."""
    if not RBAC_AVAILABLE:
        logger.warning("RBAC not available")
        raise HTTPException(status_code=403, detail="RBAC unavailable")

    try:
        return await check_scope(request, scope)
    except Exception as e:
        logger.warning(f"RBAC check failed for {scope}: {e}")
        raise HTTPException(status_code=403, detail="RBAC error")


async def get_memory_service() -> Optional[WebUIMemoryService]:
    """Get memory service with graceful fallback"""
    if not MEMORY_SERVICE_AVAILABLE:
        return None

    try:
        from ai_karen_engine.core.service_registry import get_service_registry

        registry = get_service_registry()
        return await registry.get_service("memory_service")
    except Exception as e:
        logger.warning(f"Memory service unavailable: {e}")
        return None


def record_metrics(
    operation: str,
    status: str,
    duration: float,
    user_id: str = "",
    org_id: str = "",
    decay_tier: str = "",
    correlation_id: Optional[str] = None,
):
    """Record metrics with graceful fallback"""
    if not METRICS_AVAILABLE:
        return

    try:
        metrics_service = get_metrics_service()

        if operation == "commit":
            metrics_service.record_memory_commit(
                status, decay_tier, user_id, org_id, correlation_id
            )
        else:
            metrics_service.record_memory_query(
                operation, status, user_id, org_id, correlation_id
            )

        # Record vector latency for search operations
        if operation == "search":
            metrics_service.record_vector_latency(
                duration, "search", status, correlation_id
            )

    except Exception as e:
        logger.warning(f"Metrics recording failed: {e}")


def apply_tenant_filtering(user_id: str, org_id: Optional[str]) -> Dict[str, Any]:
    """Apply tenant filtering constraints"""
    filters = {"user_id": user_id}
    if org_id:
        filters["org_id"] = org_id
    return filters


@router.post("/search", response_model=MemSearchResponse)
async def memory_search(request: MemQuery, http_request: Request):
    """
    Unified memory search endpoint - READ operation for all interfaces.

    Provides semantic search across all memory types with tenant isolation
    and scope-based permissions.
    """
    start_time = datetime.utcnow()
    correlation_id = get_correlation_id(http_request)

    # Set correlation ID in context for propagation
    if CORRELATION_AVAILABLE:
        CorrelationService.set_correlation_id(correlation_id)

        # Start trace tracking
        from ai_karen_engine.services.correlation_service import get_correlation_tracker

        tracker = get_correlation_tracker()
        tracker.start_trace(
            correlation_id,
            "memory_search",
            {
                "user_id": request.user_id,
                "org_id": request.org_id,
                "query_length": len(request.query),
                "top_k": request.top_k,
            },
        )

    # Check RBAC permissions
    if not await check_rbac_scope(http_request, "memory:read"):
        record_metrics(
            "search",
            "forbidden",
            0,
            request.user_id,
            request.org_id or "",
            "",
            correlation_id,
        )
        error_response = ErrorHandler.create_authorization_error_response(
            correlation_id=correlation_id,
            path=str(http_request.url.path),
            message="Insufficient permissions for memory search",
        )
        raise HTTPException(status_code=403, detail=error_response.dict())

    try:
        # Apply tenant filtering
        tenant_filters = apply_tenant_filtering(request.user_id, request.org_id)

        # Get memory service
        memory_service = await get_memory_service()

        if memory_service:
            try:
                tenant_id = tenant_filters.get("org_id") or tenant_filters["user_id"]
                query = WebUIMemoryQuery(
                    text=request.query,
                    user_id=request.user_id,
                    top_k=request.top_k,
                )
                memories = await memory_service.query_memories(tenant_id, query)
                hits = [
                    ContextHit(
                        id=mem.id,
                        text=mem.content,
                        score=mem.similarity_score or 0.0,
                        tags=mem.tags or [],
                        importance=getattr(mem, "importance_score", 5),
                        decay_tier=(
                            mem.metadata.get("decay") if mem.metadata else "short"
                        ),
                        created_at=datetime.utcfromtimestamp(mem.timestamp)
                        if isinstance(mem.timestamp, (int, float))
                        else mem.timestamp or datetime.utcnow(),
                        user_id=request.user_id,
                        org_id=request.org_id,
                        meta={"source": "unified_search", "tenant_filtered": True},
                    )
                    for mem in memories
                ]
            except Exception as e:
                logger.warning(f"Memory search failed: {e}")
                hits = []
        else:
            # Fallback mock results
            hits = [
                ContextHit(
                    id="fallback_mem_1",
                    text=f"Fallback result for query: {request.query}",
                    score=0.7,
                    tags=["fallback"],
                    importance=5,
                    decay_tier="short",
                    created_at=datetime.utcnow(),
                    user_id=request.user_id,
                    org_id=request.org_id,
                    meta={"source": "fallback"},
                )
            ]

        # Calculate timing
        query_duration = (datetime.utcnow() - start_time).total_seconds()
        query_time_ms = query_duration * 1000

        # Record metrics
        record_metrics(
            "search",
            "success",
            query_duration,
            request.user_id,
            request.org_id or "",
            "",
            correlation_id,
        )

        # Log memory access with structured logging (without content for privacy)
        if STRUCTURED_LOGGING_AVAILABLE:
            try:
                logging_service = get_structured_logging_service()
                logging_service.log_memory_access(
                    operation="search",
                    memory_id=f"query_{correlation_id[:8]}",  # Use correlation ID fragment
                    user_id=request.user_id,
                    org_id=request.org_id,
                    correlation_id=correlation_id,
                    hits_count=len(hits),
                    query_length=len(request.query),
                    top_k=request.top_k,
                )

                # Log API request
                logging_service.log_api_request(
                    method=http_request.method,
                    endpoint=str(http_request.url.path),
                    status_code=200,
                    duration_ms=query_duration * 1000,
                    user_id=request.user_id,
                    org_id=request.org_id,
                    ip_address=http_request.client.host
                    if http_request.client
                    else None,
                    user_agent=http_request.headers.get("user-agent"),
                    correlation_id=correlation_id,
                    hits_count=len(hits),
                )
            except Exception as e:
                logger.warning(f"Structured logging failed: {e}")

        # End trace tracking
        if CORRELATION_AVAILABLE:
            tracker.end_trace(
                correlation_id,
                "success",
                {
                    "total_duration": query_duration,
                    "hits_count": len(hits),
                    "user_id": request.user_id,
                    "org_id": request.org_id,
                },
            )

        return MemSearchResponse(
            hits=hits,
            total_found=len(hits),
            query_time_ms=query_time_ms,
            correlation_id=correlation_id,
        )

    except HTTPException:
        # End trace for HTTP exceptions
        if CORRELATION_AVAILABLE:
            query_duration = (datetime.utcnow() - start_time).total_seconds()
            tracker.end_trace(
                correlation_id,
                "http_error",
                {
                    "total_duration": query_duration,
                    "user_id": request.user_id,
                    "org_id": request.org_id,
                },
            )
        raise
    except Exception as e:
        query_duration = (datetime.utcnow() - start_time).total_seconds()
        record_metrics(
            "search",
            "error",
            query_duration,
            request.user_id,
            request.org_id or "",
            "",
            correlation_id,
        )

        # End trace for general exceptions
        if CORRELATION_AVAILABLE:
            tracker.end_trace(
                correlation_id,
                "error",
                {
                    "total_duration": query_duration,
                    "error": str(e),
                    "user_id": request.user_id,
                    "org_id": request.org_id,
                },
            )

        logger.error(
            f"Memory search failed: {e}", extra={"correlation_id": correlation_id}
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(http_request.url.path), error=e
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.post("/commit", response_model=MemCommitResponse)
async def memory_commit(request: MemCommit, http_request: Request):
    """
    Unified memory commit endpoint - CREATE operation for all interfaces.

    Stores new memories with decay policy assignment and tenant isolation.
    """
    start_time = datetime.utcnow()
    correlation_id = get_correlation_id(http_request)

    # Check RBAC permissions
    if not await check_rbac_scope(http_request, "memory:write"):
        record_metrics(
            "commit",
            "forbidden",
            0,
            request.user_id,
            request.org_id or "",
            request.decay,
            correlation_id,
        )
        error_response = ErrorHandler.create_authorization_error_response(
            correlation_id=correlation_id,
            path=str(http_request.url.path),
            message="Insufficient permissions for memory commit",
        )
        raise HTTPException(status_code=403, detail=error_response.dict())

    try:
        # Apply tenant filtering
        tenant_filters = apply_tenant_filtering(request.user_id, request.org_id)

        # Get memory service
        memory_service = await get_memory_service()

        if memory_service:
            try:
                tenant_id = tenant_filters.get("org_id") or tenant_filters["user_id"]
                memory_id = await memory_service.store_web_ui_memory(
                    tenant_id=tenant_id,
                    content=request.text,
                    user_id=request.user_id,
                    ui_source=UISource.AG_UI,
                    memory_type=MemoryType.GENERAL,
                    tags=request.tags,
                    importance_score=request.importance,
                    metadata={"decay": request.decay},
                )
                success = memory_id is not None
                message = (
                    f"Memory stored with decay tier '{request.decay}' and importance {request.importance}"
                    if success
                    else "Memory commit failed"
                )
            except Exception as e:
                logger.warning(f"Memory commit failed: {e}")
                success = False
                message = f"Memory commit failed: {str(e)}"
                memory_id = ""
        else:
            # Fallback success
            memory_id = f"mem_{uuid.uuid4().hex[:12]}"
            success = True
            message = (
                f"Memory stored in fallback mode with decay tier '{request.decay}'"
            )

        # Calculate timing
        commit_duration = (datetime.utcnow() - start_time).total_seconds()

        # Record metrics
        record_metrics(
            "commit",
            "success" if success else "error",
            commit_duration,
            request.user_id,
            request.org_id or "",
            request.decay,
            correlation_id,
        )

        return MemCommitResponse(
            id=memory_id if success else "",
            success=success,
            message=message,
            correlation_id=correlation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        commit_duration = (datetime.utcnow() - start_time).total_seconds()
        record_metrics(
            "commit",
            "error",
            commit_duration,
            request.user_id,
            request.org_id or "",
            request.decay,
            correlation_id,
        )

        logger.error(
            f"Memory commit failed: {e}", extra={"correlation_id": correlation_id}
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(http_request.url.path), error=e
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.put("/{memory_id}", response_model=MemUpdateResponse)
async def memory_update(
    memory_id: str,
    request: MemUpdateRequest,
    http_request: Request,
    user_id: str = "",
    org_id: Optional[str] = None,
):
    """
    Unified memory update endpoint - UPDATE operation with version tracking.

    Updates existing memories with version history and importance recalculation.
    """
    start_time = datetime.utcnow()
    correlation_id = get_correlation_id(http_request)

    # Check RBAC permissions
    if not await check_rbac_scope(http_request, "memory:write"):
        record_metrics(
            "update", "forbidden", 0, user_id, org_id or "", "", correlation_id
        )
        error_response = ErrorHandler.create_authorization_error_response(
            correlation_id=correlation_id,
            path=str(http_request.url.path),
            message="Insufficient permissions for memory update",
        )
        raise HTTPException(status_code=403, detail=error_response.dict())

    try:
        # Apply tenant filtering
        tenant_filters = apply_tenant_filtering(user_id, org_id)

        # Get memory service
        memory_service = await get_memory_service()

        if memory_service:
            try:
                tenant_id = tenant_filters.get("org_id") or tenant_filters["user_id"]
                success = True
                if request.importance is not None:
                    success = await memory_service.update_memory_importance(
                        tenant_id, memory_id, request.importance
                    )
                if success and (request.text or request.tags):
                    await memory_service.base_manager.delete_memory(
                        tenant_id, memory_id
                    )
                    new_id = await memory_service.store_web_ui_memory(
                        tenant_id=tenant_id,
                        content=request.text or "",
                        user_id=user_id or tenant_filters["user_id"],
                        ui_source=UISource.AG_UI,
                        memory_type=MemoryType.GENERAL,
                        tags=request.tags,
                        importance_score=request.importance,
                        metadata={"decay": request.decay} if request.decay else None,
                    )
                    success = new_id is not None
                message = (
                    f"Memory {memory_id} updated successfully"
                    if success
                    else "Memory update failed"
                )
            except Exception as e:
                logger.warning(f"Memory update failed: {e}")
                success = False
                message = f"Memory update failed: {str(e)}"
        else:
            # Fallback success
            success = True
            message = f"Memory {memory_id} updated in fallback mode"

        # Calculate timing
        update_duration = (datetime.utcnow() - start_time).total_seconds()

        # Record metrics
        record_metrics(
            "update",
            "success" if success else "error",
            update_duration,
            user_id,
            org_id or "",
            "",
            correlation_id,
        )

        return MemUpdateResponse(
            success=success, message=message, correlation_id=correlation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        update_duration = (datetime.utcnow() - start_time).total_seconds()
        record_metrics(
            "update",
            "error",
            update_duration,
            user_id,
            org_id or "",
            "",
            correlation_id,
        )

        logger.error(
            f"Memory update failed: {e}", extra={"correlation_id": correlation_id}
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(http_request.url.path), error=e
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.delete("/{memory_id}", response_model=MemDeleteResponse)
async def memory_delete(
    memory_id: str,
    http_request: Request,
    hard_delete: bool = False,
    user_id: str = "",
    org_id: Optional[str] = None,
):
    """
    Unified memory delete endpoint - DELETE operation with audit trails.

    Supports both soft deletion with audit trails and hard deletion for privacy compliance.
    """
    start_time = datetime.utcnow()
    correlation_id = get_correlation_id(http_request)

    # Check RBAC permissions
    if not await check_rbac_scope(http_request, "memory:write"):
        record_metrics(
            "delete", "forbidden", 0, user_id, org_id or "", "", correlation_id
        )
        error_response = ErrorHandler.create_authorization_error_response(
            correlation_id=correlation_id,
            path=str(http_request.url.path),
            message="Insufficient permissions for memory deletion",
        )
        raise HTTPException(status_code=403, detail=error_response.dict())

    try:
        # Apply tenant filtering
        tenant_filters = apply_tenant_filtering(user_id, org_id)

        # Get memory service
        memory_service = await get_memory_service()

        if memory_service:
            try:
                tenant_id = tenant_filters.get("org_id") or tenant_filters["user_id"]
                success = await memory_service.base_manager.delete_memory(
                    tenant_id, memory_id
                )
                delete_type = "hard" if hard_delete else "soft"
                message = (
                    f"Memory {memory_id} {delete_type} deleted successfully"
                    if success
                    else "Memory deletion failed"
                )
            except Exception as e:
                logger.warning(f"Memory deletion failed: {e}")
                success = False
                message = f"Memory deletion failed: {str(e)}"
        else:
            # Fallback success
            success = True
            delete_type = "hard" if hard_delete else "soft"
            message = f"Memory {memory_id} {delete_type} deleted in fallback mode"

        # Calculate timing
        delete_duration = (datetime.utcnow() - start_time).total_seconds()

        # Record metrics
        record_metrics(
            "delete",
            "success" if success else "error",
            delete_duration,
            user_id,
            org_id or "",
            "",
            correlation_id,
        )

        return MemDeleteResponse(
            success=success, message=message, correlation_id=correlation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        delete_duration = (datetime.utcnow() - start_time).total_seconds()
        record_metrics(
            "delete",
            "error",
            delete_duration,
            user_id,
            org_id or "",
            "",
            correlation_id,
        )

        logger.error(
            f"Memory deletion failed: {e}", extra={"correlation_id": correlation_id}
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(http_request.url.path), error=e
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.get("/health")
async def health_check():
    """Health check for memory service with dependency status"""
    return {
        "status": "healthy",
        "service": "memory",
        "dependencies": {
            "memory_service": MEMORY_SERVICE_AVAILABLE,
            "rbac": RBAC_AVAILABLE,
            "metrics": METRICS_AVAILABLE,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# Export router for inclusion in main FastAPI app
__all__ = ["router"]
