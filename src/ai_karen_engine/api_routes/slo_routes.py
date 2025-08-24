"""
SLO Monitoring API Routes - Phase 4.1.d
Production-ready SLO monitoring endpoints with dashboard integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Graceful imports with fallback mechanisms
try:
    from ai_karen_engine.services.slo_monitoring import (
        AlertSeverity,
        SLOStatus,
        get_slo_monitor,
    )

    SLO_MONITORING_AVAILABLE = True
except ImportError:
    logger.warning("SLO monitoring not available, using fallback")
    SLO_MONITORING_AVAILABLE = False

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
    from ai_karen_engine.services.metrics_service import get_metrics_service

    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("Metrics service not available, using fallback")
    METRICS_AVAILABLE = False


# Response models
class SLOThresholdStatus(BaseModel):
    """SLO threshold status response"""

    name: str
    current_value: Optional[float]
    threshold_value: float
    status: str
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None


class SLOTargetStatus(BaseModel):
    """SLO target status response"""

    name: str
    description: str
    target_value: float
    status: str
    thresholds: List[SLOThresholdStatus]


class ActiveAlert(BaseModel):
    """Active alert response"""

    id: str
    rule_name: str
    severity: str
    message: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecentViolation(BaseModel):
    """Recent violation response"""

    slo_name: str
    threshold_name: str
    actual_value: float
    threshold_value: float
    severity: str
    timestamp: str


class SLODashboardResponse(BaseModel):
    """SLO dashboard data response"""

    slo_status: Dict[str, SLOTargetStatus]
    active_alerts: List[ActiveAlert]
    recent_violations: List[RecentViolation]
    timestamp: str
    system_health: Dict[str, Any] = Field(default_factory=dict)


class MetricsExportResponse(BaseModel):
    """Metrics export response"""

    content: str
    content_type: str
    timestamp: str


# Import unified schemas
from ai_karen_engine.api_routes.unified_schemas import (
    ErrorHandler,
    ErrorResponse,
    ErrorType,
    ValidationUtils,
)

# Create router
router = APIRouter(tags=["slo"])


def get_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID for request tracking"""
    if CORRELATION_AVAILABLE:
        headers = {key: value for key, value in request.headers.items()}
        return CorrelationService.get_or_create_correlation_id(headers)
    else:
        return request.headers.get("X-Correlation-Id", "unknown")


@router.get("/status", response_model=Dict[str, SLOTargetStatus])
async def get_slo_status(request: Request):
    """
    Get current SLO status for all targets.

    Returns the current status of all SLO targets including threshold values,
    current measurements, and violation status.
    """
    correlation_id = get_correlation_id(request)

    # Set correlation ID in context
    if CORRELATION_AVAILABLE:
        CorrelationService.set_correlation_id(correlation_id)

    try:
        if not SLO_MONITORING_AVAILABLE:
            # Return fallback status
            return {
                "fallback": SLOTargetStatus(
                    name="fallback",
                    description="SLO monitoring not available",
                    target_value=1.0,
                    status=SLOStatus.UNKNOWN.value
                    if SLO_MONITORING_AVAILABLE
                    else "unknown",
                    thresholds=[],
                )
            }

        slo_monitor = get_slo_monitor()
        slo_status = slo_monitor.get_slo_status()

        # Convert to response models
        response = {}
        for slo_name, status_data in slo_status.items():
            thresholds = []
            for threshold_data in status_data.get("thresholds", []):
                thresholds.append(
                    SLOThresholdStatus(
                        name=threshold_data["name"],
                        current_value=threshold_data["current_value"],
                        threshold_value=threshold_data["threshold_value"],
                        status=threshold_data["status"],
                    )
                )

            response[slo_name] = SLOTargetStatus(
                name=status_data["name"],
                description=status_data["description"],
                target_value=status_data["target_value"],
                status=status_data["status"],
                thresholds=thresholds,
            )

        logger.info(
            f"Retrieved SLO status for {len(response)} targets",
            extra={"correlation_id": correlation_id, "slo_count": len(response)},
        )

        return response

    except Exception as e:
        logger.error(
            f"Failed to get SLO status: {e}", extra={"correlation_id": correlation_id}
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(request.url.path), error=e
        )
        raise HTTPException(
            status_code=500, detail=error_response.model_dump(mode="json")
        )


