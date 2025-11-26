"""
Error Aggregation and Analysis Service

Aggregates errors from structured logs, provides analysis and dashboard data
for production error monitoring and troubleshooting.

Requirements: 1.2, 8.5
"""

import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from ai_karen_engine.core.logging import get_logger
from src.services.structured_logging_service import LogLevel, LogCategory

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorPattern(str, Enum):
    """Common error patterns"""
    AUTHENTICATION_FAILURE = "authentication_failure"
    DATABASE_CONNECTION = "database_connection"
    LLM_TIMEOUT = "llm_timeout"
    RESPONSE_FORMATTING = "response_formatting"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_RESOURCE = "system_resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorOccurrence:
    """Individual error occurrence"""
    timestamp: datetime
    correlation_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    service: str
    component: Optional[str]
    operation: Optional[str]
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorSummary:
    """Aggregated error summary"""
    error_type: str
    error_pattern: ErrorPattern
    severity: ErrorSeverity
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    affected_users: Set[str] = field(default_factory=set)
    affected_services: Set[str] = field(default_factory=set)
    common_metadata: Dict[str, Any] = field(default_factory=dict)
    sample_stack_trace: Optional[str] = None
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class ErrorTrend:
    """Error trend analysis"""
    time_period: str
    error_counts: Dict[str, int] = field(default_factory=dict)
    severity_distribution: Dict[ErrorSeverity, int] = field(default_factory=dict)
    pattern_distribution: Dict[ErrorPattern, int] = field(default_factory=dict)
    top_errors: List[Tuple[str, int]] = field(default_factory=list)


