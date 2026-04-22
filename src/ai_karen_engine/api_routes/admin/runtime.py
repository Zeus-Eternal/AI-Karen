"""
Maintenance Admin API Routes — Unified Operator Control Surface.

Provides operator/admin controls for:
- Enabling/disabling maintenance mode
- Editing maintenance message and ETA
- Inspecting current runtime mode and dependency health
- Viewing notification subscriptions
- Data cleanup operations (folded in from legacy maintenance.py)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ai_karen_engine.core.services.dependencies import bypass_user_context_func
from ai_karen_engine.core.runtime.chat_runtime_control_plane import (
    ChatRuntimeControlPlane,
    get_chat_runtime_control_plane,
    RuntimeMode,
    DependencyStatus,
)
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/runtime", tags=["Runtime Admin"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class EnableMaintenanceRequest(BaseModel):
    """Request to enable maintenance mode."""

    reason: str = Field(..., min_length=1, max_length=500)
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User-facing maintenance message",
    )
    estimated_completion_time: Optional[str] = Field(
        None, description="ISO 8601 datetime string for ETA"
    )
    auto_end_policy: str = Field(
        "manual",
        pattern=r"^(manual|after_healthy_check|at_time)$",
        description="When to auto-end maintenance",
    )


class UpdateMaintenanceRequest(BaseModel):
    """Request to update an active maintenance window."""

    message: Optional[str] = Field(None, max_length=2000)
    estimated_completion_time: Optional[str] = None
    auto_end_policy: Optional[str] = Field(None, pattern=r"^(manual|after_healthy_check|at_time)$")


class RuntimeModeResponse(BaseModel):
    """Current runtime mode and state."""

    mode: str
    maintenance_active: bool
    maintenance_message: Optional[str]
    estimated_completion_time: Optional[str]
    normal_ready: bool
    degraded_ready: bool
    last_transition_at: Optional[str]
    last_transition_reason: Optional[str]


class DependencyHealthResponse(BaseModel):
    """Health status of a single dependency."""

    name: str
    status: str
    reason: Optional[str]
    response_time_ms: float
    consecutive_successes: int
    consecutive_failures: int
    checked_at: Optional[str]


class NotificationSubscriptionResponse(BaseModel):
    """A maintenance notification subscription."""

    id: str
    user_id: Optional[str]
    session_id: Optional[str]
    channel: str
    status: str
    requested_at: str


class CleanupRequest(BaseModel):
    """Request model for data cleanup."""

    dry_run: bool = Field(True, description="If True, only report changes")
    categories: Optional[List[str]] = Field(
        None, description="Specific categories to clean (files, users, cache, backups)"
    )


# ---------------------------------------------------------------------------
# Runtime Status Endpoints
# ---------------------------------------------------------------------------


@router.get("/status")
async def get_runtime_status(
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Get current runtime mode, maintenance state, and dependency health."""
    control_plane = await get_chat_runtime_control_plane()
    snapshot = control_plane.get_snapshot()

    deps = {}
    for name, health in snapshot.dependencies.items():
        deps[name] = {
            "status": health.status.value,
            "reason": health.reason,
            "response_time_ms": health.response_time_ms,
            "consecutive_successes": health.consecutive_successes,
            "consecutive_failures": health.consecutive_failures,
            "checked_at": health.checked_at.isoformat() if health.checked_at else None,
        }

    return {
        "mode": snapshot.mode.value,
        "maintenance_active": snapshot.maintenance_active,
        "maintenance_message": snapshot.maintenance_message,
        "estimated_completion_time": snapshot.estimated_completion_time,
        "normal_ready": snapshot.normal_ready,
        "degraded_ready": snapshot.degraded_ready,
        "degraded_capabilities": (
            {
                "memory": snapshot.degraded_capabilities.memory_available,
                "tools": snapshot.degraded_capabilities.tools_available,
                "plugins": snapshot.degraded_capabilities.plugins_available,
                "external_providers": snapshot.degraded_capabilities.external_providers_available,
                "streaming": snapshot.degraded_capabilities.streaming_supported,
                "description": snapshot.degraded_capabilities.description,
            }
            if snapshot.degraded_capabilities
            else None
        ),
        "dependencies": deps,
        "last_transition_at": snapshot.last_transition_at,
        "last_transition_reason": snapshot.last_transition_reason,
    }


