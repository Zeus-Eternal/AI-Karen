from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

# Local development context helper
from ai_karen_engine.core.dependencies import bypass_user_context_func
from ai_karen_engine.core.logging import get_logger
from services.memory.data_cleanup_service import get_data_cleanup_service, CleanupReport

logger = get_logger(__name__)

# Use the canonical prefix established in routers.py
router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


# Models for the UI integration
class CleanupRequest(BaseModel):
    """Request model for data cleanup."""

    dry_run: bool = Field(
        True, description="If True, only report changes without applying them"
    )
    categories: Optional[List[str]] = Field(
        None, description="Specific categories to clean (files, users, cache, backups)"
    )


class CleanupRecommendationResponse(BaseModel):
    """Response model for cleanup recommendations."""

    recommendations: List[str] = Field(
        ..., description="List of cleanup recommendations"
    )
    timestamp: str = Field(..., description="Timestamp of the recommendations")


class MaintenanceStatusResponse(BaseModel):
    """Overall status or maintenance readiness."""

    status: str
    last_maintenance: Optional[str] = None
    pending_tasks: int = 0
    storage_usage: str = "optimized"


@router.get("/recommendations", response_model=CleanupRecommendationResponse)
async def get_cleanup_recommendations(
    user_ctx: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """Retrieve system diagnostics and data cleanup recommendations."""
    # Enforce RBAC for administrative maintenance
    if "admin" not in user_ctx.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maintenance operations require admin privileges",
        )

    try:
        service = get_data_cleanup_service()
        recommendations = service.get_cleanup_recommendations()

        return CleanupRecommendationResponse(
            recommendations=recommendations, timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to get cleanup recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}",
        )


@router.post("/cleanup")
async def run_system_cleanup(
    dry_run: bool = Query(
        True,
        description="If true, only simulate cleanup without actually deleting files",
    ),
    user_ctx: Dict[str, Any] = Depends(bypass_user_context_func),
) -> Dict[str, Any]:
    """
    Perform system-wide data cleanup and maintenance.

    This includes:
    - Removing demo user accounts
    - Cleaning up test data files
    - Removing temporary and old log files
    - Clearing expired cache entries
    """
    # Enforce RBAC for administrative maintenance
    if "admin" not in user_ctx.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maintenance operations require admin privileges",
        )

    try:
        cleanup_service = get_data_cleanup_service()

        # Run cleanup process using correct method name
        report = await cleanup_service.cleanup_all(dry_run=dry_run)

        # Format report as flat dict for easier UI consumption
        return {
            "timestamp": report.timestamp.isoformat(),
            "dry_run": report.dry_run,
            "total_actions": report.total_actions,
            "successful_actions": report.successful_actions,
            "failed_actions": report.failed_actions,
            "bytes_cleaned": report.bytes_cleaned,
            "summary": report.summary,
            "actions": [
                {
                    "action_type": a.action_type,
                    "target": a.target,
                    "description": a.description,
                    "size_bytes": a.size_bytes,
                    "count": a.count,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in report.actions
            ],
            "errors": report.errors,
        }

    except Exception as exc:
        logger.error(f"System cleanup failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Maintenance cleanup failed: {str(exc)}"
        ) from exc


@router.get("/status", response_model=MaintenanceStatusResponse)
async def get_maintenance_status(
    user_ctx: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """Retrieve the general maintenance health of the engine."""
    if "admin" not in user_ctx.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maintenance status requires admin privileges",
        )

    # Static info for now - can be expanded to check database size, fragmentation etc.
    return MaintenanceStatusResponse(
        status="operational",
        last_maintenance=None,
        pending_tasks=0,
        storage_usage="optimized",
    )