class ErrorAggregationService:
    """
    Service for aggregating and analyzing errors from structured logs.
    """

    def __init__(self, max_errors: int = 10000, retention_hours: int = 168):  # 7 days
        self.max_errors = max_errors
        self.retention_hours = retention_hours
        
        # Error storage
        self.error_occurrences: deque = deque(maxlen=max_errors)
        self.error_summaries: Dict[str, ErrorSummary] = {}
        
        # Analysis data
        self.hourly_trends: Dict[str, ErrorTrend] = {}
        self.daily_trends: Dict[str, ErrorTrend] = {}
        
        # Pattern recognition
        self.error_patterns = self._initialize_error_patterns()
        
        # Last cleanup time
        self._last_cleanup = datetime.utcnow()

    def _initialize_error_patterns(self) -> Dict[str, ErrorPattern]:
        """Initialize error pattern recognition rules"""
        return {
            # Authentication patterns
            "AuthenticationError": ErrorPattern.AUTHENTICATION_FAILURE,
            "InvalidTokenError": ErrorPattern.AUTHENTICATION_FAILURE,
            "PermissionError": ErrorPattern.PERMISSION_DENIED,
            "Forbidden": ErrorPattern.PERMISSION_DENIED,
            "Unauthorized": ErrorPattern.AUTHENTICATION_FAILURE,
            
            # Database patterns
            "DatabaseError": ErrorPattern.DATABASE_CONNECTION,
            "ConnectionError": ErrorPattern.DATABASE_CONNECTION,
            "TimeoutError": ErrorPattern.DATABASE_CONNECTION,
            "OperationalError": ErrorPattern.DATABASE_CONNECTION,
            
            # LLM patterns
            "LLMTimeoutError": ErrorPattern.LLM_TIMEOUT,
            "ModelNotAvailableError": ErrorPattern.LLM_TIMEOUT,
            "RateLimitError": ErrorPattern.RATE_LIMIT_EXCEEDED,
            
            # Response formatting patterns
            "FormattingError": ErrorPattern.RESPONSE_FORMATTING,
            "TemplateError": ErrorPattern.RESPONSE_FORMATTING,
            
            # Validation patterns
            "ValidationError": ErrorPattern.VALIDATION_ERROR,
            "ValueError": ErrorPattern.VALIDATION_ERROR,
            "TypeError": ErrorPattern.VALIDATION_ERROR,
            
            # System resource patterns
            "MemoryError": ErrorPattern.SYSTEM_RESOURCE,
            "DiskSpaceError": ErrorPattern.SYSTEM_RESOURCE,
            "ResourceExhaustedError": ErrorPattern.SYSTEM_RESOURCE,
        }

    def record_error(
        self,
        timestamp: datetime,
        correlation_id: Optional[str],
        user_id: Optional[str],
        session_id: Optional[str],
        service: str,
        component: Optional[str],
        operation: Optional[str],
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a new error occurrence"""
        
        error_occurrence = ErrorOccurrence(
            timestamp=timestamp,
            correlation_id=correlation_id,
            user_id=user_id,
            session_id=session_id,
            service=service,
            component=component,
            operation=operation,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            metadata=metadata or {}
        )
        
        # Add to occurrences
        self.error_occurrences.append(error_occurrence)
        
        # Update error summary
        self._update_error_summary(error_occurrence)
        
        # Update trends
        self._update_trends(error_occurrence)
        
        # Cleanup old data if needed
        self._cleanup_old_data()

    def _update_error_summary(self, error: ErrorOccurrence):
        """Update aggregated error summary"""
        error_key = f"{error.service}:{error.error_type}"
        
        if error_key not in self.error_summaries:
            # Create new summary
            pattern = self._detect_error_pattern(error.error_type, error.error_message)
            severity = self._determine_error_severity(pattern, error.error_type)
            
            self.error_summaries[error_key] = ErrorSummary(
                error_type=error.error_type,
                error_pattern=pattern,
                severity=severity,
                count=1,
                first_occurrence=error.timestamp,
                last_occurrence=error.timestamp,
                affected_users={error.user_id} if error.user_id else set(),
                affected_services={error.service},
                sample_stack_trace=error.stack_trace,
                resolution_suggestions=self._get_resolution_suggestions(pattern)
            )
        else:
            # Update existing summary
            summary = self.error_summaries[error_key]
            summary.count += 1
            summary.last_occurrence = error.timestamp
            
            if error.user_id:
                summary.affected_users.add(error.user_id)
            summary.affected_services.add(error.service)
            
            # Update sample stack trace if current one is empty
            if not summary.sample_stack_trace and error.stack_trace:
                summary.sample_stack_trace = error.stack_trace

    def _detect_error_pattern(self, error_type: str, error_message: str) -> ErrorPattern:
        """Detect error pattern from error type and message"""
        
        # Check direct error type mapping
        if error_type in self.error_patterns:
            return self.error_patterns[error_type]
        
        # Check error message for patterns
        error_message_lower = error_message.lower()
        
        if any(keyword in error_message_lower for keyword in ["auth", "login", "token", "credential"]):
            return ErrorPattern.AUTHENTICATION_FAILURE
        elif any(keyword in error_message_lower for keyword in ["database", "connection", "sql"]):
            return ErrorPattern.DATABASE_CONNECTION
        elif any(keyword in error_message_lower for keyword in ["timeout", "llm", "model"]):
            return ErrorPattern.LLM_TIMEOUT
        elif any(keyword in error_message_lower for keyword in ["format", "template", "render"]):
            return ErrorPattern.RESPONSE_FORMATTING
        elif any(keyword in error_message_lower for keyword in ["permission", "forbidden", "access"]):
            return ErrorPattern.PERMISSION_DENIED
        elif any(keyword in error_message_lower for keyword in ["rate limit", "quota", "throttle"]):
            return ErrorPattern.RATE_LIMIT_EXCEEDED
        elif any(keyword in error_message_lower for keyword in ["validation", "invalid", "malformed"]):
            return ErrorPattern.VALIDATION_ERROR
        elif any(keyword in error_message_lower for keyword in ["memory", "disk", "resource"]):
            return ErrorPattern.SYSTEM_RESOURCE
        
        return ErrorPattern.UNKNOWN

    def _determine_error_severity(self, pattern: ErrorPattern, error_type: str) -> ErrorSeverity:
        """Determine error severity based on pattern and type"""
        
        # Critical patterns
        if pattern in [ErrorPattern.DATABASE_CONNECTION, ErrorPattern.SYSTEM_RESOURCE]:
            return ErrorSeverity.CRITICAL
        
        # High severity patterns
        if pattern in [ErrorPattern.AUTHENTICATION_FAILURE, ErrorPattern.LLM_TIMEOUT]:
            return ErrorSeverity.HIGH
        
        # Medium severity patterns
        if pattern in [ErrorPattern.PERMISSION_DENIED, ErrorPattern.RATE_LIMIT_EXCEEDED]:
            return ErrorSeverity.MEDIUM
        
        # Low severity patterns
        if pattern in [ErrorPattern.VALIDATION_ERROR, ErrorPattern.RESPONSE_FORMATTING]:
            return ErrorSeverity.LOW
        
        # Default based on error type
        if "Error" in error_type and error_type not in ["ValueError", "TypeError"]:
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW

    def _get_resolution_suggestions(self, pattern: ErrorPattern) -> List[str]:
        """Get resolution suggestions for error pattern"""
        suggestions = {
            ErrorPattern.AUTHENTICATION_FAILURE: [
                "Check authentication service status",
                "Verify JWT token configuration",
                "Review user credentials and permissions",
                "Check for expired tokens or sessions"
            ],
            ErrorPattern.DATABASE_CONNECTION: [
                "Check database server status",
                "Verify connection pool configuration",
                "Review database connection strings",
                "Check network connectivity to database"
            ],
            ErrorPattern.LLM_TIMEOUT: [
                "Check LLM provider status",
                "Review timeout configurations",
                "Implement fallback mechanisms",
                "Monitor LLM provider rate limits"
            ],
            ErrorPattern.RESPONSE_FORMATTING: [
                "Check response formatter implementations",
                "Verify template configurations",
                "Review content type detection logic",
                "Test fallback formatting mechanisms"
            ],
            ErrorPattern.PERMISSION_DENIED: [
                "Review user role assignments",
                "Check RBAC configuration",
                "Verify resource permissions",
                "Audit access control policies"
            ],
            ErrorPattern.RATE_LIMIT_EXCEEDED: [
                "Review rate limiting configuration",
                "Implement request queuing",
                "Check for unusual traffic patterns",
                "Consider scaling resources"
            ],
            ErrorPattern.VALIDATION_ERROR: [
                "Review input validation rules",
                "Check data format requirements",
                "Verify API request schemas",
                "Update validation error messages"
            ],
            ErrorPattern.SYSTEM_RESOURCE: [
                "Monitor system resource usage",
                "Check memory and disk space",
                "Review resource allocation",
                "Consider scaling infrastructure"
            ],
            ErrorPattern.UNKNOWN: [
                "Review error logs for patterns",
                "Check system health status",
                "Verify service configurations",
                "Contact support if issue persists"
            ]
        }
        
        return suggestions.get(pattern, [])

    def _update_trends(self, error: ErrorOccurrence):
        """Update error trend analysis"""
        
        # Update hourly trends
        hour_key = error.timestamp.strftime("%Y-%m-%d-%H")
        if hour_key not in self.hourly_trends:
            self.hourly_trends[hour_key] = ErrorTrend(time_period=hour_key)
        
        trend = self.hourly_trends[hour_key]
        trend.error_counts[error.error_type] = trend.error_counts.get(error.error_type, 0) + 1
        
        pattern = self._detect_error_pattern(error.error_type, error.error_message)
        severity = self._determine_error_severity(pattern, error.error_type)
        
        trend.pattern_distribution[pattern] = trend.pattern_distribution.get(pattern, 0) + 1
        trend.severity_distribution[severity] = trend.severity_distribution.get(severity, 0) + 1
        
        # Update daily trends
        day_key = error.timestamp.strftime("%Y-%m-%d")
        if day_key not in self.daily_trends:
            self.daily_trends[day_key] = ErrorTrend(time_period=day_key)
        
        daily_trend = self.daily_trends[day_key]
        daily_trend.error_counts[error.error_type] = daily_trend.error_counts.get(error.error_type, 0) + 1
        daily_trend.pattern_distribution[pattern] = daily_trend.pattern_distribution.get(pattern, 0) + 1
        daily_trend.severity_distribution[severity] = daily_trend.severity_distribution.get(severity, 0) + 1

    def _cleanup_old_data(self):
        """Clean up old error data based on retention policy"""
        now = datetime.utcnow()
        
        # Only cleanup every hour
        if (now - self._last_cleanup).total_seconds() < 3600:
            return
        
        cutoff_time = now - timedelta(hours=self.retention_hours)
        
        # Clean up error occurrences
        self.error_occurrences = deque(
            [error for error in self.error_occurrences if error.timestamp > cutoff_time],
            maxlen=self.max_errors
        )
        
        # Clean up trends
        cutoff_hour = cutoff_time.strftime("%Y-%m-%d-%H")
        cutoff_day = cutoff_time.strftime("%Y-%m-%d")
        
        self.hourly_trends = {
            k: v for k, v in self.hourly_trends.items() if k > cutoff_hour
        }
        
        self.daily_trends = {
            k: v for k, v in self.daily_trends.items() if k > cutoff_day
        }
        
        self._last_cleanup = now

    def get_error_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive error dashboard data"""
        now = datetime.utcnow()
        
        # Calculate time ranges
        last_hour = now - timedelta(hours=1)
        last_24_hours = now - timedelta(hours=24)
        last_7_days = now - timedelta(days=7)
        
        # Get recent errors
        recent_errors = [
            error for error in self.error_occurrences
            if error.timestamp > last_24_hours
        ]
        
        # Calculate error rates
        errors_last_hour = len([e for e in recent_errors if e.timestamp > last_hour])
        errors_last_24h = len(recent_errors)
        
        # Get top error types
        error_type_counts = defaultdict(int)
        for error in recent_errors:
            error_type_counts[error.error_type] += 1
        
        top_errors = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get severity distribution
        severity_counts = defaultdict(int)
        for summary in self.error_summaries.values():
            severity_counts[summary.severity] += summary.count
        
        # Get pattern distribution
        pattern_counts = defaultdict(int)
        for summary in self.error_summaries.values():
            pattern_counts[summary.error_pattern] += summary.count
        
        # Get affected services
        affected_services = set()
        for error in recent_errors:
            affected_services.add(error.service)
        
        return {
            "timestamp": now.isoformat(),
            "summary": {
                "total_errors": len(self.error_occurrences),
                "errors_last_hour": errors_last_hour,
                "errors_last_24h": errors_last_24h,
                "unique_error_types": len(self.error_summaries),
                "affected_services": len(affected_services),
            },
            "top_errors": top_errors,
            "severity_distribution": dict(severity_counts),
            "pattern_distribution": {k.value: v for k, v in pattern_counts.items()},
            "recent_critical_errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "service": error.service,
                    "error_type": error.error_type,
                    "error_message": error.error_message[:200],
                    "user_id": error.user_id,
                }
                for error in recent_errors
                if self._determine_error_severity(
                    self._detect_error_pattern(error.error_type, error.error_message),
                    error.error_type
                ) == ErrorSeverity.CRITICAL
            ][:10],
            "trends": {
                "hourly": {k: dict(v.error_counts) for k, v in self.hourly_trends.items()},
                "daily": {k: dict(v.error_counts) for k, v in self.daily_trends.items()},
            }
        }

    def get_error_details(self, error_type: str, service: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific error type"""
        error_key = f"{service}:{error_type}"
        
        if error_key not in self.error_summaries:
            return None
        
        summary = self.error_summaries[error_key]
        
        # Get recent occurrences
        recent_occurrences = [
            {
                "timestamp": error.timestamp.isoformat(),
                "correlation_id": error.correlation_id,
                "user_id": error.user_id,
                "operation": error.operation,
                "error_message": error.error_message,
                "metadata": error.metadata,
            }
            for error in self.error_occurrences
            if error.error_type == error_type and error.service == service
        ][-20:]  # Last 20 occurrences
        
        return {
            "error_type": summary.error_type,
            "error_pattern": summary.error_pattern.value,
            "severity": summary.severity.value,
            "count": summary.count,
            "first_occurrence": summary.first_occurrence.isoformat(),
            "last_occurrence": summary.last_occurrence.isoformat(),
            "affected_users": len(summary.affected_users),
            "affected_services": list(summary.affected_services),
            "resolution_suggestions": summary.resolution_suggestions,
            "sample_stack_trace": summary.sample_stack_trace,
            "recent_occurrences": recent_occurrences,
        }

    def search_errors(
        self,
        query: Optional[str] = None,
        service: Optional[str] = None,
        error_type: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        pattern: Optional[ErrorPattern] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search errors with various filters"""
        
        filtered_errors = []
        
        for error in self.error_occurrences:
            # Apply filters
            if service and error.service != service:
                continue
            if error_type and error.error_type != error_type:
                continue
            if start_time and error.timestamp < start_time:
                continue
            if end_time and error.timestamp > end_time:
                continue
            if query and query.lower() not in error.error_message.lower():
                continue
            
            # Check severity and pattern filters
            if severity or pattern:
                detected_pattern = self._detect_error_pattern(error.error_type, error.error_message)
                detected_severity = self._determine_error_severity(detected_pattern, error.error_type)
                
                if severity and detected_severity != severity:
                    continue
                if pattern and detected_pattern != pattern:
                    continue
            
            filtered_errors.append({
                "timestamp": error.timestamp.isoformat(),
                "correlation_id": error.correlation_id,
                "user_id": error.user_id,
                "service": error.service,
                "component": error.component,
                "operation": error.operation,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "metadata": error.metadata,
            })
            
            if len(filtered_errors) >= limit:
                break
        
        return filtered_errors


# Global instance
_error_aggregation_service: Optional[ErrorAggregationService] = None


def get_error_aggregation_service() -> ErrorAggregationService:
    """Get global error aggregation service instance"""
    global _error_aggregation_service
    if _error_aggregation_service is None:
        _error_aggregation_service = ErrorAggregationService()
    return _error_aggregation_service