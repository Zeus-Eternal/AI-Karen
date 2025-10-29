"""
Extension Health Monitor

Monitors extension health and triggers recovery actions when needed.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from sqlalchemy.orm import Session

from .models import (
    ExtensionHealth,
    ExtensionHealthStatus,
    HealthCheckConfig,
    LifecycleEvent,
    LifecycleEventType,
    RecoveryAction,
    RecoveryActionType
)
from ..manager import ExtensionManager
from ..registry import ExtensionRegistry


class ExtensionHealthMonitor:
    """Monitors extension health and triggers recovery actions."""
    
    def __init__(
        self,
        extension_manager: ExtensionManager,
        db_session: Session,
        check_interval: int = 60
    ):
        self.extension_manager = extension_manager
        self.db_session = db_session
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)
        
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._health_cache: Dict[str, ExtensionHealth] = {}
        self._recovery_actions: Dict[str, List[RecoveryAction]] = {}
        self._health_callbacks: List[Callable[[ExtensionHealth], None]] = []
        
        self.is_running = False
    
    async def start_monitoring(self) -> None:
        """Start health monitoring for all extensions."""
        self.is_running = True
        self.logger.info("Starting extension health monitoring")
        
        # Start monitoring tasks for each extension
        extensions = await self.extension_manager.get_loaded_extensions()
        for extension_name in extensions:
            await self.start_extension_monitoring(extension_name)
    
    async def stop_monitoring(self) -> None:
        """Stop all health monitoring."""
        self.is_running = False
        self.logger.info("Stopping extension health monitoring")
        
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        self._monitoring_tasks.clear()
    
    async def start_extension_monitoring(self, extension_name: str) -> None:
        """Start monitoring a specific extension."""
        if extension_name in self._monitoring_tasks:
            return
        
        config = await self._get_health_config(extension_name)
        task = asyncio.create_task(
            self._monitor_extension_health(extension_name, config)
        )
        self._monitoring_tasks[extension_name] = task
        
        self.logger.info(f"Started health monitoring for extension: {extension_name}")
    
    async def stop_extension_monitoring(self, extension_name: str) -> None:
        """Stop monitoring a specific extension."""
        if extension_name in self._monitoring_tasks:
            self._monitoring_tasks[extension_name].cancel()
            del self._monitoring_tasks[extension_name]
            
        if extension_name in self._health_cache:
            del self._health_cache[extension_name]
        
        self.logger.info(f"Stopped health monitoring for extension: {extension_name}")
    
    async def get_extension_health(self, extension_name: str) -> Optional[ExtensionHealth]:
        """Get current health status of an extension."""
        return self._health_cache.get(extension_name)
    
    async def get_all_health_status(self) -> Dict[str, ExtensionHealth]:
        """Get health status of all monitored extensions."""
        return self._health_cache.copy()
    
    def add_health_callback(self, callback: Callable[[ExtensionHealth], None]) -> None:
        """Add a callback to be called when health status changes."""
        self._health_callbacks.append(callback)
    
    async def configure_recovery_actions(
        self, 
        extension_name: str, 
        actions: List[RecoveryAction]
    ) -> None:
        """Configure recovery actions for an extension."""
        self._recovery_actions[extension_name] = actions
        self.logger.info(
            f"Configured {len(actions)} recovery actions for extension: {extension_name}"
        )
    
    async def _monitor_extension_health(
        self, 
        extension_name: str, 
        config: HealthCheckConfig
    ) -> None:
        """Monitor health of a specific extension."""
        consecutive_failures = 0
        consecutive_successes = 0
        
        while self.is_running:
            try:
                # Perform health check
                health = await self._perform_health_check(extension_name, config)
                
                # Update health cache
                self._health_cache[extension_name] = health
                
                # Determine if health check passed or failed
                health_passed = health.status in [
                    ExtensionHealthStatus.HEALTHY,
                    ExtensionHealthStatus.DEGRADED
                ]
                
                if health_passed:
                    consecutive_failures = 0
                    consecutive_successes += 1
                    
                    # Log health check passed event
                    if consecutive_successes == config.success_threshold:
                        await self._log_lifecycle_event(
                            extension_name,
                            LifecycleEventType.HEALTH_CHECK_PASSED,
                            {"health": health.dict()}
                        )
                else:
                    consecutive_successes = 0
                    consecutive_failures += 1
                    
                    # Log health check failed event
                    await self._log_lifecycle_event(
                        extension_name,
                        LifecycleEventType.HEALTH_CHECK_FAILED,
                        {
                            "health": health.dict(),
                            "consecutive_failures": consecutive_failures
                        }
                    )
                    
                    # Trigger recovery if threshold reached
                    if consecutive_failures >= config.failure_threshold:
                        await self._trigger_recovery(extension_name, health)
                        consecutive_failures = 0
                
                # Notify callbacks
                for callback in self._health_callbacks:
                    try:
                        callback(health)
                    except Exception as e:
                        self.logger.error(f"Health callback error: {e}")
                
                # Wait for next check
                await asyncio.sleep(config.check_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Error monitoring extension {extension_name}: {e}"
                )
                await asyncio.sleep(config.check_interval_seconds)
    
    async def _perform_health_check(
        self, 
        extension_name: str, 
        config: HealthCheckConfig
    ) -> ExtensionHealth:
        """Perform comprehensive health check on an extension."""
        start_time = time.time()
        
        try:
            # Get extension instance
            extension = await self.extension_manager.get_extension(extension_name)
            if not extension:
                return ExtensionHealth(
                    extension_name=extension_name,
                    status=ExtensionHealthStatus.CRITICAL,
                    last_check=datetime.utcnow(),
                    cpu_usage=0,
                    memory_usage=0,
                    disk_usage=0,
                    error_rate=100,
                    response_time=0,
                    uptime=0,
                    restart_count=0,
                    last_error="Extension not found",
                    health_score=0
                )
            
            # Collect system metrics
            metrics = await self._collect_system_metrics(extension_name)
            
            # Perform custom health checks
            custom_results = await self._perform_custom_checks(extension_name, config)
            
            # Calculate health score
            health_score = self._calculate_health_score(metrics, custom_results, config)
            
            # Determine status based on score and thresholds
            status = self._determine_health_status(health_score, metrics, config)
            
            response_time = time.time() - start_time
            
            return ExtensionHealth(
                extension_name=extension_name,
                status=status,
                last_check=datetime.utcnow(),
                cpu_usage=metrics.get("cpu_usage", 0),
                memory_usage=metrics.get("memory_usage", 0),
                disk_usage=metrics.get("disk_usage", 0),
                error_rate=metrics.get("error_rate", 0),
                response_time=response_time * 1000,  # Convert to milliseconds
                uptime=metrics.get("uptime", 0),
                restart_count=metrics.get("restart_count", 0),
                last_error=metrics.get("last_error"),
                health_score=health_score,
                metrics={**metrics, **custom_results}
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed for {extension_name}: {e}")
            return ExtensionHealth(
                extension_name=extension_name,
                status=ExtensionHealthStatus.UNKNOWN,
                last_check=datetime.utcnow(),
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                error_rate=100,
                response_time=0,
                uptime=0,
                restart_count=0,
                last_error=str(e),
                health_score=0
            )
    
    async def _collect_system_metrics(self, extension_name: str) -> Dict[str, Any]:
        """Collect system metrics for an extension."""
        metrics = {}
        
        try:
            # Get extension process info
            extension_info = await self.extension_manager.get_extension_info(extension_name)
            
            if extension_info and extension_info.get("process_id"):
                process = psutil.Process(extension_info["process_id"])
                
                # CPU usage
                metrics["cpu_usage"] = process.cpu_percent()
                
                # Memory usage
                memory_info = process.memory_info()
                metrics["memory_usage"] = memory_info.rss / (1024 * 1024)  # MB
                
                # Uptime
                create_time = process.create_time()
                metrics["uptime"] = time.time() - create_time
                
                # File descriptors (if available)
                try:
                    metrics["open_files"] = process.num_fds()
                except (AttributeError, psutil.AccessDenied):
                    pass
            
            # Get extension-specific metrics from registry
            registry_metrics = await self._get_registry_metrics(extension_name)
            metrics.update(registry_metrics)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.warning(f"Could not collect metrics for {extension_name}: {e}")
            metrics["collection_error"] = str(e)
        
        return metrics
    
    async def _perform_custom_checks(
        self, 
        extension_name: str, 
        config: HealthCheckConfig
    ) -> Dict[str, Any]:
        """Perform custom health checks defined in configuration."""
        results = {}
        
        for check in config.custom_checks:
            check_name = check.get("name", "unknown")
            try:
                # Execute custom check
                result = await self._execute_custom_check(extension_name, check)
                results[f"custom_{check_name}"] = result
            except Exception as e:
                self.logger.error(
                    f"Custom check '{check_name}' failed for {extension_name}: {e}"
                )
                results[f"custom_{check_name}_error"] = str(e)
        
        return results
    
    async def _execute_custom_check(
        self, 
        extension_name: str, 
        check_config: Dict[str, Any]
    ) -> Any:
        """Execute a single custom health check."""
        check_type = check_config.get("type", "ping")
        
        if check_type == "ping":
            # Simple ping check
            extension = await self.extension_manager.get_extension(extension_name)
            return extension is not None
        
        elif check_type == "api_endpoint":
            # Check if API endpoint responds
            endpoint = check_config.get("endpoint", "/health")
            timeout = check_config.get("timeout", 5)
            
            # This would need to be implemented based on your API client
            # For now, return a placeholder
            return True
        
        elif check_type == "database_connection":
            # Check database connectivity
            # This would need to be implemented based on your database setup
            return True
        
        else:
            raise ValueError(f"Unknown check type: {check_type}")
    
    def _calculate_health_score(
        self, 
        metrics: Dict[str, Any], 
        custom_results: Dict[str, Any],
        config: HealthCheckConfig
    ) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        # CPU usage penalty
        cpu_usage = metrics.get("cpu_usage", 0)
        if cpu_usage > config.thresholds.get("cpu_critical", 90):
            score -= 30
        elif cpu_usage > config.thresholds.get("cpu_warning", 70):
            score -= 15
        
        # Memory usage penalty
        memory_usage = metrics.get("memory_usage", 0)
        memory_limit = config.thresholds.get("memory_limit_mb", 512)
        if memory_usage > memory_limit:
            score -= 25
        elif memory_usage > memory_limit * 0.8:
            score -= 10
        
        # Error rate penalty
        error_rate = metrics.get("error_rate", 0)
        if error_rate > config.thresholds.get("error_rate_critical", 10):
            score -= 40
        elif error_rate > config.thresholds.get("error_rate_warning", 5):
            score -= 20
        
        # Response time penalty
        response_time = metrics.get("response_time", 0)
        if response_time > config.thresholds.get("response_time_critical", 5000):
            score -= 20
        elif response_time > config.thresholds.get("response_time_warning", 2000):
            score -= 10
        
        # Custom check penalties
        for key, value in custom_results.items():
            if key.endswith("_error"):
                score -= 15
            elif isinstance(value, bool) and not value:
                score -= 10
        
        return max(0.0, score)
    
    def _determine_health_status(
        self, 
        health_score: float, 
        metrics: Dict[str, Any],
        config: HealthCheckConfig
    ) -> ExtensionHealthStatus:
        """Determine health status based on score and metrics."""
        if health_score >= 90:
            return ExtensionHealthStatus.HEALTHY
        elif health_score >= 70:
            return ExtensionHealthStatus.DEGRADED
        elif health_score >= 30:
            return ExtensionHealthStatus.UNHEALTHY
        else:
            return ExtensionHealthStatus.CRITICAL
    
    async def _trigger_recovery(
        self, 
        extension_name: str, 
        health: ExtensionHealth
    ) -> None:
        """Trigger recovery actions for an unhealthy extension."""
        actions = self._recovery_actions.get(extension_name, [])
        
        if not actions:
            # Default recovery action
            actions = [
                RecoveryAction(
                    action_id=f"default_restart_{extension_name}",
                    extension_name=extension_name,
                    action_type=RecoveryActionType.RESTART,
                    trigger_condition="health_check_failed",
                    max_attempts=3,
                    cooldown_seconds=300
                )
            ]
        
        # Sort by priority
        actions.sort(key=lambda x: x.priority)
        
        for action in actions:
            if not action.is_enabled:
                continue
            
            try:
                await self._execute_recovery_action(action, health)
                break  # Stop after first successful action
            except Exception as e:
                self.logger.error(
                    f"Recovery action {action.action_type} failed for {extension_name}: {e}"
                )
    
    async def _execute_recovery_action(
        self, 
        action: RecoveryAction, 
        health: ExtensionHealth
    ) -> None:
        """Execute a specific recovery action."""
        self.logger.info(
            f"Executing recovery action {action.action_type} for {action.extension_name}"
        )
        
        await self._log_lifecycle_event(
            action.extension_name,
            LifecycleEventType.RECOVERY_INITIATED,
            {"action": action.dict(), "health": health.dict()}
        )
        
        if action.action_type == RecoveryActionType.RESTART:
            await self.extension_manager.restart_extension(action.extension_name)
        
        elif action.action_type == RecoveryActionType.ROLLBACK:
            # This would integrate with the migration manager
            pass
        
        elif action.action_type == RecoveryActionType.RESTORE_BACKUP:
            # This would integrate with the backup manager
            pass
        
        elif action.action_type == RecoveryActionType.DISABLE:
            await self.extension_manager.disable_extension(action.extension_name)
        
        elif action.action_type == RecoveryActionType.CLEAR_CACHE:
            await self.extension_manager.clear_extension_cache(action.extension_name)
        
        await self._log_lifecycle_event(
            action.extension_name,
            LifecycleEventType.RECOVERY_COMPLETED,
            {"action": action.dict()}
        )
    
    async def _get_health_config(self, extension_name: str) -> HealthCheckConfig:
        """Get health check configuration for an extension."""
        # This would typically load from database or configuration file
        # For now, return default configuration
        return HealthCheckConfig(
            extension_name=extension_name,
            check_interval_seconds=self.check_interval,
            thresholds={
                "cpu_warning": 70,
                "cpu_critical": 90,
                "memory_limit_mb": 512,
                "error_rate_warning": 5,
                "error_rate_critical": 10,
                "response_time_warning": 2000,
                "response_time_critical": 5000
            }
        )
    
    async def _get_registry_metrics(self, extension_name: str) -> Dict[str, Any]:
        """Get metrics from extension registry."""
        # This would query the extension registry for metrics
        # For now, return empty dict
        return {}
    
    async def _log_lifecycle_event(
        self, 
        extension_name: str, 
        event_type: LifecycleEventType,
        details: Dict[str, Any]
    ) -> None:
        """Log a lifecycle event."""
        event = LifecycleEvent(
            event_id=f"{extension_name}_{event_type}_{int(time.time())}",
            extension_name=extension_name,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            details=details
        )
        
        # This would typically save to database
        self.logger.info(f"Lifecycle event: {event.dict()}")