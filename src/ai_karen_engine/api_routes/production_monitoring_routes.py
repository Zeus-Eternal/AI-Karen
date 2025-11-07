"""
Production Monitoring API Routes

Provides REST API endpoints for production monitoring metrics, alerts, and health status.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
try:
    from pydantic import BaseModel
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.production_monitoring_service import (
    get_production_monitoring_service,
    MetricType,
    AlertSeverity,
)
from ai_karen_engine.services.auth.auth_service import get_current_user

logger = get_logger(__name__)

# Create router
production_monitoring_router = APIRouter(
    prefix="/api/production/monitoring",
    tags=["production-monitoring"],
)


class AlertRequest(BaseModel):
    """Request model for alert operations"""
    message: str


class MetricUpdateRequest(BaseModel):
    """Request model for metric updates"""
    metric_type: str
    data: Dict[str, Any]


@production_monitoring_router.get("/status")
async def get_monitoring_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get production monitoring system status.
    
    Returns:
        Dict containing monitoring system status and basic metrics
    """
    try:
        monitoring_service = get_production_monitoring_service()
        return {
            "status": "active" if monitoring_service._monitoring_active else "inactive",
            "last_update": monitoring_service._last_metrics_update.isoformat(),
            "metrics_summary": monitoring_service.get_production_metrics_summary(),
        }
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")


@production_monitoring_router.get("/metrics/summary")
async def get_production_metrics_summary(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive production metrics summary.
    
    Returns:
        Dict containing all production metrics
    """
    try:
        monitoring_service = get_production_monitoring_service()
        return monitoring_service.get_production_metrics_summary()
    except Exception as e:
        logger.error(f"Error getting production metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics summary")


@production_monitoring_router.get("/metrics/response-formatting")
async def get_response_formatting_metrics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get response formatting specific metrics.
    
    Returns:
        Dict containing response formatting metrics
    """
    try:
        monitoring_service = get_production_monitoring_service()
        metrics = monitoring_service.response_formatting_metrics
        
        return {
            "total_requests": metrics.total_requests,
            "successful_formats": metrics.successful_formats,
            "failed_formats": metrics.failed_formats,
            "fallback_used": metrics.fallback_used,
            "success_rate": (
                metrics.successful_formats / max(1, metrics.total_requests) * 100
            ),
            "failure_rate": (
                metrics.failed_formats / max(1, metrics.total_requests) * 100
            ),
            "avg_format_time_ms": metrics.avg_format_time_ms,
            "formatter_usage": dict(metrics.formatter_usage),
            "error_types": dict(metrics.error_types),
        }
    except Exception as e:
        logger.error(f"Error getting response formatting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response formatting metrics")


@production_monitoring_router.get("/metrics/database-consistency")
async def get_database_consistency_metrics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get database consistency specific metrics.
    
    Returns:
        Dict containing database consistency metrics
    """
    try:
        monitoring_service = get_production_monitoring_service()
        metrics = monitoring_service.database_consistency_metrics
        
        return {
            "last_check_timestamp": (
                metrics.last_check_timestamp.isoformat()
                if metrics.last_check_timestamp else None
            ),
            "consistency_score": metrics.consistency_score,
            "cross_db_issues": metrics.cross_db_issues,
            "orphaned_records": metrics.orphaned_records,
            "missing_references": metrics.missing_references,
            "check_duration_ms": metrics.check_duration_ms,
            "database_health_scores": dict(metrics.database_health_scores),
            "total_issues": (
                metrics.cross_db_issues +
                metrics.orphaned_records +
                metrics.missing_references
            ),
        }
    except Exception as e:
        logger.error(f"Error getting database consistency metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database consistency metrics")


@production_monitoring_router.get("/metrics/authentication-anomalies")
async def get_authentication_anomaly_metrics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get authentication anomaly detection metrics.
    
    Returns:
        Dict containing authentication anomaly metrics
    """
    try:
        monitoring_service = get_production_monitoring_service()
        metrics = monitoring_service.auth_anomaly_metrics
        
        return {
            "failed_login_attempts": metrics.failed_login_attempts,
            "suspicious_patterns": metrics.suspicious_patterns,
            "brute_force_attempts": metrics.brute_force_attempts,
            "unusual_access_patterns": metrics.unusual_access_patterns,
            "blocked_ips_count": len(metrics.blocked_ips),
            "blocked_ips": list(metrics.blocked_ips),
            "anomaly_score": metrics.anomaly_score,
        }
    except Exception as e:
        logger.error(f"Error getting authentication anomaly metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get authentication anomaly metrics")


@production_monitoring_router.get("/metrics/performance-degradation")
async def get_performance_degradation_metrics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance degradation metrics.
    
    Returns:
        Dict containing performance degradation metrics
    """
    try:
        monitoring_service = get_production_monitoring_service()
        metrics = monitoring_service.performance_metrics
        
        return {
            "avg_response_time_ms": metrics.avg_response_time_ms,
            "p95_response_time_ms": metrics.p95_response_time_ms,
            "p99_response_time_ms": metrics.p99_response_time_ms,
            "error_rate_percent": metrics.error_rate_percent,
            "throughput_rps": metrics.throughput_rps,
            "resource_utilization": dict(metrics.resource_utilization),
            "degradation_score": metrics.degradation_score,
        }
    except Exception as e:
        logger.error(f"Error getting performance degradation metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance degradation metrics")


@production_monitoring_router.get("/alerts")
async def get_production_alerts(
    active_only: bool = Query(True, description="Return only active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get production alerts with optional filtering.
    
    Args:
        active_only: Return only unresolved alerts
        severity: Filter by alert severity (info, warning, critical)
        metric_type: Filter by metric type
        
    Returns:
        List of production alerts
    """
    try:
        monitoring_service = get_production_monitoring_service()
        
        if active_only:
            alerts = monitoring_service.get_active_alerts()
        else:
            alerts = [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "metric_type": alert.metric_type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "details": alert.details,
                    "resolved": alert.resolved,
                    "resolution_time": (
                        alert.resolution_time.isoformat()
                        if alert.resolution_time else None
                    ),
                }
                for alert in monitoring_service.active_alerts
            ]
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        if metric_type:
            alerts = [a for a in alerts if a["metric_type"] == metric_type]
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting production alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get production alerts")


