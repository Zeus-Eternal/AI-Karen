"""
Extension Service Recovery System

This module extends existing service recovery mechanisms to include comprehensive
extension service recovery, integrating with database health monitoring, startup/shutdown
handlers, and service registry patterns.

Requirements: 2.1, 2.2, 2.3, 5.1, 5.2
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from .extension_alerting_system import (
    AlertType,
    EscalationLevel,
    extension_alert_manager,
)
from .extension_error_logging import ErrorSeverity

logger = logging.getLogger(__name__)


class RecoveryStrategy(str, Enum):
    """Recovery strategies for different types of failures"""
    RESTART_SERVICE = "restart_service"
    RELOAD_EXTENSION = "reload_extension"
    RESET_CONNECTIONS = "reset_connections"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ESCALATE_TO_ADMIN = "escalate_to_admin"
    WAIT_AND_RETRY = "wait_and_retry"


class RecoveryPriority(str, Enum):
    """Priority levels for recovery operations"""
    CRITICAL = "critical"  # Authentication, core extension services
    HIGH = "high"         # Extension APIs, background tasks
    MEDIUM = "medium"     # Extension features, non-critical services
    LOW = "low"          # Monitoring, logging, metrics


@dataclass
class RecoveryAction:
    """Represents a recovery action to be executed"""
    strategy: RecoveryStrategy
    target: str  # Service/extension name
    priority: RecoveryPriority
    max_attempts: int = 3
    current_attempts: int = 0
    backoff_seconds: float = 1.0
    timeout_seconds: float = 30.0
    recovery_function: Optional[Callable] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempt: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None


@dataclass
class ServiceRecoveryState:
    """Tracks recovery state for a service"""
    service_name: str
    service_type: str  # extension, authentication, database, etc.
    healthy: bool
    last_health_check: datetime
    failure_count: int = 0
    recovery_attempts: int = 0
    last_recovery_attempt: Optional[datetime] = None
    recovery_in_progress: bool = False
    degraded_mode: bool = False
    escalated: bool = False


class ExtensionServiceRecoveryManager:
    """
    Extension service recovery manager that integrates with existing recovery mechanisms.
    
    This manager extends the existing database health monitor recovery and startup/shutdown
    handlers to provide comprehensive extension service recovery capabilities.
    """
    
    def __init__(self, extension_manager=None, database_config=None, enhanced_health_monitor=None):
        self.extension_manager = extension_manager
        self.database_config = database_config
        self.enhanced_health_monitor = enhanced_health_monitor
        
        # Recovery state tracking
        self.service_states: Dict[str, ServiceRecoveryState] = {}
        self.recovery_queue: List[RecoveryAction] = []
        self.recovery_history: List[RecoveryAction] = []
        
        # Recovery configuration
        self.recovery_config = {
            "max_concurrent_recoveries": 3,
            "recovery_check_interval": 30,  # seconds
            "escalation_threshold": 5,  # failures before escalation
            "degradation_threshold": 3,  # failures before degraded mode
            "recovery_timeout": 300,  # 5 minutes max per recovery
            "history_retention_hours": 24
        }
        
        # Recovery task management
        self._recovery_active = False
        self._recovery_task: Optional[asyncio.Task] = None
        self._active_recoveries: Dict[str, asyncio.Task] = {}
        
        # Integration with existing systems
        self._startup_handlers: List[Callable] = []
        self._shutdown_handlers: List[Callable] = []
        self._graceful_degradation_handlers: Dict[str, Callable] = {}
    
    async def start_recovery_system(self):
        """Start the extension service recovery system"""
        self._recovery_active = True
        self._recovery_task = asyncio.create_task(self._recovery_loop())
        
        # Initialize service states
        await self._initialize_service_states()
        
        logger.info("Extension service recovery system started")
    
    async def stop_recovery_system(self):
        """Stop the extension service recovery system"""
        self._recovery_active = False
        
        # Cancel recovery task
        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass
        
        # Cancel active recoveries
        for task in self._active_recoveries.values():
            task.cancel()
        
        # Wait for active recoveries to complete
        if self._active_recoveries:
            await asyncio.gather(*self._active_recoveries.values(), return_exceptions=True)
        
        logger.info("Extension service recovery system stopped")
    
    async def _initialize_service_states(self):
        """Initialize service states for tracking"""
        # Initialize extension services
        if self.extension_manager:
            try:
                extensions = self.extension_manager.registry.get_all_extensions()
                for name, record in extensions.items():
                    self.service_states[f"extension_{name}"] = ServiceRecoveryState(
                        service_name=name,
                        service_type="extension",
                        healthy=record.status.value == "active",
                        last_health_check=datetime.now(timezone.utc)
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize extension service states: {e}")
        
        # Initialize core services
        core_services = [
            ("authentication", "authentication"),
            ("database", "database"),
            ("background_tasks", "background_tasks"),
            ("extension_api", "extension_api")
        ]
        
        for service_name, service_type in core_services:
            self.service_states[service_name] = ServiceRecoveryState(
                service_name=service_name,
                service_type=service_type,
                healthy=True,  # Will be updated by health checks
                last_health_check=datetime.now(timezone.utc)
            )
    
    async def _recovery_loop(self):
        """Main recovery loop that processes recovery actions"""
        while self._recovery_active:
            try:
                # Update service health states
                await self._update_service_health_states()
                
                # Process recovery queue
                await self._process_recovery_queue()
                
                # Check for new failures and create recovery actions
                await self._detect_and_queue_recoveries()
                
                # Clean up completed recoveries
                self._cleanup_completed_recoveries()
                
                # Clean up old history
                self._cleanup_recovery_history()
                
                await asyncio.sleep(self.recovery_config["recovery_check_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in extension service recovery loop: {e}")
                await asyncio.sleep(self.recovery_config["recovery_check_interval"])
    
    async def _update_service_health_states(self):
        """Update service health states from health monitors"""
        try:
            # Update from enhanced database health monitor
            if self.enhanced_health_monitor:
                health = await self.enhanced_health_monitor.get_current_health_with_extension_focus()
                
                # Update database service state
                if "database" in self.service_states:
                    db_healthy = health.get("extension_service_healthy", False)
                    self.service_states["database"].healthy = db_healthy
                    self.service_states["database"].last_health_check = datetime.now(timezone.utc)
                    
                    if not db_healthy:
                        self.service_states["database"].failure_count += 1
                    else:
                        self.service_states["database"].failure_count = 0
                
                # Update authentication service state
                if "authentication" in self.service_states:
                    auth_healthy = health.get("authentication_service_healthy", False)
                    self.service_states["authentication"].healthy = auth_healthy
                    self.service_states["authentication"].last_health_check = datetime.now(timezone.utc)
                    
                    if not auth_healthy:
                        self.service_states["authentication"].failure_count += 1
                    else:
                        self.service_states["authentication"].failure_count = 0
            
            # Update extension service states
            if self.extension_manager:
                try:
                    from server.extension_health_monitor import get_extension_health_monitor
                    
                    extension_monitor = get_extension_health_monitor()
                    if extension_monitor:
                        ext_health = await extension_monitor.check_extension_system_health()
                        
                        # Update individual extension states
                        for name, metrics in ext_health.extension_metrics.items():
                            service_key = f"extension_{name}"
                            if service_key in self.service_states:
                                state = self.service_states[service_key]
                                state.healthy = metrics.status.value == "healthy"
                                state.last_health_check = datetime.now(timezone.utc)
                                
                                if not state.healthy:
                                    state.failure_count += 1
                                else:
                                    state.failure_count = 0
                        
                        # Update background tasks state
                        if "background_tasks" in self.service_states:
                            bg_healthy = ext_health.background_tasks_healthy
                            self.service_states["background_tasks"].healthy = bg_healthy
                            self.service_states["background_tasks"].last_health_check = datetime.now(timezone.utc)
                            
                            if not bg_healthy:
                                self.service_states["background_tasks"].failure_count += 1
                            else:
                                self.service_states["background_tasks"].failure_count = 0
                
                except Exception as e:
                    logger.warning(f"Failed to update extension health states: {e}")
        
        except Exception as e:
            logger.error(f"Failed to update service health states: {e}")
    
    async def _detect_and_queue_recoveries(self):
        """Detect failed services and queue appropriate recovery actions"""
        for service_name, state in self.service_states.items():
            if not state.healthy and not state.recovery_in_progress:
                # Determine recovery strategy based on service type and failure count
                strategy = self._determine_recovery_strategy(state)
                priority = self._determine_recovery_priority(state)
                
                # Check if we should attempt recovery
                if self._should_attempt_recovery(state):
                    recovery_action = RecoveryAction(
                        strategy=strategy,
                        target=service_name,
                        priority=priority,
                        max_attempts=self._get_max_attempts(state),
                        recovery_function=self._get_recovery_function(service_name, strategy)
                    )
                    
                    self.recovery_queue.append(recovery_action)
                    state.recovery_in_progress = True
                    
                    logger.info(
                        f"Queued recovery for {service_name}: {strategy.value} (priority: {priority.value})"
                    )
    
    def _determine_recovery_strategy(self, state: ServiceRecoveryState) -> RecoveryStrategy:
        """Determine the appropriate recovery strategy for a service"""
        if state.failure_count >= self.recovery_config["escalation_threshold"]:
            return RecoveryStrategy.ESCALATE_TO_ADMIN
        
        if state.failure_count >= self.recovery_config["degradation_threshold"]:
            if state.service_type == "extension":
                return RecoveryStrategy.GRACEFUL_DEGRADATION
            elif state.service_type == "database":
                return RecoveryStrategy.RESET_CONNECTIONS
        
        # First few attempts - try direct recovery
        if state.service_type == "extension":
            return RecoveryStrategy.RELOAD_EXTENSION
        elif state.service_type in ["authentication", "database"]:
            return RecoveryStrategy.RESTART_SERVICE
        elif state.service_type == "background_tasks":
            return RecoveryStrategy.RESTART_SERVICE
        else:
            return RecoveryStrategy.WAIT_AND_RETRY
    
    def _determine_recovery_priority(self, state: ServiceRecoveryState) -> RecoveryPriority:
        """Determine recovery priority based on service type"""
        if state.service_type == "authentication":
            return RecoveryPriority.CRITICAL
        elif state.service_type in ["extension", "extension_api"]:
            return RecoveryPriority.HIGH
        elif state.service_type in ["database", "background_tasks"]:
            return RecoveryPriority.HIGH
        else:
            return RecoveryPriority.MEDIUM
    
    def _should_attempt_recovery(self, state: ServiceRecoveryState) -> bool:
        """Determine if recovery should be attempted for a service"""
        # Don't attempt if already escalated
        if state.escalated:
            return False
        
        # Don't attempt if too many recent recovery attempts
        if state.last_recovery_attempt:
            time_since_last = datetime.now(timezone.utc) - state.last_recovery_attempt
            if time_since_last < timedelta(minutes=5) and state.recovery_attempts >= 3:
                return False
        
        return True
    
    def _get_max_attempts(self, state: ServiceRecoveryState) -> int:
        """Get maximum recovery attempts based on service type"""
        if state.service_type == "authentication":
            return 5  # Critical service gets more attempts
        elif state.service_type == "extension":
            return 3
        else:
            return 2
    
    def _get_recovery_function(self, service_name: str, strategy: RecoveryStrategy) -> Optional[Callable]:
        """Get the recovery function for a service and strategy"""
        if strategy == RecoveryStrategy.RELOAD_EXTENSION:
            return lambda: self._reload_extension_recovery(service_name)
        elif strategy == RecoveryStrategy.RESTART_SERVICE:
            return lambda: self._restart_service_recovery(service_name)
        elif strategy == RecoveryStrategy.RESET_CONNECTIONS:
            return lambda: self._reset_connections_recovery(service_name)
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return lambda: self._graceful_degradation_recovery(service_name)
        elif strategy == RecoveryStrategy.ESCALATE_TO_ADMIN:
            return lambda: self._escalate_to_admin_recovery(service_name)
        elif strategy == RecoveryStrategy.WAIT_AND_RETRY:
            return lambda: self._wait_and_retry_recovery(service_name)
        else:
            return None
    
    async def _process_recovery_queue(self):
        """Process queued recovery actions"""
        if not self.recovery_queue:
            return
        
        # Sort by priority (critical first)
        priority_order = {
            RecoveryPriority.CRITICAL: 0,
            RecoveryPriority.HIGH: 1,
            RecoveryPriority.MEDIUM: 2,
            RecoveryPriority.LOW: 3
        }
        
        self.recovery_queue.sort(key=lambda x: priority_order[x.priority])
        
        # Process recoveries up to max concurrent limit
        while (len(self._active_recoveries) < self.recovery_config["max_concurrent_recoveries"] 
               and self.recovery_queue):
            
            action = self.recovery_queue.pop(0)
            
            # Start recovery task
            recovery_task = asyncio.create_task(self._execute_recovery_action(action))
            self._active_recoveries[action.target] = recovery_task
    
    async def _execute_recovery_action(self, action: RecoveryAction):
        """Execute a recovery action"""
        try:
            logger.info(f"Starting recovery for {action.target}: {action.strategy.value}")
            
            action.current_attempts += 1
            action.last_attempt = datetime.now(timezone.utc)
            
            # Update service state
            if action.target in self.service_states:
                self.service_states[action.target].recovery_attempts += 1
                self.service_states[action.target].last_recovery_attempt = action.last_attempt
            
            # Execute recovery function with timeout
            if action.recovery_function:
                try:
                    await asyncio.wait_for(
                        action.recovery_function(),
                        timeout=action.timeout_seconds
                    )
                    action.success = True
                    logger.info(f"Recovery successful for {action.target}")
                    
                    # Update service state
                    if action.target in self.service_states:
                        self.service_states[action.target].recovery_in_progress = False
                        self.service_states[action.target].failure_count = 0
                
                except asyncio.TimeoutError:
                    action.error = f"Recovery timed out after {action.timeout_seconds} seconds"
                    logger.error(f"Recovery timeout for {action.target}: {action.error}")
                
                except Exception as e:
                    action.error = str(e)
                    logger.error(f"Recovery failed for {action.target}: {action.error}")
            
            # Handle retry logic
            if not action.success and action.current_attempts < action.max_attempts:
                # Exponential backoff
                backoff_time = action.backoff_seconds * (2 ** (action.current_attempts - 1))
                await asyncio.sleep(min(backoff_time, 60))  # Max 60 seconds backoff
                
                # Re-queue for retry
                self.recovery_queue.append(action)
                logger.info(f"Re-queuing recovery for {action.target} (attempt {action.current_attempts + 1})")
            else:
                # Recovery completed (success or max attempts reached)
                self.recovery_history.append(action)
                
                if action.target in self.service_states:
                    state = self.service_states[action.target]
                    state.recovery_in_progress = False
                    
                    if not action.success:
                        # Mark for escalation if all attempts failed
                        if action.current_attempts >= action.max_attempts:
                            state.escalated = True
                            logger.error(f"Recovery failed for {action.target} after {action.max_attempts} attempts")
        
        except Exception as e:
            logger.error(f"Error executing recovery action for {action.target}: {e}")
            action.error = str(e)
            self.recovery_history.append(action)
            
            if action.target in self.service_states:
                self.service_states[action.target].recovery_in_progress = False
        
        finally:
            # Remove from active recoveries
            if action.target in self._active_recoveries:
                del self._active_recoveries[action.target]
    
    async def _reload_extension_recovery(self, service_name: str):
        """Recovery function to reload an extension"""
        if not self.extension_manager:
            raise Exception("Extension manager not available")
        
        # Extract extension name from service name
        if service_name.startswith("extension_"):
            extension_name = service_name[10:]  # Remove "extension_" prefix
        else:
            extension_name = service_name
        
        logger.info(f"Attempting to reload extension: {extension_name}")
        
        try:
            # Reload the extension
            record = await self.extension_manager.reload_extension(extension_name)
            
            if record and record.status.value == "active":
                logger.info(f"Extension {extension_name} reloaded successfully")
            else:
                raise Exception(f"Extension {extension_name} failed to reload properly")
        
        except Exception as e:
            logger.error(f"Failed to reload extension {extension_name}: {e}")
            raise
    
    async def _restart_service_recovery(self, service_name: str):
        """Recovery function to restart a service"""
        logger.info(f"Attempting to restart service: {service_name}")
        
        if service_name == "authentication":
            # Restart authentication service
            try:
                from server.security import get_extension_auth_manager
                auth_manager = get_extension_auth_manager()
                if auth_manager and hasattr(auth_manager, 'restart'):
                    await auth_manager.restart()
                else:
                    logger.warning("Authentication service restart not implemented")
            except Exception as e:
                logger.error(f"Failed to restart authentication service: {e}")
                raise
        
        elif service_name == "background_tasks":
            # Restart background task system
            try:
                if self.extension_manager and hasattr(self.extension_manager, 'restart_background_tasks'):
                    await self.extension_manager.restart_background_tasks()
                else:
                    logger.warning("Background tasks restart not implemented")
            except Exception as e:
                logger.error(f"Failed to restart background tasks: {e}")
                raise
        
        else:
            logger.warning(f"Service restart not implemented for: {service_name}")
    
    async def _reset_connections_recovery(self, service_name: str):
        """Recovery function to reset database connections"""
        logger.info(f"Attempting to reset connections for: {service_name}")
        
        try:
            if self.database_config:
                # Reset database connections
                await self.database_config.reset_connections()
                logger.info("Database connections reset successfully")
            else:
                logger.warning("Database config not available for connection reset")
        
        except Exception as e:
            logger.error(f"Failed to reset connections: {e}")
            raise
    
    async def _graceful_degradation_recovery(self, service_name: str):
        """Recovery function to enable graceful degradation"""
        logger.info(f"Enabling graceful degradation for: {service_name}")
        
        try:
            # Update service state to degraded mode
            if service_name in self.service_states:
                self.service_states[service_name].degraded_mode = True
            
            # Call degradation handler if available
            if service_name in self._graceful_degradation_handlers:
                await self._graceful_degradation_handlers[service_name]()
            
            logger.info(f"Graceful degradation enabled for {service_name}")
        
        except Exception as e:
            logger.error(f"Failed to enable graceful degradation for {service_name}: {e}")
            raise
    
    async def _escalate_to_admin_recovery(self, service_name: str):
        """Recovery function to escalate to admin"""
        logger.error(f"Escalating {service_name} failure to admin")

        try:
            # Mark as escalated
            if service_name in self.service_states:
                self.service_states[service_name].escalated = True

            state = self.service_states.get(service_name)
            failure_count = state.failure_count if state else None
            recovery_attempts = state.recovery_attempts if state else None
            last_health_check = state.last_health_check.isoformat() if state else None
            last_recovery_attempt = (
                state.last_recovery_attempt.isoformat() if state and state.last_recovery_attempt else None
            )

            logger.critical(
                "Service recovery escalation required",
                extra={
                    "service": service_name,
                    "failure_count": failure_count,
                    "recovery_attempts": recovery_attempts,
                    "escalated": True,
                }
            )

            recovery_context = {
                "service": service_name,
                "failure_count": failure_count,
                "recovery_attempts": recovery_attempts,
                "last_health_check": last_health_check,
                "last_recovery_attempt": last_recovery_attempt,
            }

            # Dispatch structured alert through central alert manager
            await extension_alert_manager.create_manual_alert(
                alert_type=AlertType.RECOVERY_FAILURE,
                severity=ErrorSeverity.CRITICAL,
                message=(
                    f"Service {service_name} has exhausted automated recovery options and requires"
                    " administrator intervention."
                ),
                context=recovery_context,
                escalation_level=EscalationLevel.LEVEL_3,
            )

        except Exception as e:
            logger.error(f"Failed to escalate {service_name}: {e}")
            raise
    
    async def _wait_and_retry_recovery(self, service_name: str):
        """Recovery function that waits and retries"""
        logger.info(f"Waiting and retrying for: {service_name}")
        
        # Simple wait - the health check will re-evaluate
        await asyncio.sleep(30)
        
        # Reset failure count to give it another chance
        if service_name in self.service_states:
            self.service_states[service_name].failure_count = max(0, 
                self.service_states[service_name].failure_count - 1)
    
    def _cleanup_completed_recoveries(self):
        """Clean up completed recovery tasks"""
        completed_tasks = []
        for target, task in self._active_recoveries.items():
            if task.done():
                completed_tasks.append(target)
        
        for target in completed_tasks:
            del self._active_recoveries[target]
    
    def _cleanup_recovery_history(self):
        """Clean up old recovery history"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            hours=self.recovery_config["history_retention_hours"]
        )
        
        self.recovery_history = [
            action for action in self.recovery_history
            if action.created_at >= cutoff_time
        ]
    
    # Integration methods for existing startup/shutdown handlers
    
    def add_startup_handler(self, handler: Callable):
        """Add a startup handler for extension lifecycle management"""
        self._startup_handlers.append(handler)
    
    def add_shutdown_handler(self, handler: Callable):
        """Add a shutdown handler for extension lifecycle management"""
        self._shutdown_handlers.append(handler)
    
    def add_graceful_degradation_handler(self, service_name: str, handler: Callable):
        """Add a graceful degradation handler for a specific service"""
        self._graceful_degradation_handlers[service_name] = handler
    
    async def execute_startup_handlers(self):
        """Execute all registered startup handlers"""
        for handler in self._startup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Startup handler failed: {e}")
    
    async def execute_shutdown_handlers(self):
        """Execute all registered shutdown handlers"""
        for handler in self._shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Shutdown handler failed: {e}")
    
    # API methods for monitoring and control
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status"""
        return {
            "recovery_active": self._recovery_active,
            "active_recoveries": len(self._active_recoveries),
            "queued_recoveries": len(self.recovery_queue),
            "service_states": {
                name: {
                    "healthy": state.healthy,
                    "failure_count": state.failure_count,
                    "recovery_attempts": state.recovery_attempts,
                    "recovery_in_progress": state.recovery_in_progress,
                    "degraded_mode": state.degraded_mode,
                    "escalated": state.escalated,
                    "last_health_check": state.last_health_check.isoformat(),
                    "last_recovery_attempt": state.last_recovery_attempt.isoformat() if state.last_recovery_attempt else None
                }
                for name, state in self.service_states.items()
            },
            "recovery_history_count": len(self.recovery_history),
            "config": self.recovery_config
        }
    
    def get_recovery_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recovery history for the specified number of hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return [
            {
                "strategy": action.strategy.value,
                "target": action.target,
                "priority": action.priority.value,
                "attempts": action.current_attempts,
                "max_attempts": action.max_attempts,
                "success": action.success,
                "error": action.error,
                "created_at": action.created_at.isoformat(),
                "last_attempt": action.last_attempt.isoformat() if action.last_attempt else None
            }
            for action in self.recovery_history
            if action.created_at >= cutoff_time
        ]
    
    async def force_recovery(self, service_name: str, strategy: RecoveryStrategy = None) -> bool:
        """Force a recovery attempt for a specific service"""
        if service_name not in self.service_states:
            logger.error(f"Service {service_name} not found in service states")
            return False
        
        state = self.service_states[service_name]
        
        # Determine strategy if not provided
        if strategy is None:
            strategy = self._determine_recovery_strategy(state)
        
        priority = self._determine_recovery_priority(state)
        
        recovery_action = RecoveryAction(
            strategy=strategy,
            target=service_name,
            priority=priority,
            max_attempts=1,  # Single attempt for forced recovery
            recovery_function=self._get_recovery_function(service_name, strategy)
        )
        
        # Add to front of queue for immediate processing
        self.recovery_queue.insert(0, recovery_action)
        state.recovery_in_progress = True
        
        logger.info(f"Forced recovery queued for {service_name}: {strategy.value}")
        return True


# Global instance
_extension_service_recovery_manager: Optional[ExtensionServiceRecoveryManager] = None


def get_extension_service_recovery_manager() -> Optional[ExtensionServiceRecoveryManager]:
    """Get the global extension service recovery manager"""
    return _extension_service_recovery_manager


async def initialize_extension_service_recovery_manager(
    extension_manager=None,
    database_config=None,
    enhanced_health_monitor=None
) -> ExtensionServiceRecoveryManager:
    """Initialize the extension service recovery manager"""
    global _extension_service_recovery_manager
    
    _extension_service_recovery_manager = ExtensionServiceRecoveryManager(
        extension_manager=extension_manager,
        database_config=database_config,
        enhanced_health_monitor=enhanced_health_monitor
    )
    
    await _extension_service_recovery_manager.start_recovery_system()
    
    logger.info("Extension service recovery manager initialized")
    return _extension_service_recovery_manager


async def shutdown_extension_service_recovery_manager():
    """Shutdown the extension service recovery manager"""
    global _extension_service_recovery_manager
    
    if _extension_service_recovery_manager:
        await _extension_service_recovery_manager.stop_recovery_system()
        _extension_service_recovery_manager = None
    
    logger.info("Extension service recovery manager shutdown completed")