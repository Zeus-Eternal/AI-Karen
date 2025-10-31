"""
Error Dashboard API Routes

Provides REST API endpoints for error aggregation dashboard, error analysis,
and troubleshooting information.

Requirements: 1.2, 8.5
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.error_aggregation_service import (
    get_error_aggregation_service,
    ErrorSeverity,
    ErrorPattern,
)
from ai_karen_engine.services.auth.auth_service import get_current_user

logger = get_logger(__name__)

# Create router
error_dashboard_router = APIRouter(
    prefix="/api/errors",
    tags=["error-dashboard"],
)


class ErrorSearchRequest(BaseModel):
    """Request model for error search"""
    query: Optional[str] = None
    service: Optional[str] = None
    error_type: Optional[str] = None
    severity: Optional[str] = None
    pattern: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100


@error_dashboard_router.get("/dashboard")
async def get_error_dashboard(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive error dashboard data.
    
    Returns:
        Dict containing error dashboard information
    """
    try:
        error_service = get_error_aggregation_service()
        return error_service.get_error_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting error dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error dashboard")


@error_dashboard_router.get("/summary")
async def get_error_summary(
    hours: int = Query(24, description="Hours to look back for summary"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get error summary for specified time period.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        Dict containing error summary
    """
    try:
        error_service = get_error_aggregation_service()
        dashboard_data = error_service.get_error_dashboard_data()
        
        # Extract summary for specified time period
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=hours)
        
        # Filter recent errors
        recent_errors = [
            error for error in error_service.error_occurrences
            if error.timestamp > cutoff_time
        ]
        
        # Calculate metrics
        total_errors = len(recent_errors)
        unique_error_types = len(set(error.error_type for error in recent_errors))
        affected_users = len(set(error.user_id for error in recent_errors if error.user_id))
        affected_services = len(set(error.service for error in recent_errors))
        
        return {
            "time_period_hours": hours,
            "total_errors": total_errors,
            "unique_error_types": unique_error_types,
            "affected_users": affected_users,
            "affected_services": affected_services,
            "error_rate_per_hour": total_errors / max(1, hours),
            "top_error_types": dashboard_data["top_errors"][:5],
            "severity_distribution": dashboard_data["severity_distribution"],
            "pattern_distribution": dashboard_data["pattern_distribution"],
        }
    except Exception as e:
        logger.error(f"Error getting error summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error summary")


@error_dashboard_router.get("/details/{service}/{error_type}")
async def get_error_details(
    service: str,
    error_type: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific error type.
    
    Args:
        service: Service name
        error_type: Error type
        
    Returns:
        Dict containing detailed error information
    """
    try:
        error_service = get_error_aggregation_service()
        details = error_service.get_error_details(error_type, service)
        
        if not details:
            raise HTTPException(
                status_code=404,
                detail=f"Error type '{error_type}' not found for service '{service}'"
            )
        
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting error details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error details")


@error_dashboard_router.post("/search")
async def search_errors(
    request: ErrorSearchRequest,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Search errors with various filters.
    
    Args:
        request: Error search request with filters
        
    Returns:
        List of matching errors
    """
    try:
        error_service = get_error_aggregation_service()
        
        # Convert string enums to enum objects
        severity = None
        if request.severity:
            try:
                severity = ErrorSeverity(request.severity.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {request.severity}")
        
        pattern = None
        if request.pattern:
            try:
                pattern = ErrorPattern(request.pattern.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid pattern: {request.pattern}")
        
        results = error_service.search_errors(
            query=request.query,
            service=request.service,
            error_type=request.error_type,
            severity=severity,
            pattern=pattern,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit
        )
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching errors: {e}")
        raise HTTPException(status_code=500, detail="Failed to search errors")


@error_dashboard_router.get("/trends")
async def get_error_trends(
    period: str = Query("hourly", description="Trend period: hourly or daily"),
    hours: int = Query(24, description="Hours to look back"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get error trends for specified period.
    
    Args:
        period: Trend period (hourly or daily)
        hours: Hours to look back
        
    Returns:
        Dict containing error trend data
    """
    try:
        if period not in ["hourly", "daily"]:
            raise HTTPException(status_code=400, detail="Period must be 'hourly' or 'daily'")
        
        error_service = get_error_aggregation_service()
        dashboard_data = error_service.get_error_dashboard_data()
        
        # Get trends for specified period
        trends = dashboard_data["trends"][period]
        
        # Filter by time range if needed
        if hours < 168:  # Less than 7 days
            now = datetime.utcnow()
            cutoff_time = now - timedelta(hours=hours)
            
            if period == "hourly":
                cutoff_key = cutoff_time.strftime("%Y-%m-%d-%H")
                trends = {k: v for k, v in trends.items() if k >= cutoff_key}
            else:  # daily
                cutoff_key = cutoff_time.strftime("%Y-%m-%d")
                trends = {k: v for k, v in trends.items() if k >= cutoff_key}
        
        return {
            "period": period,
            "hours_back": hours,
            "trends": trends,
            "total_periods": len(trends),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting error trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error trends")


@error_dashboard_router.get("/patterns")
async def get_error_patterns(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about error patterns and their descriptions.
    
    Returns:
        Dict containing error pattern information
    """
    try:
        pattern_descriptions = {
            ErrorPattern.AUTHENTICATION_FAILURE: {
                "name": "Authentication Failure",
                "description": "Errors related to user authentication, login, or token validation",
                "common_causes": [
                    "Invalid credentials",
                    "Expired tokens",
                    "Authentication service unavailable",
                    "Malformed authentication headers"
                ],
                "severity": "high"
            },
            ErrorPattern.DATABASE_CONNECTION: {
                "name": "Database Connection",
                "description": "Errors related to database connectivity and operations",
                "common_causes": [
                    "Database server unavailable",
                    "Connection pool exhausted",
                    "Network connectivity issues",
                    "Database timeout"
                ],
                "severity": "critical"
            },
            ErrorPattern.LLM_TIMEOUT: {
                "name": "LLM Timeout",
                "description": "Errors related to LLM provider timeouts and availability",
                "common_causes": [
                    "LLM provider service unavailable",
                    "Request timeout",
                    "Rate limiting",
                    "Model not available"
                ],
                "severity": "high"
            },
            ErrorPattern.RESPONSE_FORMATTING: {
                "name": "Response Formatting",
                "description": "Errors in response formatting and template rendering",
                "common_causes": [
                    "Template syntax errors",
                    "Missing template data",
                    "Formatter implementation bugs",
                    "Content type detection issues"
                ],
                "severity": "low"
            },
            ErrorPattern.PERMISSION_DENIED: {
                "name": "Permission Denied",
                "description": "Errors related to access control and permissions",
                "common_causes": [
                    "Insufficient user permissions",
                    "RBAC configuration issues",
                    "Resource access restrictions",
                    "Role assignment problems"
                ],
                "severity": "medium"
            },
            ErrorPattern.RATE_LIMIT_EXCEEDED: {
                "name": "Rate Limit Exceeded",
                "description": "Errors due to rate limiting and quota restrictions",
                "common_causes": [
                    "Too many requests from client",
                    "API quota exceeded",
                    "Provider rate limits",
                    "Unusual traffic patterns"
                ],
                "severity": "medium"
            },
            ErrorPattern.VALIDATION_ERROR: {
                "name": "Validation Error",
                "description": "Errors in input validation and data format",
                "common_causes": [
                    "Invalid input format",
                    "Missing required fields",
                    "Data type mismatches",
                    "Schema validation failures"
                ],
                "severity": "low"
            },
            ErrorPattern.SYSTEM_RESOURCE: {
                "name": "System Resource",
                "description": "Errors related to system resource exhaustion",
                "common_causes": [
                    "Out of memory",
                    "Disk space full",
                    "CPU overload",
                    "Resource allocation failures"
                ],
                "severity": "critical"
            },
            ErrorPattern.UNKNOWN: {
                "name": "Unknown",
                "description": "Errors that don't match known patterns",
                "common_causes": [
                    "New error types",
                    "Unclassified errors",
                    "System anomalies",
                    "Third-party service errors"
                ],
                "severity": "medium"
            }
        }
        
        return {
            "patterns": {
                pattern.value: {
                    **info,
                    "pattern_id": pattern.value
                }
                for pattern, info in pattern_descriptions.items()
            }
        }
    except Exception as e:
        logger.error(f"Error getting error patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error patterns")


@error_dashboard_router.get("/health")
async def get_error_system_health(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get error aggregation system health status.
    
    Returns:
        Dict containing system health information
    """
    try:
        error_service = get_error_aggregation_service()
        
        # Calculate health metrics
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        
        recent_errors = [
            error for error in error_service.error_occurrences
            if error.timestamp > last_hour
        ]
        
        critical_errors = len([
            error for error in recent_errors
            if error_service._determine_error_severity(
                error_service._detect_error_pattern(error.error_type, error.error_message),
                error.error_type
            ) == ErrorSeverity.CRITICAL
        ])
        
        # Determine overall health
        if critical_errors > 10:
            health_status = "critical"
        elif critical_errors > 5:
            health_status = "warning"
        elif len(recent_errors) > 100:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "timestamp": now.isoformat(),
            "metrics": {
                "total_errors_stored": len(error_service.error_occurrences),
                "errors_last_hour": len(recent_errors),
                "critical_errors_last_hour": critical_errors,
                "unique_error_types": len(error_service.error_summaries),
                "retention_hours": error_service.retention_hours,
                "max_errors": error_service.max_errors,
            },
            "storage_usage": {
                "current_errors": len(error_service.error_occurrences),
                "max_capacity": error_service.max_errors,
                "usage_percent": (len(error_service.error_occurrences) / error_service.max_errors) * 100,
            }
        }
    except Exception as e:
        logger.error(f"Error getting error system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")