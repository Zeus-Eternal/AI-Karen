"""
API Routes for Validation System Metrics

This module provides HTTP endpoints for accessing validation system metrics,
health status, and statistics for monitoring and debugging purposes.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from datetime import datetime, timedelta

from ai_karen_engine.monitoring.validation_metrics import (
    get_validation_metrics_collector,
    ValidationEventType,
    ThreatLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validation", tags=["validation-metrics"])


@router.get("/metrics/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of validation system metrics
    
    Returns:
        Dictionary containing metrics summary
    """
    try:
        collector = get_validation_metrics_collector()
        summary = collector.get_metrics_summary()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics summary")


@router.get("/health")
async def get_validation_system_health() -> Dict[str, Any]:
    """
    Get validation system health status
    
    Returns:
        Dictionary containing health status of validation components
    """
    try:
        collector = get_validation_metrics_collector()
        
        # Check if metrics collector is working
        metrics_healthy = True
        try:
            collector.get_metrics_summary()
        except Exception:
            metrics_healthy = False
        
        # Update health metrics
        collector.update_system_health("metrics_collector", metrics_healthy)
        collector.update_system_health("validation_system", True)  # Basic health check
        
        health_status = {
            "status": "healthy" if metrics_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "metrics_collector": "healthy" if metrics_healthy else "unhealthy",
                "validation_system": "healthy",
                "prometheus_integration": "healthy" if collector.metrics_manager._prometheus_available else "unavailable"
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking validation system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check system health")


@router.post("/test/security-event")
async def test_security_event(
    threat_level: str = Query("medium", description="Threat level (none, low, medium, high, critical)"),
    attack_type: str = Query("sql_injection", description="Attack type"),
    endpoint: str = Query("/api/test", description="Test endpoint"),
    method: str = Query("POST", description="HTTP method")
) -> Dict[str, Any]:
    """
    Test endpoint to generate security events for testing monitoring
    
    Args:
        threat_level: Security threat level
        attack_type: Type of attack to simulate
        endpoint: Endpoint being attacked
        method: HTTP method
        
    Returns:
        Confirmation of test event generation
    """
    try:
        collector = get_validation_metrics_collector()
        
        # Map string threat level to enum
        threat_level_map = {
            "none": ThreatLevel.NONE,
            "low": ThreatLevel.LOW,
            "medium": ThreatLevel.MEDIUM,
            "high": ThreatLevel.HIGH,
            "critical": ThreatLevel.CRITICAL
        }
        
        threat_enum = threat_level_map.get(threat_level.lower(), ThreatLevel.MEDIUM)
        
        # Generate test metrics data
        from ai_karen_engine.monitoring.validation_metrics import ValidationMetricsData
        
        test_data = ValidationMetricsData(
            event_type=ValidationEventType.SECURITY_THREAT_DETECTED,
            threat_level=threat_enum,
            validation_rule="test_rule",
            client_ip_hash="test_client_hash",
            endpoint=endpoint,
            http_method=method,
            user_agent_category="security_tool",
            processing_time_ms=50.0,
            attack_categories=[attack_type],
            additional_labels={
                "confidence_score": "0.85",
                "client_reputation": "suspicious",
                "test_event": "true"
            }
        )
        
        collector.record_validation_event(test_data)
        
        return {
            "status": "success",
            "message": "Test security event generated",
            "event_details": {
                "threat_level": threat_level,
                "attack_type": attack_type,
                "endpoint": endpoint,
                "method": method
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating test security event: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test event")


@router.post("/test/rate-limit-event")
async def test_rate_limit_event(
    rule_name: str = Query("test_rule", description="Rate limit rule name"),
    endpoint: str = Query("/api/test", description="Test endpoint"),
    scope: str = Query("ip", description="Rate limit scope")
) -> Dict[str, Any]:
    """
    Test endpoint to generate rate limit events for testing monitoring
    
    Args:
        rule_name: Name of rate limit rule
        endpoint: Endpoint being rate limited
        scope: Scope of rate limiting
        
    Returns:
        Confirmation of test event generation
    """
    try:
        collector = get_validation_metrics_collector()
        
        # Generate test rate limit event
        from ai_karen_engine.monitoring.validation_metrics import ValidationMetricsData
        
        test_data = ValidationMetricsData(
            event_type=ValidationEventType.RATE_LIMIT_EXCEEDED,
            threat_level=ThreatLevel.LOW,
            validation_rule="rate_limit_validation",
            client_ip_hash="test_client_hash",
            endpoint=endpoint,
            http_method="POST",
            user_agent_category="api_client",
            processing_time_ms=10.0,
            rate_limit_rule=rule_name,
            additional_labels={
                "rate_limit_scope": scope,
                "rate_limit_algorithm": "sliding_window",
                "current_usage_percent": "95.0",
                "reset_time_unix": str(datetime.utcnow().timestamp() + 60),
                "test_event": "true"
            }
        )
        
        collector.record_validation_event(test_data)
        
        return {
            "status": "success",
            "message": "Test rate limit event generated",
            "event_details": {
                "rule_name": rule_name,
                "endpoint": endpoint,
                "scope": scope
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating test rate limit event: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test event")


@router.get("/stats/threats")
async def get_threat_statistics(
    hours: int = Query(24, description="Number of hours to look back", ge=1, le=168)
) -> Dict[str, Any]:
    """
    Get threat statistics for the specified time period
    
    Args:
        hours: Number of hours to look back (1-168)
        
    Returns:
        Dictionary containing threat statistics
    """
    try:
        # This would typically query the metrics backend (Prometheus)
        # For now, return mock data structure
        
        return {
            "status": "success",
            "time_period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_threats_detected": 0,
                "threats_by_level": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "threats_by_category": {
                    "sql_injection": 0,
                    "xss": 0,
                    "path_traversal": 0,
                    "command_injection": 0,
                    "other": 0
                },
                "blocked_requests": 0,
                "rate_limited_requests": 0,
                "top_attacked_endpoints": [],
                "suspicious_clients": 0
            },
            "note": "This endpoint provides mock data. Integrate with Prometheus for real metrics."
        }
        
    except Exception as e:
        logger.error(f"Error getting threat statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get threat statistics")


@router.get("/config/metrics")
async def get_metrics_configuration() -> Dict[str, Any]:
    """
    Get current metrics configuration
    
    Returns:
        Dictionary containing metrics configuration
    """
    try:
        collector = get_validation_metrics_collector()
        
        config = {
            "prometheus_available": collector.metrics_manager._prometheus_available,
            "registered_metrics": collector.metrics_manager.list_registered_metrics(),
            "cache_settings": {
                "cache_ttl_seconds": 60,
                "max_cache_size": 1000
            },
            "collection_settings": {
                "endpoint_sanitization": True,
                "ip_hashing": True,
                "cardinality_limits": {
                    "max_endpoint_length": 100,
                    "max_client_hash_length": 16
                }
            }
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "configuration": config
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics configuration")


@router.post("/maintenance/cleanup")
async def cleanup_metrics_cache() -> Dict[str, Any]:
    """
    Manually trigger metrics cache cleanup
    
    Returns:
        Confirmation of cleanup operation
    """
    try:
        collector = get_validation_metrics_collector()
        
        # Force cache cleanup
        collector._maybe_clear_cache()
        
        return {
            "status": "success",
            "message": "Metrics cache cleanup completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup cache")


@router.get("/debug/metrics-list")
async def list_available_metrics() -> Dict[str, Any]:
    """
    List all available validation metrics for debugging
    
    Returns:
        List of available metrics with descriptions
    """
    try:
        metrics_info = {
            "validation_metrics": [
                {
                    "name": "http_validation_requests_total",
                    "type": "counter",
                    "description": "Total HTTP validation requests processed",
                    "labels": ["event_type", "validation_rule", "endpoint", "method", "result"]
                },
                {
                    "name": "http_validation_duration_seconds",
                    "type": "histogram",
                    "description": "Time spent on HTTP request validation",
                    "labels": ["validation_rule", "endpoint", "method"]
                },
                {
                    "name": "http_security_threats_total",
                    "type": "counter",
                    "description": "Total security threats detected",
                    "labels": ["threat_level", "attack_category", "endpoint", "method", "client_reputation"]
                },
                {
                    "name": "http_rate_limit_events_total",
                    "type": "counter",
                    "description": "Total rate limiting events",
                    "labels": ["rule_name", "scope", "algorithm", "action", "endpoint"]
                },
                {
                    "name": "http_blocked_requests_total",
                    "type": "counter",
                    "description": "Total blocked requests by reason",
                    "labels": ["block_reason", "threat_level", "endpoint", "method"]
                }
            ],
            "security_metrics": [
                {
                    "name": "http_attack_patterns_detected_total",
                    "type": "counter",
                    "description": "Total attack patterns detected by type",
                    "labels": ["pattern_type", "pattern_category", "endpoint", "method"]
                },
                {
                    "name": "http_client_reputation_score",
                    "type": "histogram",
                    "description": "Client reputation scores",
                    "labels": ["reputation_category", "endpoint"]
                },
                {
                    "name": "http_suspicious_clients_total",
                    "type": "counter",
                    "description": "Total suspicious client activities",
                    "labels": ["activity_type", "reputation", "endpoint"]
                }
            ],
            "system_metrics": [
                {
                    "name": "http_validation_system_health",
                    "type": "gauge",
                    "description": "Validation system health status",
                    "labels": ["component"]
                },
                {
                    "name": "http_validation_errors_total",
                    "type": "counter",
                    "description": "Total validation system errors",
                    "labels": ["error_type", "component", "severity"]
                },
                {
                    "name": "http_threat_intelligence_entries_total",
                    "type": "gauge",
                    "description": "Total entries in threat intelligence database",
                    "labels": ["entry_type"]
                }
            ]
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_catalog": metrics_info,
            "total_metrics": sum(len(category) for category in metrics_info.values())
        }
        
    except Exception as e:
        logger.error(f"Error listing metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to list metrics")