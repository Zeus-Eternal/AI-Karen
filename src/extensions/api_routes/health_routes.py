"""
Health Dashboard API Routes - REST endpoints for health monitoring.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from extensions.core.registry.health_dashboard import (
    get_health_service,
    HealthStatus,
)

logger = logging.getLogger("kari.health_routes")

router = APIRouter(prefix="/api/health", tags=["health-dashboard"])


@router.get("/summary", response_model=Dict[str, Any])
async def get_health_summary():
    """
    Get a summary of the plugin ecosystem health.

    Returns:
        Overall health status with detailed metrics
    """
    try:
        service = get_health_service()
        summary = await service.get_health_summary()

        return {
            "status": "success",
            "data": summary,
        }

    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health summary: {str(e)}",
        )


@router.get("/snapshot", response_model=Dict[str, Any])
async def get_health_snapshot():
    """
    Get a detailed health snapshot.

    Returns:
        Complete health snapshot with all plugin records
    """
    try:
        service = get_health_service()
        snapshot = await service.collect_health_snapshot()

        return {
            "status": "success",
            "data": {
                "timestamp": snapshot.timestamp.isoformat(),
                "overall_status": snapshot.overall_status.value,
                "system_metrics": {
                    "total_plugins": snapshot.system_metrics.total_plugins,
                    "active_plugins": snapshot.system_metrics.active_plugins,
                    "pending_operations": snapshot.system_metrics.pending_operations,
                    "cpu_percent": round(snapshot.system_metrics.cpu_percent, 1),
                    "memory_percent": round(snapshot.system_metrics.memory_percent, 1),
                },
                "database_status": snapshot.database_status.value,
                "plugin_count": len(snapshot.plugin_health),
                "plugins": [
                    {
                        "plugin_id": p.plugin_id,
                        "name": p.name,
                        "version": p.version,
                        "backend_status": p.backend_status,
                        "frontend_status": p.frontend_status,
                        "state_machine_state": p.state_machine_state,
                        "is_validated": p.is_validated,
                        "has_errors": p.has_errors,
                        "error_count": p.error_count,
                        "last_error": p.last_error,
                        "last_error_time": p.last_error_time.isoformat()
                        if p.last_error_time
                        else None,
                        "load_time_ms": p.load_time_ms,
                        "memory_usage_mb": p.memory_usage_mb,
                        "cpu_usage_percent": p.cpu_usage_percent,
                        "hooks_assigned": p.hooks_assigned,
                        "last_loaded": p.last_loaded.isoformat()
                        if p.last_loaded
                        else None,
                        "uptime_minutes": round(p.uptime_minutes, 1)
                        if p.uptime_minutes
                        else None,
                    }
                    for p in snapshot.plugin_health
                ],
                "alerts": snapshot.alerts,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get health snapshot: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health snapshot: {str(e)}",
        )


@router.get("/plugin/{plugin_id}", response_model=Dict[str, Any])
async def get_plugin_health(
    plugin_id: str,
    hours: int = Query(24, ge=1, le=168),
):
    """
    Get health history for a specific plugin.

    Args:
        plugin_id: Plugin identifier
        hours: Number of hours of history to return

    Returns:
        Plugin health history timeline
    """
    try:
        service = get_health_service()
        history = await service.get_plugin_health_history(plugin_id, hours)

        return {
            "status": "success",
            "data": {
                "plugin_id": plugin_id,
                "history": history,
                "total_entries": len(history),
                "time_range_hours": hours,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get plugin health history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get plugin health history: {str(e)}",
        )


@router.get("/trends", response_model=Dict[str, Any])
async def get_health_trends(
    hours: int = Query(24, ge=1, le=168),
    interval_minutes: int = Query(60, ge=1, le=1440),
):
    """
    Get health trends over time.

    Args:
        hours: Number of hours to analyze
        interval_minutes: Data collection interval in minutes

    Returns:
        Health trend data with metrics
    """
    try:
        service = get_health_service()
        trend = await service.get_health_trends(hours, interval_minutes)

        return {
            "status": "success",
            "data": {
                "period_start": trend.period_start.isoformat(),
                "period_end": trend.period_end.isoformat(),
                "avg_plugin_count": round(trend.avg_plugin_count, 1),
                "avg_active_count": round(trend.avg_active_count, 1),
                "error_count": trend.error_count,
                "degradation_events": trend.degradation_events,
                "snapshot_count": len(trend.snapshots),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get health trends: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health trends: {str(e)}",
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts(
    severity: Optional[str] = Query(
        None, description="Filter by severity (critical, warning)"
    ),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get active health alerts.

    Args:
        severity: Filter by severity
        limit: Maximum alerts to return

    Returns:
        List of active alerts
    """
    try:
        service = get_health_service()
        alerts = service.get_active_alerts(severity, limit)

        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "total": len(alerts),
                "critical_count": sum(
                    1 for a in alerts if a.get("severity") == "critical"
                ),
                "warning_count": sum(
                    1 for a in alerts if a.get("severity") == "warning"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}",
        )


