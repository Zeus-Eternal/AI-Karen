"""
Extension Monitoring System Usage Example

This module demonstrates how to integrate the error logging and monitoring system
with existing extension authentication and recovery systems.

Requirements demonstrated:
- 10.1: Extension error alerts with relevant details
- 10.2: Metrics collection on response times, error rates, and availability
- 10.3: Authentication issue escalation and alerting
- 10.4: Performance degradation recommendations
- 10.5: Historical data for trend analysis and capacity planning
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends

from .extension_monitoring_integration import (
    extension_monitoring, monitor_extension_endpoint, monitor_recovery_operation
)
from .extension_error_logging import ErrorCategory, ErrorSeverity
from .extension_alerting_system import extension_alert_manager

logger = logging.getLogger(__name__)

# Example: Enhanced extension API endpoint with monitoring
@monitor_extension_endpoint(
    endpoint_name="list_extensions",
    extension_name="extension_manager"
)
async def list_extensions_with_monitoring(
    user_context: Dict[str, Any] = None,
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Example of extension API endpoint with comprehensive monitoring.
    
    This demonstrates how to integrate monitoring with existing extension endpoints
    to track errors, performance, and recovery attempts.
    """
    
    try:
        # Simulate extension listing logic
        extensions = await _get_extensions_from_manager(user_context)
        
        return {
            'success': True,
            'extensions': extensions,
            'total': len(extensions),
            'correlation_id': correlation_id
        }
        
    except HTTPException as e:
        # HTTP exceptions are automatically logged by the monitoring decorator
        # but we can add additional context
        if e.status_code == 403:
            await extension_monitoring.log_authentication_error(
                error_message=f"Authentication failed for extension listing: {e.detail}",
                user_id=user_context.get('user_id') if user_context else None,
                tenant_id=user_context.get('tenant_id') if user_context else None,
                endpoint="/api/extensions/",
                context={
                    'status_code': e.status_code,
                    'detail': e.detail,
                    'headers': dict(e.headers) if e.headers else {}
                }
            )
        raise
        
    except Exception as e:
        # Other exceptions are also automatically logged, but we can add context
        logger.error(f"Unexpected error in list_extensions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _get_extensions_from_manager(user_context: Dict[str, Any]) -> list:
    """Simulate getting extensions from extension manager."""
    # This would normally call the actual extension manager
    return [
        {
            'name': 'test_extension',
            'version': '1.0.0',
            'status': 'active',
            'capabilities': ['read', 'write']
        }
    ]

# Example: Extension authentication with recovery monitoring
async def authenticate_extension_request_with_monitoring(
    token: str,
    endpoint: str,
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Example of extension authentication with recovery monitoring.
    
    This demonstrates how to integrate monitoring with authentication
    and recovery mechanisms.
    """
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Attempt authentication
            user_context = await _validate_extension_token(token)
            
            # Log successful authentication
            logger.info(f"Extension authentication successful for {endpoint}")
            
            return user_context
            
        except HTTPException as e:
            if e.status_code == 403 and retry_count < max_retries - 1:
                # Authentication failed - attempt recovery
                retry_count += 1
                
                async with monitor_recovery_operation(
                    recovery_strategy="token_refresh",
                    correlation_id=correlation_id
                ) as recovery_correlation_id:
                    
                    logger.info(f"Attempting token refresh (attempt {retry_count})")
                    
                    # Simulate token refresh
                    refreshed_token = await _attempt_token_refresh(token)
                    
                    if refreshed_token:
                        token = refreshed_token
                        logger.info("Token refresh successful, retrying authentication")
                        continue
                    else:
                        raise Exception("Token refresh failed")
            else:
                # Log authentication failure
                await extension_monitoring.log_authentication_error(
                    error_message=f"Authentication failed after {retry_count + 1} attempts: {e.detail}",
                    endpoint=endpoint,
                    context={
                        'status_code': e.status_code,
                        'retry_count': retry_count,
                        'max_retries': max_retries
                    }
                )
                raise
                
        except Exception as e:
            # Log unexpected error
            logger.error(f"Unexpected authentication error: {e}")
            await extension_monitoring.log_authentication_error(
                error_message=f"Unexpected authentication error: {str(e)}",
                endpoint=endpoint,
                context={
                    'error_type': type(e).__name__,
                    'retry_count': retry_count
                }
            )
            raise HTTPException(status_code=500, detail="Authentication service error")
    
    # If we get here, all retries failed
    raise HTTPException(status_code=403, detail="Authentication failed after all retries")

async def _validate_extension_token(token: str) -> Dict[str, Any]:
    """Simulate token validation."""
    # This would normally validate the JWT token
    if token == "invalid_token":
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {
        'user_id': 'test_user',
        'tenant_id': 'test_tenant',
        'roles': ['user'],
        'permissions': ['extension:read']
    }

async def _attempt_token_refresh(old_token: str) -> Optional[str]:
    """Simulate token refresh attempt."""
    # This would normally call the auth service to refresh the token
    if old_token == "expired_token":
        return "new_valid_token"
    return None

# Example: Service health monitoring with recovery
async def monitor_extension_service_health():
    """
    Example of service health monitoring with automatic recovery.
    
    This demonstrates how to monitor extension service health and
    trigger recovery when issues are detected.
    """
    
    try:
        # Check extension service health
        health_status = await _check_extension_service_health()
        
        if not health_status['healthy']:
            # Log service unavailable
            await extension_monitoring.log_service_unavailable(
                service_name="extension_service",
                error_message=f"Service health check failed: {health_status['error']}",
                context=health_status
            )
            
            # Attempt service recovery
            async with monitor_recovery_operation(
                recovery_strategy="service_restart"
            ) as correlation_id:
                
                logger.info("Attempting extension service recovery")
                
                # Simulate service restart
                recovery_success = await _attempt_service_recovery()
                
                if recovery_success:
                    logger.info("Extension service recovery successful")
                else:
                    raise Exception("Service recovery failed")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Extension service health monitoring failed: {e}")
        raise

async def _check_extension_service_health() -> Dict[str, Any]:
    """Simulate extension service health check."""
    # This would normally check the actual service health
    return {
        'healthy': True,
        'response_time': 150,
        'last_check': datetime.utcnow().isoformat()
    }

async def _attempt_service_recovery() -> bool:
    """Simulate service recovery attempt."""
    # This would normally attempt to restart or recover the service
    return True

# Example: Performance monitoring and recommendations
async def get_extension_performance_insights() -> Dict[str, Any]:
    """
    Example of getting performance insights and recommendations.
    
    This demonstrates how to use the monitoring system to get
    performance data and improvement recommendations.
    """
    
    try:
        # Get comprehensive monitoring data
        dashboard_data = await extension_monitoring.get_monitoring_dashboard_data()
        
        # Extract key performance metrics
        metrics = dashboard_data['metrics']
        recommendations = dashboard_data['recommendations']
        system_health = dashboard_data['system_health']
        
        # Generate performance insights
        insights = {
            'overall_health': system_health,
            'key_metrics': {
                'error_rate': sum(metrics['error_rates'].values()),
                'avg_response_time': metrics['response_stats']['avg'],
                'availability': sum(metrics['availability_stats'].values()) / len(metrics['availability_stats']) if metrics['availability_stats'] else 1.0,
                'recovery_success_rate': sum(metrics['recovery_rates'].values()) / len(metrics['recovery_rates']) if metrics['recovery_rates'] else 1.0
            },
            'recommendations': recommendations,
            'alerts': {
                'active_count': len(dashboard_data['alerts']['active']),
                'critical_alerts': [
                    alert for alert in dashboard_data['alerts']['active']
                    if alert.get('severity') == 'critical'
                ]
            }
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get performance insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance insights")

# Example: Alert management
async def manage_extension_alerts():
    """
    Example of managing extension alerts.
    
    This demonstrates how to work with the alerting system to
    acknowledge and resolve alerts.
    """
    
    try:
        # Get active alerts
        active_alerts = extension_alert_manager.get_active_alerts()
        
        logger.info(f"Found {len(active_alerts)} active alerts")
        
        # Process each alert
        for alert in active_alerts:
            logger.info(f"Processing alert: {alert.alert_id} - {alert.message}")
            
            # Example: Auto-acknowledge low severity alerts
            if alert.severity == ErrorSeverity.LOW:
                success = extension_alert_manager.acknowledge_alert(
                    alert.alert_id,
                    acknowledged_by="auto_system"
                )
                if success:
                    logger.info(f"Auto-acknowledged low severity alert: {alert.alert_id}")
            
            # Example: Auto-resolve alerts for resolved issues
            if alert.alert_type == "service_unavailable":
                # Check if service is now available
                service_healthy = await _check_extension_service_health()
                if service_healthy['healthy']:
                    success = extension_alert_manager.resolve_alert(
                        alert.alert_id,
                        resolved_by="auto_system"
                    )
                    if success:
                        logger.info(f"Auto-resolved service unavailable alert: {alert.alert_id}")
        
        return {
            'processed_alerts': len(active_alerts),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to manage alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to manage alerts")

# Example: Custom monitoring integration
class CustomExtensionMonitor:
    """
    Example of custom monitoring integration for specific extension needs.
    
    This demonstrates how to extend the monitoring system for
    application-specific requirements.
    """
    
    def __init__(self):
        self.custom_metrics = {}
    
    async def monitor_custom_operation(
        self,
        operation_name: str,
        user_context: Dict[str, Any] = None
    ):
        """Monitor a custom extension operation."""
        
        async with extension_monitoring.monitor_request(
            endpoint=f"/custom/{operation_name}",
            user_id=user_context.get('user_id') if user_context else None,
            tenant_id=user_context.get('tenant_id') if user_context else None,
            extension_name="custom_extension"
        ) as correlation_id:
            
            try:
                # Perform custom operation
                result = await self._perform_custom_operation(operation_name)
                
                # Record custom metrics
                self.custom_metrics[operation_name] = {
                    'last_success': datetime.utcnow(),
                    'correlation_id': correlation_id
                }
                
                return result
                
            except Exception as e:
                # Log custom error with additional context
                await extension_monitoring.log_authentication_error(
                    error_message=f"Custom operation {operation_name} failed: {str(e)}",
                    user_id=user_context.get('user_id') if user_context else None,
                    tenant_id=user_context.get('tenant_id') if user_context else None,
                    endpoint=f"/custom/{operation_name}",
                    context={
                        'operation_name': operation_name,
                        'custom_metrics': self.custom_metrics.get(operation_name, {})
                    }
                )
                raise
    
    async def _perform_custom_operation(self, operation_name: str):
        """Simulate custom operation."""
        if operation_name == "fail_operation":
            raise Exception("Simulated failure")
        
        return {'success': True, 'operation': operation_name}

# Example usage in a FastAPI endpoint
async def example_monitored_endpoint():
    """Example of how to use monitoring in a FastAPI endpoint."""
    
    # Initialize custom monitor
    custom_monitor = CustomExtensionMonitor()
    
    # Monitor custom operation
    result = await custom_monitor.monitor_custom_operation(
        operation_name="test_operation",
        user_context={'user_id': 'test_user', 'tenant_id': 'test_tenant'}
    )
    
    # Get performance insights
    insights = await get_extension_performance_insights()
    
    # Manage alerts
    alert_status = await manage_extension_alerts()
    
    return {
        'operation_result': result,
        'performance_insights': insights,
        'alert_status': alert_status
    }

if __name__ == "__main__":
    # Example of running monitoring operations
    asyncio.run(example_monitored_endpoint())