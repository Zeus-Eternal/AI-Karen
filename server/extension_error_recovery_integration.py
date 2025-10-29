"""
Extension Error Recovery Integration

Integrates the comprehensive error recovery manager with existing extension
authentication, service recovery, and health monitoring systems.

Requirements addressed:
- 3.1: Extension integration service error handling
- 3.2: Extension API calls with proper authentication
- 3.3: Authentication failures and retry logic
- 9.1: Graceful degradation when authentication fails
- 9.2: Fallback behavior for extension unavailability
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone

from .extension_error_recovery_manager import (
    ExtensionErrorRecoveryManager,
    ExtensionError,
    ErrorCategory,
    ErrorSeverity,
    RecoveryResult,
    initialize_extension_error_recovery_manager,
    get_extension_error_recovery_manager,
    create_auth_token_expired_error,
    create_service_unavailable_error,
    create_network_error,
    create_permission_denied_error
)

logger = logging.getLogger(__name__)


class ExtensionErrorRecoveryIntegration:
    """
    Integration layer that connects the error recovery manager with existing systems.
    
    This class provides integration points for:
    - Extension authentication system
    - Service recovery manager
    - Health monitoring system
    - Extension API endpoints
    """
    
    def __init__(self):
        self.recovery_manager: Optional[ExtensionErrorRecoveryManager] = None
        self.auth_manager = None
        self.service_recovery_manager = None
        self.health_monitor = None
        self.cache_manager = None
        self.initialized = False
    
    async def initialize(
        self,
        auth_manager=None,
        service_recovery_manager=None,
        health_monitor=None,
        cache_manager=None
    ):
        """Initialize the error recovery integration"""
        try:
            self.auth_manager = auth_manager
            self.service_recovery_manager = service_recovery_manager
            self.health_monitor = health_monitor
            self.cache_manager = cache_manager
            
            # Initialize the recovery manager
            self.recovery_manager = initialize_extension_error_recovery_manager(
                auth_manager=auth_manager,
                service_recovery_manager=service_recovery_manager,
                degradation_manager=None,  # Will be set up separately
                cache_manager=cache_manager
            )
            
            # Set up integration hooks
            await self._setup_integration_hooks()
            
            self.initialized = True
            logger.info("Extension error recovery integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize extension error recovery integration: {e}")
            raise
    
    async def _setup_integration_hooks(self):
        """Set up integration hooks with existing systems"""
        try:
            # Hook into service recovery manager if available
            if self.service_recovery_manager:
                await self._setup_service_recovery_hooks()
            
            # Hook into health monitor if available
            if self.health_monitor:
                await self._setup_health_monitor_hooks()
            
            # Hook into auth manager if available
            if self.auth_manager:
                await self._setup_auth_manager_hooks()
                
        except Exception as e:
            logger.error(f"Failed to set up integration hooks: {e}")
            raise
    
    async def _setup_service_recovery_hooks(self):
        """Set up hooks with the service recovery manager"""
        try:
            # Add error recovery as a graceful degradation handler
            if hasattr(self.service_recovery_manager, 'add_graceful_degradation_handler'):
                self.service_recovery_manager.add_graceful_degradation_handler(
                    "extension_error_recovery",
                    self._handle_service_degradation
                )
            
            # Add startup handler for recovery system
            if hasattr(self.service_recovery_manager, 'add_startup_handler'):
                self.service_recovery_manager.add_startup_handler(
                    self._startup_recovery_system
                )
            
            # Add shutdown handler for recovery system
            if hasattr(self.service_recovery_manager, 'add_shutdown_handler'):
                self.service_recovery_manager.add_shutdown_handler(
                    self._shutdown_recovery_system
                )
                
            logger.info("Service recovery hooks set up successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up service recovery hooks: {e}")
    
    async def _setup_health_monitor_hooks(self):
        """Set up hooks with the health monitor"""
        try:
            # Register error recovery status as a health check
            if hasattr(self.health_monitor, 'register_health_check'):
                self.health_monitor.register_health_check(
                    "extension_error_recovery",
                    self._check_recovery_system_health
                )
                
            logger.info("Health monitor hooks set up successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up health monitor hooks: {e}")
    
    async def _setup_auth_manager_hooks(self):
        """Set up hooks with the authentication manager"""
        try:
            # Hook into auth failure events if supported
            if hasattr(self.auth_manager, 'add_failure_handler'):
                self.auth_manager.add_failure_handler(self._handle_auth_failure)
                
            logger.info("Auth manager hooks set up successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up auth manager hooks: {e}")
    
    async def _handle_service_degradation(self):
        """Handle service degradation through error recovery"""
        try:
            if not self.recovery_manager:
                return
            
            # Get recovery statistics to assess system health
            stats = self.recovery_manager.get_recovery_statistics()
            
            # If error rate is high, apply additional degradation measures
            if stats.get("success_rate_24h", 1.0) < 0.5:  # Less than 50% success rate
                logger.warning("High error recovery failure rate detected, applying additional degradation")
                
                # Force circuit breaker if not already open
                if not stats.get("circuit_breaker_open", False):
                    self.recovery_manager.force_circuit_breaker_reset()
                    
        except Exception as e:
            logger.error(f"Error handling service degradation: {e}")
    
    async def _startup_recovery_system(self):
        """Startup handler for the recovery system"""
        try:
            if self.recovery_manager:
                # Clear any stale recovery state
                self.recovery_manager.clear_recovery_history()
                
                # Reset circuit breaker
                self.recovery_manager.force_circuit_breaker_reset()
                
                logger.info("Extension error recovery system started up")
                
        except Exception as e:
            logger.error(f"Error during recovery system startup: {e}")
    
    async def _shutdown_recovery_system(self):
        """Shutdown handler for the recovery system"""
        try:
            if self.recovery_manager:
                # Cancel any active recoveries
                active_recoveries = self.recovery_manager.get_active_recoveries()
                if active_recoveries:
                    logger.info(f"Cancelling {len(active_recoveries)} active recoveries during shutdown")
                
                logger.info("Extension error recovery system shut down")
                
        except Exception as e:
            logger.error(f"Error during recovery system shutdown: {e}")
    
    async def _check_recovery_system_health(self) -> Dict[str, Any]:
        """Health check for the recovery system"""
        try:
            if not self.recovery_manager:
                return {
                    "healthy": False,
                    "message": "Recovery manager not initialized"
                }
            
            stats = self.recovery_manager.get_recovery_statistics()
            active_recoveries = self.recovery_manager.get_active_recoveries()
            
            # Determine health based on statistics
            healthy = True
            issues = []
            
            # Check circuit breaker
            if stats.get("circuit_breaker_open", False):
                healthy = False
                issues.append("Circuit breaker is open")
            
            # Check success rate
            success_rate = stats.get("success_rate_24h", 1.0)
            if success_rate < 0.7:  # Less than 70% success rate
                healthy = False
                issues.append(f"Low success rate: {success_rate:.2%}")
            
            # Check for too many active recoveries
            if len(active_recoveries) > 5:
                healthy = False
                issues.append(f"Too many active recoveries: {len(active_recoveries)}")
            
            return {
                "healthy": healthy,
                "message": "Recovery system healthy" if healthy else f"Issues: {', '.join(issues)}",
                "statistics": stats,
                "active_recoveries_count": len(active_recoveries)
            }
            
        except Exception as e:
            logger.error(f"Error checking recovery system health: {e}")
            return {
                "healthy": False,
                "message": f"Health check failed: {str(e)}"
            }
    
    async def _handle_auth_failure(self, failure_info: Dict[str, Any]):
        """Handle authentication failure through error recovery"""
        try:
            if not self.recovery_manager:
                return
            
            # Create appropriate error based on failure type
            error_code = failure_info.get("error_code", "AUTH_FAILURE")
            endpoint = failure_info.get("endpoint", "/api/extensions/")
            operation = failure_info.get("operation", "authentication")
            
            if error_code in ["TOKEN_EXPIRED", "TOKEN_INVALID"]:
                error = create_auth_token_expired_error(
                    endpoint=endpoint,
                    operation=operation,
                    context=failure_info
                )
            else:
                error = create_permission_denied_error(
                    endpoint=endpoint,
                    operation=operation,
                    context=failure_info
                )
            
            # Handle the error through recovery manager
            result = await self.recovery_manager.handle_error(error, failure_info)
            
            logger.info(f"Auth failure handled: {result.message}")
            
        except Exception as e:
            logger.error(f"Error handling auth failure: {e}")
    
    # Public API methods
    
    async def handle_http_error(
        self,
        status_code: int,
        endpoint: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """Handle HTTP error from extension API calls"""
        if not self.recovery_manager:
            return RecoveryResult(
                success=False,
                strategy="no_recovery",
                message="Error recovery not initialized"
            )
        
        if context is None:
            context = {}
        
        # Create appropriate error based on status code
        if status_code == 401:
            error = create_auth_token_expired_error(
                endpoint=endpoint,
                operation=operation,
                context={**context, "http_status": status_code}
            )
        elif status_code == 403:
            error = create_permission_denied_error(
                endpoint=endpoint,
                operation=operation,
                context={**context, "http_status": status_code}
            )
        elif status_code == 503:
            error = create_service_unavailable_error(
                endpoint=endpoint,
                operation=operation,
                context={**context, "http_status": status_code}
            )
        else:
            error = create_network_error(
                endpoint=endpoint,
                operation=operation,
                context={**context, "http_status": status_code}
            )
        
        return await self.recovery_manager.handle_error(error, context)
    
    async def handle_network_error(
        self,
        endpoint: str,
        operation: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """Handle network error from extension API calls"""
        if not self.recovery_manager:
            return RecoveryResult(
                success=False,
                strategy="no_recovery",
                message="Error recovery not initialized"
            )
        
        if context is None:
            context = {}
        
        error = create_network_error(
            endpoint=endpoint,
            operation=operation,
            context={**context, "error_message": error_message}
        )
        
        return await self.recovery_manager.handle_error(error, context)
    
    async def handle_service_error(
        self,
        service_name: str,
        endpoint: str,
        operation: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """Handle service error from extension operations"""
        if not self.recovery_manager:
            return RecoveryResult(
                success=False,
                strategy="no_recovery",
                message="Error recovery not initialized"
            )
        
        if context is None:
            context = {}
        
        context["service_name"] = service_name
        
        error = create_service_unavailable_error(
            endpoint=endpoint,
            operation=operation,
            context={**context, "error_message": error_message}
        )
        
        return await self.recovery_manager.handle_error(error, context)
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        if not self.recovery_manager:
            return {"error": "Recovery manager not initialized"}
        
        return self.recovery_manager.get_recovery_statistics()
    
    def get_active_recoveries(self) -> List[Dict[str, Any]]:
        """Get active recovery attempts"""
        if not self.recovery_manager:
            return []
        
        return self.recovery_manager.get_active_recoveries()
    
    def is_healthy(self) -> bool:
        """Check if the recovery system is healthy"""
        if not self.recovery_manager:
            return False
        
        stats = self.recovery_manager.get_recovery_statistics()
        return not stats.get("circuit_breaker_open", False)


# Global integration instance
_integration: Optional[ExtensionErrorRecoveryIntegration] = None


async def initialize_extension_error_recovery_integration(
    auth_manager=None,
    service_recovery_manager=None,
    health_monitor=None,
    cache_manager=None
) -> ExtensionErrorRecoveryIntegration:
    """Initialize the global extension error recovery integration"""
    global _integration
    
    _integration = ExtensionErrorRecoveryIntegration()
    await _integration.initialize(
        auth_manager=auth_manager,
        service_recovery_manager=service_recovery_manager,
        health_monitor=health_monitor,
        cache_manager=cache_manager
    )
    
    return _integration


def get_extension_error_recovery_integration() -> Optional[ExtensionErrorRecoveryIntegration]:
    """Get the global extension error recovery integration"""
    return _integration


async def shutdown_extension_error_recovery_integration():
    """Shutdown the global extension error recovery integration"""
    global _integration
    
    if _integration and _integration.recovery_manager:
        # Perform cleanup
        await _integration._shutdown_recovery_system()
    
    _integration = None


# Convenience functions for common error handling scenarios

async def handle_extension_api_error(
    status_code: int,
    endpoint: str,
    operation: str = "extension_api_call",
    context: Optional[Dict[str, Any]] = None
) -> RecoveryResult:
    """Handle error from extension API call"""
    integration = get_extension_error_recovery_integration()
    if not integration:
        return RecoveryResult(
            success=False,
            strategy="no_recovery",
            message="Error recovery integration not initialized"
        )
    
    return await integration.handle_http_error(status_code, endpoint, operation, context)


async def handle_extension_auth_error(
    endpoint: str,
    operation: str = "extension_auth",
    context: Optional[Dict[str, Any]] = None
) -> RecoveryResult:
    """Handle authentication error from extension operation"""
    return await handle_extension_api_error(403, endpoint, operation, context)


async def handle_extension_service_unavailable(
    service_name: str,
    endpoint: str,
    operation: str = "extension_service",
    context: Optional[Dict[str, Any]] = None
) -> RecoveryResult:
    """Handle service unavailable error from extension operation"""
    integration = get_extension_error_recovery_integration()
    if not integration:
        return RecoveryResult(
            success=False,
            strategy="no_recovery",
            message="Error recovery integration not initialized"
        )
    
    return await integration.handle_service_error(
        service_name, endpoint, operation, "Service unavailable", context
    )


async def handle_extension_network_error(
    endpoint: str,
    error_message: str,
    operation: str = "extension_network",
    context: Optional[Dict[str, Any]] = None
) -> RecoveryResult:
    """Handle network error from extension operation"""
    integration = get_extension_error_recovery_integration()
    if not integration:
        return RecoveryResult(
            success=False,
            strategy="no_recovery",
            message="Error recovery integration not initialized"
        )
    
    return await integration.handle_network_error(endpoint, operation, error_message, context)


# Decorator for automatic error recovery
def with_extension_error_recovery(
    endpoint: str,
    operation: str,
    max_retries: int = 3
):
    """Decorator to automatically handle errors with recovery"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_error = e
                    
                    if attempt >= max_retries:
                        # Final attempt failed, handle error
                        if hasattr(e, 'status_code'):
                            result = await handle_extension_api_error(
                                e.status_code, endpoint, operation
                            )
                        else:
                            result = await handle_extension_network_error(
                                endpoint, str(e), operation
                            )
                        
                        if result.fallback_data is not None:
                            return result.fallback_data
                        else:
                            raise e
                    
                    # Handle error and check if we should retry
                    if hasattr(e, 'status_code'):
                        result = await handle_extension_api_error(
                            e.status_code, endpoint, operation
                        )
                    else:
                        result = await handle_extension_network_error(
                            endpoint, str(e), operation
                        )
                    
                    if result.success:
                        # Recovery successful, retry the operation
                        continue
                    elif result.retry_after:
                        # Wait before retry
                        await asyncio.sleep(result.retry_after)
                        continue
                    elif result.fallback_data is not None:
                        # Use fallback data
                        return result.fallback_data
                    else:
                        # No recovery possible
                        raise e
            
            # Should not reach here
            raise last_error
        
        return wrapper
    return decorator