@production_monitoring_router.post("/alerts/resolve")
async def resolve_production_alert(
    request: AlertRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually resolve a production alert.
    
    Args:
        request: Alert resolution request containing alert message
        
    Returns:
        Dict containing resolution status
    """
    try:
        monitoring_service = get_production_monitoring_service()
        resolved = await monitoring_service.resolve_alert(request.message)
        
        return {
            "resolved": resolved,
            "message": request.message,
            "timestamp": monitoring_service._last_metrics_update.isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error resolving production alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@production_monitoring_router.post("/start")
async def start_production_monitoring(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start production monitoring service.
    
    Returns:
        Dict containing start status
    """
    try:
        # Check if user has admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        monitoring_service = get_production_monitoring_service()
        await monitoring_service.start_monitoring()
        
        return {
            "status": "started",
            "timestamp": monitoring_service._last_metrics_update.isoformat(),
            "message": "Production monitoring service started successfully",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting production monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")


@production_monitoring_router.post("/stop")
async def stop_production_monitoring(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Stop production monitoring service.
    
    Returns:
        Dict containing stop status
    """
    try:
        # Check if user has admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        monitoring_service = get_production_monitoring_service()
        await monitoring_service.stop_monitoring()
        
        return {
            "status": "stopped",
            "timestamp": monitoring_service._last_metrics_update.isoformat(),
            "message": "Production monitoring service stopped successfully",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping production monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")


@production_monitoring_router.post("/metrics/update")
async def update_production_metrics(
    request: MetricUpdateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update production metrics (for internal service use).
    
    Args:
        request: Metric update request
        
    Returns:
        Dict containing update status
    """
    try:
        monitoring_service = get_production_monitoring_service()
        
        # Route to appropriate metric update method
        if request.metric_type == "response_formatting_success":
            monitoring_service.record_response_formatting_success(
                formatter_type=request.data.get("formatter_type", "unknown"),
                content_type=request.data.get("content_type", "unknown"),
                duration_ms=request.data.get("duration_ms", 0.0)
            )
        elif request.metric_type == "response_formatting_failure":
            monitoring_service.record_response_formatting_failure(
                formatter_type=request.data.get("formatter_type", "unknown"),
                error_type=request.data.get("error_type", "unknown"),
                error_message=request.data.get("error_message", "")
            )
        elif request.metric_type == "response_formatting_fallback":
            monitoring_service.record_response_formatting_fallback(
                original_formatter=request.data.get("original_formatter", "unknown"),
                fallback_reason=request.data.get("fallback_reason", "unknown")
            )
        elif request.metric_type == "authentication_failure":
            monitoring_service.record_authentication_failure(
                failure_reason=request.data.get("failure_reason", "unknown"),
                source_ip=request.data.get("source_ip", "unknown"),
                user_agent=request.data.get("user_agent")
            )
        elif request.metric_type == "api_response_time":
            monitoring_service.record_api_response_time(
                endpoint=request.data.get("endpoint", "unknown"),
                method=request.data.get("method", "unknown"),
                response_time_ms=request.data.get("response_time_ms", 0.0),
                status_code=request.data.get("status_code", 200)
            )
        elif request.metric_type == "database_consistency_update":
            await monitoring_service.update_database_consistency_metrics()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown metric type: {request.metric_type}")
        
        return {
            "status": "updated",
            "metric_type": request.metric_type,
            "timestamp": monitoring_service._last_metrics_update.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating production metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metrics")


@production_monitoring_router.get("/prometheus")
async def get_prometheus_metrics() -> str:
    """
    Get Prometheus-formatted metrics for scraping.
    
    Returns:
        Prometheus metrics in text format
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from server.metrics import PROMETHEUS_ENABLED
        
        if not PROMETHEUS_ENABLED:
            raise HTTPException(status_code=503, detail="Prometheus metrics not available")
        
        # Generate Prometheus metrics
        metrics_output = generate_latest()
        
        return metrics_output.decode('utf-8')
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Prometheus client not available")
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate metrics")


@production_monitoring_router.get("/health")
async def get_monitoring_health() -> Dict[str, Any]:
    """
    Get production monitoring system health status.
    
    Returns:
        Dict containing monitoring system health
    """
    try:
        monitoring_service = get_production_monitoring_service()
        
        # Get basic health information
        active_alerts = monitoring_service.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
        
        # Determine health status
        if critical_alerts:
            health_status = "critical"
        elif active_alerts:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "monitoring_active": monitoring_service._monitoring_active,
            "last_update": monitoring_service._last_metrics_update.isoformat(),
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "metrics_available": True,
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring health: {e}")
        return {
            "status": "error",
            "monitoring_active": False,
            "error": str(e),
            "metrics_available": False,
        }