@router.get("/dependencies")
async def get_dependency_health(
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Get detailed dependency health for all probed services."""
    control_plane = await get_chat_runtime_control_plane()
    snapshot = control_plane.get_snapshot()

    deps = []
    for name, health in snapshot.dependencies.items():
        deps.append(
            DependencyHealthResponse(
                name=name,
                status=health.status.value,
                reason=health.reason,
                response_time_ms=health.response_time_ms,
                consecutive_successes=health.consecutive_successes,
                consecutive_failures=health.consecutive_failures,
                checked_at=health.checked_at.isoformat() if health.checked_at else None,
            ).model_dump()
        )

    return {"dependencies": deps, "count": len(deps)}


@router.post("/check-health")
async def trigger_health_check(
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Trigger an immediate health check of all dependencies."""
    control_plane = await get_chat_runtime_control_plane()
    await control_plane._run_health_checks()

    snapshot = control_plane.get_snapshot()
    return {
        "mode": snapshot.mode.value,
        "normal_ready": snapshot.normal_ready,
        "degraded_ready": snapshot.degraded_ready,
        "message": "Health check completed",
    }


# ---------------------------------------------------------------------------
# Maintenance Control Endpoints
# ---------------------------------------------------------------------------


@router.post("/maintenance/enable")
async def enable_maintenance(
    request: EnableMaintenanceRequest,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Enable maintenance mode."""
    control_plane = await get_chat_runtime_control_plane()

    eta = None
    if request.estimated_completion_time:
        try:
            eta = datetime.fromisoformat(request.estimated_completion_time)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid estimated_completion_time format. Use ISO 8601.",
            )

    success = await control_plane.enable_maintenance(
        reason=request.reason,
        message=request.message,
        estimated_completion_time=eta,
        auto_end_policy=request.auto_end_policy,
        created_by=user.get("user_id"),
    )

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to enable maintenance mode"
        )

    return {
        "success": True,
        "mode": "maintenance",
        "reason": request.reason,
        "message": request.message,
    }


@router.post("/maintenance/disable")
async def disable_maintenance(
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Disable maintenance mode and trigger auto-recovery."""
    control_plane = await get_chat_runtime_control_plane()

    success = await control_plane.disable_maintenance(
        updated_by=user.get("user_id"),
    )

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to disable maintenance mode"
        )

    snapshot = control_plane.get_snapshot()
    return {
        "success": True,
        "new_mode": snapshot.mode.value,
        "normal_ready": snapshot.normal_ready,
        "degraded_ready": snapshot.degraded_ready,
    }


@router.put("/maintenance/update")
async def update_maintenance(
    request: UpdateMaintenanceRequest,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Update the active maintenance window's message or ETA."""
    control_plane = await get_chat_runtime_control_plane()

    if not control_plane.has_active_maintenance():
        raise HTTPException(
            status_code=400, detail="No active maintenance window to update"
        )

    eta = None
    if request.estimated_completion_time is not None:
        try:
            eta = datetime.fromisoformat(
                request.estimated_completion_time
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ETA format")

    success = await control_plane.update_maintenance(
        message=request.message,
        estimated_completion_time=eta,
        auto_end_policy=request.auto_end_policy,
        updated_by=user.get("user_id"),
    )

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to update maintenance window"
        )

    return {"success": True, "message": "Maintenance window updated"}


# ---------------------------------------------------------------------------
# Notification Subscription Endpoints
# ---------------------------------------------------------------------------


@router.get("/maintenance/notifications")
async def get_notification_subscriptions(
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """View all maintenance notification subscriptions."""
    try:
        control_plane = await get_chat_runtime_control_plane()
        subscriptions = await control_plane.get_maintenance_notification_subscriptions()
        return {
            "subscriptions": subscriptions,
            "count": len(subscriptions),
        }
    except Exception as e:
        logger.error(f"Failed to fetch notification subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscriptions")


@router.post("/maintenance/notifications/subscribe")
async def subscribe_to_maintenance_notifications(
    user: Dict[str, Any] = Depends(bypass_user_context_func),
    channel: str = "in_app",
) -> Dict[str, Any]:
    """Subscribe to receive notification when maintenance ends."""
    control_plane = await get_chat_runtime_control_plane()

    if not control_plane.has_active_maintenance():
        raise HTTPException(
            status_code=400,
            detail="No active maintenance window to subscribe to",
        )

    try:
        success = await control_plane.create_maintenance_notification_request(
            notification_channel=channel,
            user_id=user.get("user_id"),
            session_id=user.get("session_id"),
        )
        if not success:
            raise HTTPException(status_code=400, detail="Unable to subscribe")

        return {"success": True, "channel": channel, "status": "subscribed"}

    except Exception as e:
        logger.error(f"Failed to create notification subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")


# ---------------------------------------------------------------------------
# Data Cleanup (folded from legacy maintenance.py)
# ---------------------------------------------------------------------------


@router.post("/cleanup")
async def run_data_cleanup(
    request: CleanupRequest,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Run data cleanup operations."""
    try:
        from ai_karen_engine.memory.data_cleanup_service import (
            get_data_cleanup_service,
        )

        service = get_data_cleanup_service()
        report = await service.run_cleanup(
            dry_run=request.dry_run,
            categories=request.categories,
        )

        return {
            "success": True,
            "dry_run": request.dry_run,
            "report": report.__dict__ if hasattr(report, "__dict__") else str(report),
        }

    except ImportError:
        raise HTTPException(
            status_code=501, detail="Data cleanup service not available"
        )
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# ---------------------------------------------------------------------------
# Runtime Events / Audit
# ---------------------------------------------------------------------------


@router.get("/events")
async def get_runtime_events(
    limit: int = 50,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """Get recent runtime events for audit trail."""
    try:
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        from ai_karen_engine.database.models import ChatRuntimeEvent
        from sqlalchemy import select

        db = MultiTenantPostgresClient()
        async with db.get_async_session() as session:
            result = await session.execute(
                select(ChatRuntimeEvent)
                .order_by(ChatRuntimeEvent.created_at.desc())
                .limit(min(limit, 200))
            )
            events = result.scalars().all()

            return {
                "events": [
                    {
                        "id": str(ev.id),
                        "event_type": ev.event_type,
                        "mode": ev.mode,
                        "details": ev.details_json,
                        "created_at": ev.created_at.isoformat() if ev.created_at else None,
                    }
                    for ev in events
                ],
                "count": len(events),
            }

    except Exception as e:
        logger.error(f"Failed to fetch runtime events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events")