@router.get("/snapshots", response_model=Dict[str, Any])
async def get_recent_snapshots(
    limit: int = Query(10, ge=1, le=100),
):
    """
    Get recent health snapshots.

    Args:
        limit: Maximum snapshots to return

    Returns:
        List of recent snapshots
    """
    try:
        service = get_health_service()
        snapshots = service.get_recent_snapshots(limit)

        return {
            "status": "success",
            "data": {
                "snapshots": [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "overall_status": s.overall_status.value,
                        "plugin_count": len(s.plugin_health),
                        "alert_count": len(s.alerts),
                    }
                    for s in snapshots
                ],
                "total": len(snapshots),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get snapshots: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get snapshots: {str(e)}",
        )


@router.get("/plugins/{plugin_id}/diagnose", response_model=Dict[str, Any])
async def diagnose_plugin(plugin_id: str):
    """
    Diagnose a specific plugin's health issues.

    Args:
        plugin_id: Plugin identifier

    Returns:
        Detailed diagnostic information
    """
    try:
        service = get_health_service()

        # Get current snapshot
        snapshot = await service.collect_health_snapshot()

        # Find the plugin
        plugin_record = next(
            (p for p in snapshot.plugin_health if p.plugin_id == plugin_id),
            None,
        )

        if not plugin_record:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found",
            )

        # Build diagnostic report
        diagnostics = {
            "plugin_id": plugin_id,
            "name": plugin_record.name,
            "version": plugin_record.version,
            "timestamp": datetime.utcnow().isoformat(),
            "status": plugin_record.backend_status,
            "state_machine": plugin_record.state_machine_state,
            "issues": [],
            "recommendations": [],
        }

        # Check for issues
        if plugin_record.has_errors:
            diagnostics["issues"].append(
                {
                    "severity": "error",
                    "category": "runtime",
                    "message": f"Plugin has {plugin_record.error_count} errors",
                    "details": plugin_record.last_error,
                }
            )
            diagnostics["recommendations"].append(
                {
                    "action": "restart",
                    "message": "Restart the plugin to clear errors",
                }
            )

        if plugin_record.backend_status != "active":
            diagnostics["issues"].append(
                {
                    "severity": "warning",
                    "category": "status",
                    "message": f"Plugin is not active (status: {plugin_record.backend_status})",
                }
            )
            diagnostics["recommendations"].append(
                {
                    "action": "enable",
                    "message": "Enable the plugin if it should be running",
                }
            )

        if plugin_record.state_machine_state == "ERROR":
            diagnostics["issues"].append(
                {
                    "severity": "error",
                    "category": "state",
                    "message": "State machine is in error state",
                }
            )
            diagnostics["recommendations"].append(
                {
                    "action": "reset",
                    "message": "Reset the plugin to initial state",
                }
            )

        if not plugin_record.is_validated:
            diagnostics["issues"].append(
                {
                    "severity": "warning",
                    "category": "validation",
                    "message": "Plugin has not been validated",
                }
            )
            diagnostics["recommendations"].append(
                {
                    "action": "validate",
                    "message": "Run validation on the plugin",
                }
            )

        if plugin_record.load_time_ms and plugin_record.load_time_ms > 5000:
            diagnostics["issues"].append(
                {
                    "severity": "warning",
                    "category": "performance",
                    "message": f"Plugin load time is slow ({plugin_record.load_time_ms}ms)",
                }
            )

        if plugin_record.memory_usage_mb and plugin_record.memory_usage_mb > 256:
            diagnostics["issues"].append(
                {
                    "severity": "warning",
                    "category": "resources",
                    "message": f"High memory usage ({plugin_record.memory_usage_mb}MB)",
                }
            )

        # If no issues found
        if not diagnostics["issues"]:
            diagnostics["issues"].append(
                {
                    "severity": "info",
                    "category": "health",
                    "message": "No issues detected",
                }
            )

        return {
            "status": "success",
            "data": diagnostics,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to diagnose plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to diagnose plugin: {str(e)}",
        )