@router.get("/dashboard", response_model=SLODashboardResponse)
async def get_slo_dashboard(request: Request):
    """
    Get comprehensive SLO dashboard data.

    Returns SLO status, active alerts, recent violations, and system health
    information for dashboard display.
    """
    correlation_id = get_correlation_id(request)

    # Set correlation ID in context
    if CORRELATION_AVAILABLE:
        CorrelationService.set_correlation_id(correlation_id)

    try:
        if not SLO_MONITORING_AVAILABLE:
            # Return fallback dashboard
            return SLODashboardResponse(
                slo_status={},
                active_alerts=[],
                recent_violations=[],
                timestamp=datetime.utcnow().isoformat(),
                system_health={
                    "status": "unknown",
                    "message": "SLO monitoring not available",
                },
            )

        slo_monitor = get_slo_monitor()
        dashboard_data = slo_monitor.get_dashboard_data()

        # Convert SLO status
        slo_status = {}
        for slo_name, status_data in dashboard_data["slo_status"].items():
            thresholds = []
            for threshold_data in status_data.get("thresholds", []):
                thresholds.append(
                    SLOThresholdStatus(
                        name=threshold_data["name"],
                        current_value=threshold_data["current_value"],
                        threshold_value=threshold_data["threshold_value"],
                        status=threshold_data["status"],
                    )
                )

            slo_status[slo_name] = SLOTargetStatus(
                name=status_data["name"],
                description=status_data["description"],
                target_value=status_data["target_value"],
                status=status_data["status"],
                thresholds=thresholds,
            )

        # Convert active alerts
        active_alerts = [
            ActiveAlert(
                id=alert["id"],
                rule_name=alert["rule_name"],
                severity=alert["severity"],
                message=alert["message"],
                timestamp=alert["timestamp"],
                metadata=alert["metadata"],
            )
            for alert in dashboard_data["active_alerts"]
        ]

        # Convert recent violations
        recent_violations = [
            RecentViolation(
                slo_name=violation["slo_name"],
                threshold_name=violation["threshold_name"],
                actual_value=violation["actual_value"],
                threshold_value=violation["threshold_value"],
                severity=violation["severity"],
                timestamp=violation["timestamp"],
            )
            for violation in dashboard_data["recent_violations"]
        ]

        # Get system health from metrics service
        system_health = {"status": "healthy"}
        if METRICS_AVAILABLE:
            try:
                metrics_service = get_metrics_service()
                stats = metrics_service.get_stats_summary()
                system_health.update(
                    {
                        "metrics_backend": stats.get("metrics_backend", "unknown"),
                        "registry_available": stats.get("registry_available", False),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to get system health: {e}")
                system_health["status"] = "degraded"
                system_health["message"] = "Metrics service unavailable"

        response = SLODashboardResponse(
            slo_status=slo_status,
            active_alerts=active_alerts,
            recent_violations=recent_violations,
            timestamp=dashboard_data["timestamp"],
            system_health=system_health,
        )

        logger.info(
            f"Retrieved SLO dashboard data",
            extra={
                "correlation_id": correlation_id,
                "slo_count": len(slo_status),
                "active_alerts": len(active_alerts),
                "recent_violations": len(recent_violations),
            },
        )

        return response

    except Exception as e:
        logger.error(
            f"Failed to get SLO dashboard: {e}",
            extra={"correlation_id": correlation_id},
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(request.url.path), error=e
        )
        raise HTTPException(
            status_code=500, detail=error_response.model_dump(mode="json")
        )


@router.get("/metrics", response_model=MetricsExportResponse)
async def export_metrics(request: Request):
    """
    Export metrics in Prometheus format.

    Returns all collected metrics in Prometheus exposition format
    for integration with monitoring systems.
    """
    correlation_id = get_correlation_id(request)

    # Set correlation ID in context
    if CORRELATION_AVAILABLE:
        CorrelationService.set_correlation_id(correlation_id)

    try:
        if not METRICS_AVAILABLE:
            # Return fallback metrics
            return MetricsExportResponse(
                content="# Metrics service not available\n",
                content_type="text/plain; charset=utf-8",
                timestamp=datetime.utcnow().isoformat(),
            )

        metrics_service = get_metrics_service()
        content = metrics_service.get_metrics_export()
        content_type = metrics_service.get_content_type()

        logger.debug(
            f"Exported metrics",
            extra={
                "correlation_id": correlation_id,
                "content_length": len(content),
                "content_type": content_type,
            },
        )

        return MetricsExportResponse(
            content=content,
            content_type=content_type,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(
            f"Failed to export metrics: {e}", extra={"correlation_id": correlation_id}
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(request.url.path), error=e
        )
        raise HTTPException(
            status_code=500, detail=error_response.model_dump(mode="json")
        )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, request: Request):
    """
    Resolve an active alert.

    Marks the specified alert as resolved and removes it from active alerts.
    """
    correlation_id = get_correlation_id(request)

    # Set correlation ID in context
    if CORRELATION_AVAILABLE:
        CorrelationService.set_correlation_id(correlation_id)

    try:
        if not SLO_MONITORING_AVAILABLE:
            raise HTTPException(status_code=503, detail="SLO monitoring not available")

        slo_monitor = get_slo_monitor()
        slo_monitor.resolve_alert(alert_id)

        logger.info(
            f"Resolved alert: {alert_id}",
            extra={"correlation_id": correlation_id, "alert_id": alert_id},
        )

        return {
            "success": True,
            "message": f"Alert {alert_id} resolved",
            "correlation_id": correlation_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to resolve alert {alert_id}: {e}",
            extra={"correlation_id": correlation_id},
        )

        error_response = ErrorHandler.create_internal_error_response(
            correlation_id=correlation_id, path=str(request.url.path), error=e
        )
        raise HTTPException(
            status_code=500, detail=error_response.model_dump(mode="json")
        )


@router.get("/health")
async def health_check():
    """Health check for SLO monitoring service"""
    return {
        "status": "healthy",
        "service": "slo_monitoring",
        "dependencies": {
            "slo_monitoring": SLO_MONITORING_AVAILABLE,
            "correlation": CORRELATION_AVAILABLE,
            "metrics": METRICS_AVAILABLE,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# Export router for inclusion in main FastAPI app
__all__ = ["router"]
