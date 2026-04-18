"""
Extension Monitoring Integration

This module integrates the error logging and monitoring system with the existing
extension runtime authentication and recovery systems.

Requirements addressed:
- 10.1: Extension error alerts with relevant details
- 10.2: Metrics collection on response times, error rates, and availability
- 10.3: Authentication issue escalation and alerting
- 10.4: Performance degradation recommendations
- 10.5: Historical data for trend analysis and capacity planning
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from contextlib import asynccontextmanager
import traceback

from .extension_error_logging import (
    extension_error_logger, extension_metrics_collector, extension_trend_analyzer,
    ErrorEvent, ErrorCategory, ErrorSeverity
)
from .extension_alerting_system import extension_alert_manager

logger = logging.getLogger(__name__)

class ExtensionMonitoringIntegration:
    """Integrates monitoring with extension runtime operations."""

    def __init__(self):
        self.monitoring_enabled = True
        self.request_tracking: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize monitoring integration."""
        logger.info("Initializing extension monitoring integration")
        
        # Start alert monitoring
        await extension_alert_manager.start_monitoring()
        
        # Start metrics cleanup task
        asyncio.create_task(self._metrics_cleanup_task())
        
        logger.info("Extension monitoring integration initialized")

    async def shutdown(self):
        """Shutdown monitoring integration."""
        logger.info("Shutting down extension monitoring integration")
        
        # Stop alert monitoring
        await extension_alert_manager.stop_monitoring()
        
        logger.info("Extension monitoring integration shutdown complete")

    @asynccontextmanager
    async def monitor_request(
        self,
        endpoint: str,
        user_id: str = None,
        tenant_id: str = None,
        extension_name: str = None,
        correlation_id: str = None
    ):
        """Context manager for monitoring extension API requests."""
        
        if not self.monitoring_enabled:
            yield
            return
        
        start_time = time.time()
        request_id = correlation_id or extension_error_logger.get_correlation_id()
        
        # Track request start
        self.request_tracking[request_id] = {
            'endpoint': endpoint,
            'user_id': user_id,
            'tenant_id': tenant_id,
            'extension_name': extension_name,
            'start_time': start_time
        }
        
        try:
            with extension_error_logger.correlation_context_manager(request_id):
                yield request_id
                
                # Record successful request
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                extension_metrics_collector.record_success(
                    endpoint=endpoint,
                    response_time=response_time,
                    extension_name=extension_name
                )
                
                logger.debug(f"Request completed successfully: {endpoint} in {response_time:.2f}ms")
                
        except Exception as e:
            # Record error
            response_time = (time.time() - start_time) * 1000
            await self._handle_request_error(
                error=e,
                endpoint=endpoint,
                user_id=user_id,
                tenant_id=tenant_id,
                extension_name=extension_name,
                request_id=request_id,
                response_time=response_time
            )
            raise
        
        finally:
            # Clean up request tracking
            self.request_tracking.pop(request_id, None)

    async def _handle_request_error(
        self,
        error: Exception,
        endpoint: str,
        user_id: str = None,
        tenant_id: str = None,
        extension_name: str = None,
        request_id: str = None,
        response_time: float = None
    ):
        """Handle and log request errors."""
        
        # Classify error
        error_category, error_severity = self._classify_error(error)
        
        # Log structured error
        error_event = extension_error_logger.log_error(
            error_type=type(error).__name__,
            error_message=str(error),
            category=error_category,
            severity=error_severity,
            context={
                'endpoint': endpoint,
                'response_time_ms': response_time,
                'error_details': {
                    'type': type(error).__name__,
                    'message': str(error),
                    'args': error.args if hasattr(error, 'args') else None
                }
            },
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            tenant_id=tenant_id,
            extension_name=extension_name,
            endpoint=endpoint,
            request_id=request_id
        )
        
        # Record error metrics
        extension_metrics_collector.record_error(
            error_event=error_event,
            endpoint=endpoint,
            response_time=response_time
        )

    def _classify_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify error by category and severity."""
        
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Authentication errors
        if ('403' in error_message or 'forbidden' in error_message or 
            'unauthorized' in error_message or 'authentication' in error_message):
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH
        
        # Authorization errors
        if ('401' in error_message or 'permission' in error_message or 
            'access denied' in error_message):
            return ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM
        
        # Service unavailable errors
        if ('503' in error_message or 'service unavailable' in error_message or 
            'connection refused' in error_message or 'timeout' in error_message):
            return ErrorCategory.SERVICE_UNAVAILABLE, ErrorSeverity.HIGH
        
        # Network errors
        if ('network' in error_message or 'connection' in error_message or 
            'dns' in error_message or 'socket' in error_message):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        
        # Configuration errors
        if ('config' in error_message or 'setting' in error_message or 
            'environment' in error_message):
            return ErrorCategory.CONFIGURATION, ErrorSeverity.MEDIUM
        
        # Performance errors (timeouts, etc.)
        if ('timeout' in error_message or 'slow' in error_message or 
            'performance' in error_message):
            return ErrorCategory.PERFORMANCE, ErrorSeverity.MEDIUM
        
        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    async def log_authentication_error(
        self,
        error_message: str,
        user_id: str = None,
        tenant_id: str = None,
        endpoint: str = None,
        context: Dict[str, Any] = None
    ):
        """Log authentication-specific errors."""
        
        error_event = extension_error_logger.log_error(
            error_type="AuthenticationError",
            error_message=error_message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            context=context or {},
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint=endpoint
        )
        
        extension_metrics_collector.record_error(error_event, endpoint)

    async def log_service_unavailable(
        self,
        service_name: str,
        error_message: str,
        endpoint: str = None,
        context: Dict[str, Any] = None
    ):
        """Log service unavailable errors."""
        
        error_event = extension_error_logger.log_error(
            error_type="ServiceUnavailableError",
            error_message=f"Service {service_name}: {error_message}",
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.CRITICAL,
            context=context or {},
            extension_name=service_name,
            endpoint=endpoint
        )
        
        extension_metrics_collector.record_error(error_event, endpoint)

    async def log_recovery_attempt(
        self,
        correlation_id: str,
        recovery_strategy: str,
        success: bool,
        duration: float,
        details: Dict[str, Any] = None
    ):
        """Log error recovery attempts."""
        
        extension_error_logger.log_recovery_attempt(
            correlation_id=correlation_id,
            recovery_strategy=recovery_strategy,
            success=success,
            duration=duration,
            details=details
        )
        
        extension_metrics_collector.record_recovery_success(
            correlation_id=correlation_id,
            recovery_strategy=recovery_strategy,
            duration=duration,
            success=success
        )

    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring data for dashboard."""
        
        # Get current metrics
        error_rates = extension_metrics_collector.get_error_rate(time_window_minutes=60)
        response_stats = extension_metrics_collector.get_response_time_stats(time_window_minutes=60)
        availability_stats = extension_metrics_collector.get_availability_stats(time_window_minutes=60)
        recovery_rates = extension_metrics_collector.get_recovery_success_rate(time_window_minutes=60)
        
        # Get trend analysis
        trend_analysis = extension_trend_analyzer.analyze_error_trends(time_window_hours=24)
        recommendations = extension_trend_analyzer.get_performance_recommendations()
        
        # Get active alerts
        active_alerts = extension_alert_manager.get_active_alerts()
        alert_history = extension_alert_manager.get_alert_history(hours=24)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'error_rates': error_rates,
                'response_stats': response_stats,
                'availability_stats': availability_stats,
                'recovery_rates': recovery_rates
            },
            'trends': trend_analysis,
            'recommendations': recommendations,
            'alerts': {
                'active': [alert.__dict__ for alert in active_alerts],
                'history_24h': [alert.__dict__ for alert in alert_history]
            },
            'system_health': self._calculate_system_health(
                error_rates, availability_stats, recovery_rates
            )
        }

    def _calculate_system_health(
        self,
        error_rates: Dict[str, float],
        availability_stats: Dict[str, float],
        recovery_rates: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate overall system health score."""
        
        # Calculate health components
        total_error_rate = sum(error_rates.values())
        avg_availability = sum(availability_stats.values()) / len(availability_stats) if availability_stats else 1.0
        avg_recovery_rate = sum(recovery_rates.values()) / len(recovery_rates) if recovery_rates else 1.0
        
        # Calculate health score (0-100)
        error_score = max(0, 100 - (total_error_rate * 2000))  # Penalize errors heavily
        availability_score = avg_availability * 100
        recovery_score = avg_recovery_rate * 100
        
        overall_score = (error_score * 0.4 + availability_score * 0.4 + recovery_score * 0.2)
        
        # Determine health status
        if overall_score >= 95:
            status = "excellent"
        elif overall_score >= 85:
            status = "good"
        elif overall_score >= 70:
            status = "fair"
        elif overall_score >= 50:
            status = "poor"
        else:
            status = "critical"
        
        return {
            'overall_score': round(overall_score, 1),
            'status': status,
            'components': {
                'error_handling': round(error_score, 1),
                'availability': round(availability_score, 1),
                'recovery': round(recovery_score, 1)
            },
            'metrics': {
                'total_error_rate': total_error_rate,
                'avg_availability': avg_availability,
                'avg_recovery_rate': avg_recovery_rate
            }
        }

    async def _metrics_cleanup_task(self):
        """Background task to clean up old metrics."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                extension_metrics_collector.cleanup_old_metrics()
                logger.debug("Metrics cleanup completed")
            except Exception as e:
                logger.error(f"Error in metrics cleanup task: {e}")

# Global monitoring integration instance
extension_monitoring = ExtensionMonitoringIntegration()

# Decorator for monitoring extension API endpoints
def monitor_extension_endpoint(
    endpoint_name: str = None,
    extension_name: str = None
):
    """Decorator to automatically monitor extension API endpoints."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract context from function arguments
            endpoint = endpoint_name or func.__name__
            
            # Try to extract user context from kwargs
            user_id = kwargs.get('user_id')
            tenant_id = kwargs.get('tenant_id')
            
            # Try to extract from user_context if available
            user_context = kwargs.get('user_context', {})
            if isinstance(user_context, dict):
                user_id = user_id or user_context.get('user_id')
                tenant_id = tenant_id or user_context.get('tenant_id')
            
            async with extension_monitoring.monitor_request(
                endpoint=endpoint,
                user_id=user_id,
                tenant_id=tenant_id,
                extension_name=extension_name
            ) as correlation_id:
                # Add correlation_id to kwargs for downstream use
                kwargs['correlation_id'] = correlation_id
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Context manager for monitoring recovery operations
@asynccontextmanager
async def monitor_recovery_operation(
    recovery_strategy: str,
    correlation_id: str = None
):
    """Context manager for monitoring error recovery operations."""
    
    start_time = time.time()
    correlation_id = correlation_id or extension_error_logger.get_correlation_id()
    
    try:
        yield correlation_id
        
        # Record successful recovery
        duration = time.time() - start_time
        await extension_monitoring.log_recovery_attempt(
            correlation_id=correlation_id,
            recovery_strategy=recovery_strategy,
            success=True,
            duration=duration
        )
        
    except Exception as e:
        # Record failed recovery
        duration = time.time() - start_time
        await extension_monitoring.log_recovery_attempt(
            correlation_id=correlation_id,
            recovery_strategy=recovery_strategy,
            success=False,
            duration=duration,
            details={'error': str(e), 'error_type': type(e).__name__}
        )
        raise