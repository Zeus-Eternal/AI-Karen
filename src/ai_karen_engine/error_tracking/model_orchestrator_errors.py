"""
Model Orchestrator Error Tracking Integration.

This module provides comprehensive error tracking for model orchestrator operations,
integrating with existing error handling and providing structured error reporting.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

from ai_karen_engine.monitoring.model_orchestrator_tracing import TraceContext

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of model orchestrator errors."""
    NETWORK = "network"
    DISK = "disk"
    PERMISSION = "permission"
    LICENSE = "license"
    VERIFICATION = "verification"
    SCHEMA = "schema"
    COMPATIBILITY = "compatibility"
    QUOTA = "quota"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ModelError:
    """Structured error information for model operations."""
    timestamp: str
    error_id: str
    error_type: str
    error_category: str
    severity: str
    message: str
    operation: Optional[str]
    model_id: Optional[str]
    user_id: Optional[str]
    library: Optional[str]
    correlation_id: Optional[str]
    trace_id: Optional[str]
    stack_trace: Optional[str]
    context: Dict[str, Any]
    recovery_suggestions: List[str]
    is_retryable: bool
    retry_count: int = 0


class ModelOrchestratorErrorTracker:
    """
    Error tracking system for model orchestrator operations.
    
    Provides structured error logging, categorization, and recovery suggestions
    integrated with existing error handling systems.
    """
    
    def __init__(self, error_log_path: Optional[Path] = None):
        self.error_log_path = error_log_path or Path("logs/model_orchestrator_errors.log")
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Error categorization mapping
        self.error_category_map = {
            "ConnectionError": ErrorCategory.NETWORK,
            "TimeoutError": ErrorCategory.NETWORK,
            "HTTPError": ErrorCategory.NETWORK,
            "URLError": ErrorCategory.NETWORK,
            "OSError": ErrorCategory.DISK,
            "IOError": ErrorCategory.DISK,
            "PermissionError": ErrorCategory.PERMISSION,
            "FileNotFoundError": ErrorCategory.DISK,
            "DiskSpaceError": ErrorCategory.DISK,
            "LicenseError": ErrorCategory.LICENSE,
            "ValidationError": ErrorCategory.VALIDATION,
            "SchemaError": ErrorCategory.SCHEMA,
            "CompatibilityError": ErrorCategory.COMPATIBILITY,
            "QuotaExceededError": ErrorCategory.QUOTA,
            "AuthenticationError": ErrorCategory.AUTHENTICATION,
            "AuthorizationError": ErrorCategory.AUTHORIZATION,
            "ConfigurationError": ErrorCategory.CONFIGURATION,
        }
        
        # Recovery suggestions by category
        self.recovery_suggestions = {
            ErrorCategory.NETWORK: [
                "Check internet connection",
                "Verify proxy settings",
                "Try again later",
                "Use --offline mode if available"
            ],
            ErrorCategory.DISK: [
                "Check available disk space",
                "Verify file permissions",
                "Run garbage collection to free space",
                "Check disk health"
            ],
            ErrorCategory.PERMISSION: [
                "Check file/directory permissions",
                "Run with appropriate user privileges",
                "Verify access to models directory"
            ],
            ErrorCategory.LICENSE: [
                "Accept the required license",
                "Review license terms",
                "Contact administrator for license approval"
            ],
            ErrorCategory.VERIFICATION: [
                "Re-download the model",
                "Check file integrity",
                "Verify checksums"
            ],
            ErrorCategory.SCHEMA: [
                "Update registry schema",
                "Validate configuration files",
                "Check for schema version compatibility"
            ],
            ErrorCategory.COMPATIBILITY: [
                "Check system requirements",
                "Verify CPU/GPU compatibility",
                "Update system drivers"
            ],
            ErrorCategory.QUOTA: [
                "Free up storage space",
                "Request quota increase",
                "Remove unused models"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Check authentication credentials",
                "Refresh authentication tokens",
                "Verify user permissions"
            ],
            ErrorCategory.AUTHORIZATION: [
                "Check user permissions",
                "Contact administrator for access",
                "Verify role assignments"
            ],
            ErrorCategory.VALIDATION: [
                "Check input parameters",
                "Verify data format",
                "Review validation rules"
            ],
            ErrorCategory.CONFIGURATION: [
                "Check configuration files",
                "Verify settings",
                "Reset to default configuration"
            ],
            ErrorCategory.SYSTEM: [
                "Check system resources",
                "Restart the service",
                "Check system logs"
            ],
            ErrorCategory.UNKNOWN: [
                "Check logs for more details",
                "Contact support",
                "Try the operation again"
            ]
        }
        
        logger.debug(f"Error tracker initialized: {self.error_log_path}")
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its type."""
        error_type = type(error).__name__
        return self.error_category_map.get(error_type, ErrorCategory.UNKNOWN)
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on type and category."""
        # Critical errors that prevent system operation
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.DISK, ErrorCategory.PERMISSION, ErrorCategory.SYSTEM]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.NETWORK, ErrorCategory.LICENSE, ErrorCategory.QUOTA]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        return ErrorSeverity.LOW
    
    def _is_retryable(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if an error is retryable."""
        # Network errors are usually retryable
        if category == ErrorCategory.NETWORK:
            return True
        
        # Temporary disk issues might be retryable
        if category == ErrorCategory.DISK and "temporarily" in str(error).lower():
            return True
        
        # System errors might be retryable
        if category == ErrorCategory.SYSTEM:
            return True
        
        # Most other errors are not retryable
        return False
    
    def _generate_error_id(self, error: Exception, operation: str, model_id: str = None) -> str:
        """Generate a unique error ID."""
        import hashlib
        
        content = f"{type(error).__name__}:{operation}:{model_id or 'none'}:{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def track_error(
        self,
        error: Exception,
        operation: Optional[str] = None,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None,
        retry_count: int = 0
    ) -> ModelError:
        """Track an error with full context and categorization."""
        try:
            category = self._categorize_error(error)
            severity = self._determine_severity(error, category)
            is_retryable = self._is_retryable(error, category)
            error_id = self._generate_error_id(error, operation or "unknown", model_id)
            
            model_error = ModelError(
                timestamp=datetime.utcnow().isoformat() + "Z",
                error_id=error_id,
                error_type=type(error).__name__,
                error_category=category.value,
                severity=severity.value,
                message=str(error),
                operation=operation,
                model_id=model_id,
                user_id=user_id,
                library=library,
                correlation_id=trace_context.correlation_id if trace_context else None,
                trace_id=trace_context.trace_id if trace_context else None,
                stack_trace=traceback.format_exc(),
                context=context or {},
                recovery_suggestions=self.recovery_suggestions.get(category, []),
                is_retryable=is_retryable,
                retry_count=retry_count
            )
            
            # Log the error
            self._log_error(model_error)
            
            # Log to standard logger based on severity
            log_level = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(severity, logging.ERROR)
            
            logger.log(
                log_level,
                f"Model orchestrator error [{error_id}]: {error} "
                f"(operation: {operation}, model: {model_id}, "
                f"correlation_id: {trace_context.correlation_id if trace_context else 'none'})"
            )
            
            return model_error
            
        except Exception as e:
            # Fallback error tracking
            logger.error(f"Failed to track error: {e}")
            return ModelError(
                timestamp=datetime.utcnow().isoformat() + "Z",
                error_id="error-tracking-failed",
                error_type=type(error).__name__,
                error_category=ErrorCategory.UNKNOWN.value,
                severity=ErrorSeverity.MEDIUM.value,
                message=str(error),
                operation=operation,
                model_id=model_id,
                user_id=user_id,
                library=library,
                correlation_id=None,
                trace_id=None,
                stack_trace=None,
                context={},
                recovery_suggestions=["Check logs for more details"],
                is_retryable=False
            )
    
    def _log_error(self, model_error: ModelError):
        """Log error to file."""
        try:
            error_dict = asdict(model_error)
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_dict, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")
    
    def get_error_statistics(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get error statistics for the specified time period."""
        try:
            if not self.error_log_path.exists():
                return {"error": "Error log file not found"}
            
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            errors = []
            
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        error_data = json.loads(line.strip())
                        error_time = datetime.fromisoformat(
                            error_data['timestamp'].replace('Z', '+00:00')
                        ).timestamp()
                        
                        if error_time >= cutoff_time:
                            errors.append(error_data)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            # Calculate statistics
            total_errors = len(errors)
            if total_errors == 0:
                return {"total_errors": 0, "period_hours": hours}
            
            # Group by category
            by_category = {}
            by_severity = {}
            by_operation = {}
            by_error_type = {}
            retryable_count = 0
            
            for error in errors:
                category = error.get('error_category', 'unknown')
                severity = error.get('severity', 'unknown')
                operation = error.get('operation', 'unknown')
                error_type = error.get('error_type', 'unknown')
                
                by_category[category] = by_category.get(category, 0) + 1
                by_severity[severity] = by_severity.get(severity, 0) + 1
                by_operation[operation] = by_operation.get(operation, 0) + 1
                by_error_type[error_type] = by_error_type.get(error_type, 0) + 1
                
                if error.get('is_retryable', False):
                    retryable_count += 1
            
            # Find most common errors
            most_common_category = max(by_category.items(), key=lambda x: x[1])
            most_common_type = max(by_error_type.items(), key=lambda x: x[1])
            
            return {
                "total_errors": total_errors,
                "period_hours": hours,
                "retryable_errors": retryable_count,
                "retryable_percentage": (retryable_count / total_errors) * 100,
                "by_category": by_category,
                "by_severity": by_severity,
                "by_operation": by_operation,
                "by_error_type": by_error_type,
                "most_common_category": most_common_category,
                "most_common_type": most_common_type,
                "error_rate_per_hour": total_errors / hours
            }
            
        except Exception as e:
            logger.error(f"Error generating error statistics: {e}")
            return {"error": str(e)}
    
    def get_recovery_suggestions(
        self,
        error_category: str,
        error_type: str = None,
        context: Dict[str, Any] = None
    ) -> List[str]:
        """Get recovery suggestions for a specific error."""
        try:
            category = ErrorCategory(error_category)
            suggestions = self.recovery_suggestions.get(category, []).copy()
            
            # Add context-specific suggestions
            if context:
                if context.get('disk_space_low'):
                    suggestions.insert(0, "Free up disk space immediately")
                
                if context.get('network_timeout'):
                    suggestions.insert(0, "Check network connectivity and try again")
                
                if context.get('permission_denied'):
                    suggestions.insert(0, "Check file/directory permissions")
            
            return suggestions
            
        except ValueError:
            return ["Check logs for more details", "Contact support"]
    
    def should_retry(
        self,
        error: Exception,
        retry_count: int,
        max_retries: int = 3
    ) -> bool:
        """Determine if an operation should be retried."""
        if retry_count >= max_retries:
            return False
        
        category = self._categorize_error(error)
        return self._is_retryable(error, category)
    
    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get error trends over the specified number of days."""
        try:
            if not self.error_log_path.exists():
                return {"error": "Error log file not found"}
            
            cutoff_time = datetime.utcnow().timestamp() - (days * 24 * 3600)
            daily_errors = {}
            
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        error_data = json.loads(line.strip())
                        error_time = datetime.fromisoformat(
                            error_data['timestamp'].replace('Z', '+00:00')
                        )
                        
                        if error_time.timestamp() >= cutoff_time:
                            date_key = error_time.date().isoformat()
                            if date_key not in daily_errors:
                                daily_errors[date_key] = {
                                    'total': 0,
                                    'by_category': {},
                                    'by_severity': {}
                                }
                            
                            daily_errors[date_key]['total'] += 1
                            
                            category = error_data.get('error_category', 'unknown')
                            severity = error_data.get('severity', 'unknown')
                            
                            daily_errors[date_key]['by_category'][category] = \
                                daily_errors[date_key]['by_category'].get(category, 0) + 1
                            daily_errors[date_key]['by_severity'][severity] = \
                                daily_errors[date_key]['by_severity'].get(severity, 0) + 1
                    
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            return {
                "period_days": days,
                "daily_errors": daily_errors,
                "total_days_with_errors": len(daily_errors)
            }
            
        except Exception as e:
            logger.error(f"Error generating error trends: {e}")
            return {"error": str(e)}


# Global error tracker instance
_error_tracker: Optional[ModelOrchestratorErrorTracker] = None


def get_model_orchestrator_error_tracker() -> ModelOrchestratorErrorTracker:
    """Get the global model orchestrator error tracker instance."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ModelOrchestratorErrorTracker()
    return _error_tracker


def track_model_error(
    error: Exception,
    operation: Optional[str] = None,
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    library: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    trace_context: Optional[TraceContext] = None,
    retry_count: int = 0
) -> ModelError:
    """Convenience function to track a model orchestrator error."""
    tracker = get_model_orchestrator_error_tracker()
    return tracker.track_error(
        error=error,
        operation=operation,
        model_id=model_id,
        user_id=user_id,
        library=library,
        context=context,
        trace_context=trace_context,
        retry_count=retry_count
    )