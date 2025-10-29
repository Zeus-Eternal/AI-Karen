"""
Extension Debugging API Routes

FastAPI routes for extension debugging and monitoring endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from .debug_manager import ExtensionDebugManager
from .dashboard import ExtensionDebugDashboard
from .models import LogLevel, AlertSeverity


# Request/Response Models
class DebugSessionRequest(BaseModel):
    session_id: Optional[str] = None
    configuration: Dict[str, Any] = {}


class DebugSessionResponse(BaseModel):
    session_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    configuration: Dict[str, Any]
    collected_data: Dict[str, Any] = {}


class LogSearchRequest(BaseModel):
    query: Optional[str] = None
    level: Optional[str] = None
    source: Optional[str] = None
    since: Optional[str] = None
    limit: int = 100


class AlertResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None


class MetricsRequest(BaseModel):
    metric_names: List[str]
    time_window_hours: int = 1


# Global debug managers registry
debug_managers: Dict[str, ExtensionDebugManager] = {}


def get_debug_manager(extension_id: str) -> ExtensionDebugManager:
    """Get or create debug manager for extension."""
    if extension_id not in debug_managers:
        raise HTTPException(status_code=404, detail=f"Debug manager not found for extension {extension_id}")
    return debug_managers[extension_id]


def get_dashboard(extension_id: str) -> ExtensionDebugDashboard:
    """Get dashboard for extension."""
    debug_manager = get_debug_manager(extension_id)
    return ExtensionDebugDashboard(debug_manager)


# Create router
router = APIRouter(prefix="/api/extensions/debugging", tags=["Extension Debugging"])


@router.post("/managers/{extension_id}/start")
async def start_debug_manager(extension_id: str):
    """Start debug manager for an extension."""
    if extension_id in debug_managers:
        debug_manager = debug_managers[extension_id]
        if debug_manager._running:
            return {"status": "already_running", "extension_id": extension_id}
    else:
        # Create new debug manager
        debug_manager = ExtensionDebugManager(extension_id, extension_id)
        debug_managers[extension_id] = debug_manager
    
    await debug_manager.start()
    
    return {
        "status": "started",
        "extension_id": extension_id,
        "enabled_components": debug_manager._get_enabled_components()
    }


@router.post("/managers/{extension_id}/stop")
async def stop_debug_manager(extension_id: str):
    """Stop debug manager for an extension."""
    debug_manager = get_debug_manager(extension_id)
    await debug_manager.stop()
    
    return {"status": "stopped", "extension_id": extension_id}


@router.get("/managers/{extension_id}/status")
async def get_debug_manager_status(extension_id: str):
    """Get debug manager status."""
    debug_manager = get_debug_manager(extension_id)
    summary = debug_manager.get_debug_summary()
    
    return {
        "extension_id": extension_id,
        "status": "running" if debug_manager._running else "stopped",
        "summary": summary
    }


@router.get("/managers")
async def list_debug_managers():
    """List all debug managers."""
    managers = []
    for extension_id, debug_manager in debug_managers.items():
        managers.append({
            "extension_id": extension_id,
            "extension_name": debug_manager.extension_name,
            "status": "running" if debug_manager._running else "stopped",
            "enabled_components": debug_manager._get_enabled_components()
        })
    
    return {"managers": managers}


# Dashboard endpoints
@router.get("/dashboard/{extension_id}")
async def get_dashboard_data(extension_id: str):
    """Get comprehensive dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_dashboard_data()


@router.get("/dashboard/{extension_id}/overview")
async def get_overview_data(extension_id: str):
    """Get overview dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_overview_data()


@router.get("/dashboard/{extension_id}/metrics")
async def get_metrics_data(
    extension_id: str,
    time_window_hours: int = Query(1, ge=1, le=168)
):
    """Get metrics dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_metrics_data(time_window_hours)


