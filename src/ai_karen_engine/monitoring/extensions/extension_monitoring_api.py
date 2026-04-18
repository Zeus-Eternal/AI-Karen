"""
Extension Monitoring API

This module provides REST API endpoints for accessing extension monitoring data,
managing alerts, and viewing system health metrics.

Requirements addressed:
- 10.1: Extension error alerts with relevant details
- 10.2: Metrics collection on response times, error rates, and availability
- 10.3: Authentication issue escalation and alerting
- 10.4: Performance degradation recommendations
- 10.5: Historical data for trend analysis and capacity planning
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from .extension_monitoring_integration import extension_monitoring
from .extension_alerting_system import extension_alert_manager
from .extension_error_logging import extension_metrics_collector, extension_trend_analyzer

logger = logging.getLogger(__name__)

# Create router for monitoring endpoints
monitoring_router = APIRouter(prefix="/api/extensions/monitoring", tags=["extension-monitoring"])

@monitoring_router.get("/dashboard")
async def get_monitoring_dashboard(
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)")
) -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data."""
    try:
        dashboard_data = await extension_monitoring.get_monitoring_dashboard_data()
        
        # Add time window specific data
        dashboard_data['time_window_hours'] = time_window_hours
        
        return {
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring dashboard")

@monitoring_router.get("/metrics/errors")
async def get_error_metrics(
    time_window_minutes: int = Query(60, ge=5, le=1440, description="Time window in minutes (5-1440)"),
    category: Optional[str] = Query(None, description="Filter by error category")
) -> Dict[str, Any]:
    """Get error rate metrics."""
    try:
        error_rates = extension_metrics_collector.get_error_rate(time_window_minutes=time_window_minutes)
        
        # Filter by category if specified
        if category:
            error_rates = {k: v for k, v in error_rates.items() if category.lower() in k.lower()}
        
        return {
            'success': True,
            'data': {
                'error_rates': error_rates,
                'total_error_rate': sum(error_rates.values()),
                'time_window_minutes': time_window_minutes,
                'category_filter': category
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting error metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error metrics")

@monitoring_router.get("/metrics/performance")
async def get_performance_metrics(
    time_window_minutes: int = Query(60, ge=5, le=1440, description="Time window in minutes (5-1440)"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint")
) -> Dict[str, Any]:
    """Get performance metrics including response times."""
    try:
        response_stats = extension_metrics_collector.get_response_time_stats(
            endpoint=endpoint,
            time_window_minutes=time_window_minutes
        )
        
        return {
            'success': True,
            'data': {
                'response_stats': response_stats,
                'time_window_minutes': time_window_minutes,
                'endpoint_filter': endpoint
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@monitoring_router.get("/metrics/availability")
async def get_availability_metrics(
    time_window_minutes: int = Query(60, ge=5, le=1440, description="Time window in minutes (5-1440)")
) -> Dict[str, Any]:
    """Get availability metrics by endpoint."""
    try:
        availability_stats = extension_metrics_collector.get_availability_stats(
            time_window_minutes=time_window_minutes
        )
        
        # Calculate overall availability
        if availability_stats:
            overall_availability = sum(availability_stats.values()) / len(availability_stats)
        else:
            overall_availability = 1.0
        
        return {
            'success': True,
            'data': {
                'availability_by_endpoint': availability_stats,
                'overall_availability': overall_availability,
                'time_window_minutes': time_window_minutes
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting availability metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get availability metrics")

@monitoring_router.get("/metrics/recovery")
async def get_recovery_metrics(
    time_window_minutes: int = Query(60, ge=5, le=1440, description="Time window in minutes (5-1440)"),
    strategy: Optional[str] = Query(None, description="Filter by recovery strategy")
) -> Dict[str, Any]:
    """Get error recovery success rate metrics."""
    try:
        recovery_rates = extension_metrics_collector.get_recovery_success_rate(
            time_window_minutes=time_window_minutes,
            strategy=strategy
        )
        
        # Calculate overall recovery rate
        if recovery_rates:
            overall_recovery_rate = sum(recovery_rates.values()) / len(recovery_rates)
        else:
            overall_recovery_rate = 0.0
        
        return {
            'success': True,
            'data': {
                'recovery_rates_by_strategy': recovery_rates,
                'overall_recovery_rate': overall_recovery_rate,
                'time_window_minutes': time_window_minutes,
                'strategy_filter': strategy
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recovery metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recovery metrics")

@monitoring_router.get("/trends/analysis")
async def get_trend_analysis(
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)"),
    bucket_size_minutes: int = Query(60, ge=15, le=240, description="Bucket size in minutes (15-240)")
) -> Dict[str, Any]:
    """Get error trend analysis over time."""
    try:
        trend_analysis = extension_trend_analyzer.analyze_error_trends(
            time_window_hours=time_window_hours,
            bucket_size_minutes=bucket_size_minutes
        )
        
        return {
            'success': True,
            'data': trend_analysis,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trend analysis")

@monitoring_router.get("/recommendations")
async def get_performance_recommendations() -> Dict[str, Any]:
    """Get performance improvement recommendations."""
    try:
        recommendations = extension_trend_analyzer.get_performance_recommendations()
        
        return {
            'success': True,
            'data': {
                'recommendations': recommendations,
                'count': len(recommendations)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@monitoring_router.get("/alerts/active")
async def get_active_alerts() -> Dict[str, Any]:
    """Get all active alerts."""
    try:
        active_alerts = extension_alert_manager.get_active_alerts()
        
        # Convert alerts to dictionaries
        alerts_data = []
        for alert in active_alerts:
            alert_dict = {
                'alert_id': alert.alert_id,
                'correlation_id': alert.correlation_id,
                'alert_type': alert.alert_type,
                'severity': alert.severity.value,
                'message': alert.message,
                'context': alert.context,
                'created_at': alert.created_at.isoformat(),
                'status': alert.status.value,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            alerts_data.append(alert_dict)
        
        return {
            'success': True,
            'data': {
                'alerts': alerts_data,
                'count': len(alerts_data)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active alerts")

@monitoring_router.get("/alerts/history")
async def get_alert_history(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)")
) -> Dict[str, Any]:
    """Get alert history for specified time period."""
    try:
        alert_history = extension_alert_manager.get_alert_history(hours=hours)
        
        # Convert alerts to dictionaries
        alerts_data = []
        for alert in alert_history:
            alert_dict = {
                'alert_id': alert.alert_id,
                'correlation_id': alert.correlation_id,
                'alert_type': alert.alert_type,
                'severity': alert.severity.value,
                'message': alert.message,
                'context': alert.context,
                'created_at': alert.created_at.isoformat(),
                'status': alert.status.value,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            alerts_data.append(alert_dict)
        
        return {
            'success': True,
            'data': {
                'alerts': alerts_data,
                'count': len(alerts_data),
                'time_window_hours': hours
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert history")

@monitoring_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: Optional[str] = Query(None, description="User acknowledging the alert")
) -> Dict[str, Any]:
    """Acknowledge an active alert."""
    try:
        success = extension_alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        
        if success:
            return {
                'success': True,
                'message': f'Alert {alert_id} acknowledged successfully',
                'acknowledged_by': acknowledged_by,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found or already acknowledged")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

@monitoring_router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: Optional[str] = Query(None, description="User resolving the alert")
) -> Dict[str, Any]:
    """Resolve an active alert."""
    try:
        success = extension_alert_manager.resolve_alert(alert_id, resolved_by)
        
        if success:
            return {
                'success': True,
                'message': f'Alert {alert_id} resolved successfully',
                'resolved_by': resolved_by,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found or already resolved")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

@monitoring_router.get("/health")
async def get_monitoring_health() -> Dict[str, Any]:
    """Get monitoring system health status."""
    try:
        # Check if monitoring components are working
        health_status = {
            'monitoring_enabled': extension_monitoring.monitoring_enabled,
            'alert_monitoring_active': extension_alert_manager.monitoring_active,
            'metrics_collector_active': True,  # Always active
            'trend_analyzer_active': True     # Always active
        }
        
        # Calculate overall health
        active_components = sum(1 for status in health_status.values() if status)
        total_components = len(health_status)
        health_percentage = (active_components / total_components) * 100
        
        overall_status = "healthy" if health_percentage == 100 else "degraded" if health_percentage >= 75 else "unhealthy"
        
        return {
            'success': True,
            'data': {
                'overall_status': overall_status,
                'health_percentage': health_percentage,
                'components': health_status,
                'active_components': active_components,
                'total_components': total_components
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring health")

@monitoring_router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """Get overall extension system status with monitoring data."""
    try:
        # Get comprehensive system status
        dashboard_data = await extension_monitoring.get_monitoring_dashboard_data()
        
        # Extract key metrics for status summary
        system_health = dashboard_data.get('system_health', {})
        active_alerts = dashboard_data.get('alerts', {}).get('active', [])
        recommendations = dashboard_data.get('recommendations', [])
        
        # Categorize alerts by severity
        alert_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for alert in active_alerts:
            severity = alert.get('severity', 'medium')
            alert_counts[severity] = alert_counts.get(severity, 0) + 1
        
        # Categorize recommendations by severity
        recommendation_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for rec in recommendations:
            severity = rec.get('severity', 'medium')
            recommendation_counts[severity] = recommendation_counts.get(severity, 0) + 1
        
        return {
            'success': True,
            'data': {
                'system_health': system_health,
                'alerts': {
                    'total_active': len(active_alerts),
                    'by_severity': alert_counts
                },
                'recommendations': {
                    'total': len(recommendations),
                    'by_severity': recommendation_counts
                },
                'last_updated': dashboard_data.get('timestamp')
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

# Export the router for integration with main FastAPI app
__all__ = ['monitoring_router']