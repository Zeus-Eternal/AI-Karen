"""
Extension Monitoring Dashboard API

FastAPI routes for accessing monitoring data, metrics, and alerts.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from .extension_metrics_dashboard import extension_dashboard, AlertSeverity, Alert

logger = logging.getLogger(__name__)

# Create router for monitoring endpoints
monitoring_router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@monitoring_router.get("/dashboard")
async def get_dashboard_data() -> Dict[str, Any]:
    """Get complete dashboard data including all metrics and alerts."""
    try:
        return extension_dashboard.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@monitoring_router.get("/authentication/metrics")
async def get_authentication_metrics() -> Dict[str, Any]:
    """Get authentication-specific metrics."""
    try:
        return extension_dashboard.metrics_collector.get_auth_metrics()
    except Exception as e:
        logger.error(f"Error getting authentication metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get authentication metrics")


@monitoring_router.get("/health/metrics")
async def get_service_health_metrics() -> Dict[str, Any]:
    """Get service health metrics."""
    try:
        return extension_dashboard.metrics_collector.get_service_health_metrics()
    except Exception as e:
        logger.error(f"Error getting service health metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service health metrics")


@monitoring_router.get("/performance/metrics")
async def get_api_performance_metrics() -> Dict[str, Any]:
    """Get API performance metrics."""
    try:
        return extension_dashboard.metrics_collector.get_api_performance_metrics()
    except Exception as e:
        logger.error(f"Error getting API performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API performance metrics")


@monitoring_router.get("/alerts/active")
async def get_active_alerts() -> List[Dict[str, Any]]:
    """Get all currently active alerts."""
    try:
        return extension_dashboard.alert_manager.get_active_alerts()
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active alerts")


@monitoring_router.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000, description="Number of alerts to return")
) -> List[Dict[str, Any]]:
    """Get alert history."""
    try:
        return extension_dashboard.alert_manager.get_alert_history(limit)
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert history")


@monitoring_router.post("/alerts")
async def create_alert(alert_data: Dict[str, Any]) -> Dict[str, str]:
    """Create a new alert rule."""
    try:
        # Validate required fields
        required_fields = ['id', 'name', 'description', 'severity', 'condition', 'threshold']
        for field in required_fields:
            if field not in alert_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create alert
        alert = Alert(
            id=alert_data['id'],
            name=alert_data['name'],
            description=alert_data['description'],
            severity=AlertSeverity(alert_data['severity']),
            condition=alert_data['condition'],
            threshold=float(alert_data['threshold'])
        )
        
        extension_dashboard.alert_manager.add_alert(alert)
        
        return {"message": f"Alert '{alert.name}' created successfully", "alert_id": alert.id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid alert data: {e}")
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@monitoring_router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str) -> Dict[str, str]:
    """Delete an alert rule."""
    try:
        extension_dashboard.alert_manager.remove_alert(alert_id)
        return {"message": f"Alert '{alert_id}' deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert")


@monitoring_router.get("/status")
async def get_monitoring_status() -> Dict[str, Any]:
    """Get monitoring system status."""
    try:
        auth_metrics = extension_dashboard.metrics_collector.get_auth_metrics()
        health_metrics = extension_dashboard.metrics_collector.get_service_health_metrics()
        api_metrics = extension_dashboard.metrics_collector.get_api_performance_metrics()
        active_alerts = extension_dashboard.alert_manager.get_active_alerts()
        
        # Calculate overall system health
        overall_health = "healthy"
        if len(active_alerts) > 0:
            critical_alerts = [a for a in active_alerts if a['severity'] == 'critical']
            error_alerts = [a for a in active_alerts if a['severity'] == 'error']
            
            if critical_alerts:
                overall_health = "critical"
            elif error_alerts:
                overall_health = "degraded"
            else:
                overall_health = "warning"
        
        return {
            "monitoring_active": extension_dashboard.monitoring_active,
            "overall_health": overall_health,
            "summary": {
                "auth_success_rate": auth_metrics.get('success_rate', 0),
                "service_health_percentage": health_metrics.get('health_percentage', 0),
                "api_error_rate": api_metrics.get('error_rate', 0),
                "active_alerts_count": len(active_alerts),
                "total_api_requests": api_metrics.get('total_requests', 0)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")


@monitoring_router.post("/test/auth-success")
async def test_record_auth_success(
    response_time: float = Query(..., description="Response time in seconds"),
    user_id: Optional[str] = Query(None, description="User ID")
) -> Dict[str, str]:
    """Test endpoint to record authentication success (for testing/demo purposes)."""
    try:
        extension_dashboard.record_auth_success(response_time, user_id)
        return {"message": "Authentication success recorded"}
    except Exception as e:
        logger.error(f"Error recording auth success: {e}")
        raise HTTPException(status_code=500, detail="Failed to record auth success")


@monitoring_router.post("/test/auth-failure")
async def test_record_auth_failure(
    response_time: float = Query(..., description="Response time in seconds"),
    error_type: str = Query(..., description="Error type"),
    user_id: Optional[str] = Query(None, description="User ID")
) -> Dict[str, str]:
    """Test endpoint to record authentication failure (for testing/demo purposes)."""
    try:
        extension_dashboard.record_auth_failure(response_time, error_type, user_id)
        return {"message": "Authentication failure recorded"}
    except Exception as e:
        logger.error(f"Error recording auth failure: {e}")
        raise HTTPException(status_code=500, detail="Failed to record auth failure")


@monitoring_router.post("/test/service-health")
async def test_record_service_health(
    service_name: str = Query(..., description="Service name"),
    status: str = Query(..., description="Service status"),
    response_time: Optional[float] = Query(None, description="Response time in seconds")
) -> Dict[str, str]:
    """Test endpoint to record service health (for testing/demo purposes)."""
    try:
        extension_dashboard.record_service_health(service_name, status, response_time)
        return {"message": f"Service health recorded for {service_name}"}
    except Exception as e:
        logger.error(f"Error recording service health: {e}")
        raise HTTPException(status_code=500, detail="Failed to record service health")


@monitoring_router.post("/test/api-request")
async def test_record_api_request(
    endpoint: str = Query(..., description="API endpoint"),
    method: str = Query(..., description="HTTP method"),
    status_code: int = Query(..., description="HTTP status code"),
    response_time: float = Query(..., description="Response time in seconds")
) -> Dict[str, str]:
    """Test endpoint to record API request (for testing/demo purposes)."""
    try:
        extension_dashboard.record_api_request(endpoint, method, status_code, response_time)
        return {"message": f"API request recorded for {method} {endpoint}"}
    except Exception as e:
        logger.error(f"Error recording API request: {e}")
        raise HTTPException(status_code=500, detail="Failed to record API request")


@monitoring_router.get("/export/prometheus")
async def export_prometheus_metrics() -> str:
    """Export metrics in Prometheus format."""
    try:
        auth_metrics = extension_dashboard.metrics_collector.get_auth_metrics()
        health_metrics = extension_dashboard.metrics_collector.get_service_health_metrics()
        api_metrics = extension_dashboard.metrics_collector.get_api_performance_metrics()
        
        prometheus_output = []
        
        # Authentication metrics
        prometheus_output.append(f"# HELP extension_auth_requests_total Total authentication requests")
        prometheus_output.append(f"# TYPE extension_auth_requests_total counter")
        prometheus_output.append(f"extension_auth_requests_total {auth_metrics['total_requests']}")
        
        prometheus_output.append(f"# HELP extension_auth_success_rate Authentication success rate percentage")
        prometheus_output.append(f"# TYPE extension_auth_success_rate gauge")
        prometheus_output.append(f"extension_auth_success_rate {auth_metrics['success_rate']}")
        
        prometheus_output.append(f"# HELP extension_auth_response_time_avg Average authentication response time")
        prometheus_output.append(f"# TYPE extension_auth_response_time_avg gauge")
        prometheus_output.append(f"extension_auth_response_time_avg {auth_metrics['average_response_time']}")
        
        # Service health metrics
        prometheus_output.append(f"# HELP extension_service_health_percentage Service health percentage")
        prometheus_output.append(f"# TYPE extension_service_health_percentage gauge")
        prometheus_output.append(f"extension_service_health_percentage {health_metrics['health_percentage']}")
        
        # API performance metrics
        prometheus_output.append(f"# HELP extension_api_requests_total Total API requests")
        prometheus_output.append(f"# TYPE extension_api_requests_total counter")
        prometheus_output.append(f"extension_api_requests_total {api_metrics['total_requests']}")
        
        prometheus_output.append(f"# HELP extension_api_error_rate API error rate percentage")
        prometheus_output.append(f"# TYPE extension_api_error_rate gauge")
        prometheus_output.append(f"extension_api_error_rate {api_metrics['error_rate']}")
        
        prometheus_output.append(f"# HELP extension_api_response_time_avg Average API response time")
        prometheus_output.append(f"# TYPE extension_api_response_time_avg gauge")
        prometheus_output.append(f"extension_api_response_time_avg {api_metrics['average_response_time']}")
        
        return "\n".join(prometheus_output)
        
    except Exception as e:
        logger.error(f"Error exporting Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export Prometheus metrics")


# Middleware to automatically record API metrics
class MonitoringMiddleware:
    """Middleware to automatically record API request metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Record request start time
            start_time = datetime.utcnow()
            
            # Process request
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # Calculate response time
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds()
                    
                    # Extract request info
                    method = scope.get("method", "UNKNOWN")
                    path = scope.get("path", "/unknown")
                    status_code = message.get("status", 500)
                    
                    # Record metrics for extension API endpoints
                    if path.startswith("/api/extensions") or path.startswith("/api/monitoring"):
                        extension_dashboard.record_api_request(path, method, status_code, response_time)
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)