@router.get("/dashboard/{extension_id}/logs")
async def get_logs_data(
    extension_id: str,
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get logs dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_logs_data(limit, level, search)


@router.get("/dashboard/{extension_id}/errors")
async def get_errors_data(
    extension_id: str,
    time_window_hours: int = Query(24, ge=1, le=168)
):
    """Get errors dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_errors_data(time_window_hours)


@router.get("/dashboard/{extension_id}/alerts")
async def get_alerts_data(extension_id: str):
    """Get alerts dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_alerts_data()


@router.get("/dashboard/{extension_id}/performance")
async def get_performance_data(extension_id: str):
    """Get performance dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_performance_data()


@router.get("/dashboard/{extension_id}/health")
async def get_health_data(extension_id: str):
    """Get health dashboard data."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_health_data()


# Real-time endpoints
@router.post("/dashboard/{extension_id}/metrics/realtime")
async def get_realtime_metrics(extension_id: str, request: MetricsRequest):
    """Get real-time metrics."""
    dashboard = get_dashboard(extension_id)
    return dashboard.get_real_time_metrics(request.metric_names)


@router.get("/dashboard/{extension_id}/logs/stream")
async def get_log_stream(
    extension_id: str,
    since: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Get streaming log data."""
    dashboard = get_dashboard(extension_id)
    
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid since timestamp format")
    
    return dashboard.get_log_stream(since_dt, limit)


@router.post("/dashboard/{extension_id}/logs/search")
async def search_logs(extension_id: str, request: LogSearchRequest):
    """Search logs with advanced filtering."""
    dashboard = get_dashboard(extension_id)
    
    since_dt = None
    if request.since:
        try:
            since_dt = datetime.fromisoformat(request.since)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid since timestamp format")
    
    return dashboard.search_logs(
        query=request.query,
        level=request.level,
        source=request.source,
        since=since_dt,
        limit=request.limit
    )


# Debug session endpoints
@router.post("/sessions/{extension_id}/start")
async def start_debug_session(extension_id: str, request: DebugSessionRequest):
    """Start a debug session."""
    debug_manager = get_debug_manager(extension_id)
    
    session_id = debug_manager.start_debug_session(
        session_id=request.session_id,
        configuration=request.configuration
    )
    
    return {"session_id": session_id, "status": "started"}


@router.post("/sessions/{extension_id}/{session_id}/stop")
async def stop_debug_session(extension_id: str, session_id: str):
    """Stop a debug session."""
    debug_manager = get_debug_manager(extension_id)
    
    session = debug_manager.stop_debug_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return DebugSessionResponse(
        session_id=session.id,
        status=session.status,
        start_time=session.start_time.isoformat(),
        end_time=session.end_time.isoformat() if session.end_time else None,
        configuration=session.configuration,
        collected_data=session.collected_data
    )


@router.get("/sessions/{extension_id}")
async def list_debug_sessions(extension_id: str):
    """List active debug sessions."""
    debug_manager = get_debug_manager(extension_id)
    
    sessions = []
    for session in debug_manager.active_sessions.values():
        duration_seconds = (datetime.utcnow() - session.start_time).total_seconds()
        sessions.append({
            "session_id": session.id,
            "start_time": session.start_time.isoformat(),
            "duration_seconds": duration_seconds,
            "configuration": session.configuration
        })
    
    return {"active_sessions": sessions}


# Health and diagnostics endpoints
@router.post("/health/{extension_id}/check")
async def run_health_check(extension_id: str):
    """Run health diagnostics."""
    debug_manager = get_debug_manager(extension_id)
    health_status = await debug_manager.run_diagnostics()
    
    return {
        "extension_id": extension_id,
        "overall_status": health_status.overall_status,
        "last_check": health_status.last_check.isoformat(),
        "diagnostics": [d.to_dict() for d in health_status.diagnostics],
        "metrics_summary": health_status.metrics_summary,
        "recent_errors_count": len(health_status.recent_errors),
        "active_alerts_count": len(health_status.active_alerts)
    }


@router.get("/health/{extension_id}")
async def get_health_status(extension_id: str):
    """Get current health status."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.health_status:
        raise HTTPException(status_code=404, detail="No health data available")
    
    health_status = debug_manager.health_status
    return {
        "extension_id": extension_id,
        "overall_status": health_status.overall_status,
        "last_check": health_status.last_check.isoformat(),
        "diagnostics": [d.to_dict() for d in health_status.diagnostics]
    }


# Alert management endpoints
@router.get("/alerts/{extension_id}")
async def get_alerts(
    extension_id: str,
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None)
):
    """Get alerts for extension."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.alert_manager:
        raise HTTPException(status_code=404, detail="Alerting not enabled")
    
    severity_filter = None
    if severity:
        try:
            severity_filter = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid severity level")
    
    alerts = debug_manager.alert_manager.get_active_alerts(
        severity=severity_filter,
        alert_type=alert_type
    )
    
    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "total_count": len(alerts)
    }


@router.post("/alerts/{extension_id}/{alert_id}/resolve")
async def resolve_alert(extension_id: str, alert_id: str, request: AlertResolveRequest):
    """Resolve an alert."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.alert_manager:
        raise HTTPException(status_code=404, detail="Alerting not enabled")
    
    await debug_manager.alert_manager.resolve_alert(alert_id, request.resolution_notes)
    
    return {"status": "resolved", "alert_id": alert_id}


@router.get("/alerts/{extension_id}/statistics")
async def get_alert_statistics(extension_id: str):
    """Get alert statistics."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.alert_manager:
        raise HTTPException(status_code=404, detail="Alerting not enabled")
    
    return debug_manager.alert_manager.get_alert_statistics()


# Export endpoints
@router.get("/export/{extension_id}/logs")
async def export_logs(
    extension_id: str,
    format: str = Query("json", regex="^(json|csv)$")
):
    """Export logs."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.logger:
        raise HTTPException(status_code=404, detail="Logging not enabled")
    
    try:
        exported_data = debug_manager.logger.export_logs(format)
        return {"format": format, "data": exported_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/{extension_id}/metrics")
async def export_metrics(
    extension_id: str,
    format: str = Query("json", regex="^(json|csv|prometheus)$")
):
    """Export metrics."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.metrics_collector:
        raise HTTPException(status_code=404, detail="Metrics collection not enabled")
    
    try:
        exported_data = debug_manager.metrics_collector.export_metrics(format)
        return {"format": format, "data": exported_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/{extension_id}/errors")
async def export_errors(
    extension_id: str,
    format: str = Query("json", regex="^(json|csv)$")
):
    """Export errors."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.error_tracker:
        raise HTTPException(status_code=404, detail="Error tracking not enabled")
    
    try:
        exported_data = debug_manager.error_tracker.export_errors(format)
        return {"format": format, "data": exported_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/{extension_id}/alerts")
async def export_alerts(
    extension_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    include_resolved: bool = Query(True)
):
    """Export alerts."""
    debug_manager = get_debug_manager(extension_id)
    
    if not debug_manager.alert_manager:
        raise HTTPException(status_code=404, detail="Alerting not enabled")
    
    try:
        exported_data = debug_manager.alert_manager.export_alerts(format, include_resolved)
        return {"format": format, "data": exported_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/{extension_id}/all")
async def export_all_debug_data(
    extension_id: str,
    format: str = Query("json", regex="^(json)$")
):
    """Export all debug data."""
    debug_manager = get_debug_manager(extension_id)
    
    try:
        exported_data = debug_manager.export_debug_data(format)
        return {"format": format, "data": exported_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Utility endpoints
@router.delete("/managers/{extension_id}")
async def cleanup_debug_manager(extension_id: str):
    """Clean up debug manager and all its data."""
    if extension_id not in debug_managers:
        raise HTTPException(status_code=404, detail=f"Debug manager not found for extension {extension_id}")
    
    debug_manager = debug_managers[extension_id]
    await debug_manager.stop()
    
    # Clear all data
    if debug_manager.logger:
        debug_manager.logger.handler.log_entries.clear()
    if debug_manager.metrics_collector:
        debug_manager.metrics_collector.buffer.clear()
    if debug_manager.error_tracker:
        debug_manager.error_tracker.errors.clear()
    if debug_manager.tracer:
        debug_manager.tracer.clear_traces()
    if debug_manager.profiler:
        debug_manager.profiler.clear_profiles()
    
    # Remove from registry
    del debug_managers[extension_id]
    
    return {"status": "cleaned_up", "extension_id": extension_id}