"""
Graceful Degradation Controller

This module coordinates graceful degradation of system functionality
when services fail, ensuring core functionality remains available.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from .error_recovery_manager import ErrorRecoveryManager, ServiceStatus
from .service_health_monitor import ServiceHealthMonitor
from .fallback_mechanisms import FallbackManager, FallbackType
from .service_classification import ServiceClassification


class DegradationLevel(Enum):
    """Levels of system degradation"""
    NORMAL = "normal"           # All services operational
    MINOR = "minor"             # Some optional services degraded
    MODERATE = "moderate"       # Multiple services affected, fallbacks active
    SEVERE = "severe"           # Essential services affected
    CRITICAL = "critical"       # Core functionality at risk


@dataclass
class DegradationRule:
    """Rule for determining degradation actions"""
    trigger_condition: str      # Condition that triggers this rule
    degradation_level: DegradationLevel
    affected_services: List[str]
    actions: List[str]          # Actions to take when triggered
    priority: int = 1           # Lower number = higher priority


@dataclass
class SystemState:
    """Current system state and degradation status"""
    degradation_level: DegradationLevel = DegradationLevel.NORMAL
    failed_services: Set[str] = field(default_factory=set)
    degraded_services: Set[str] = field(default_factory=set)
    active_fallbacks: Set[str] = field(default_factory=set)
    disabled_features: Set[str] = field(default_factory=set)
    last_update: datetime = field(default_factory=datetime.now)
    degradation_reason: str = ""


class GracefulDegradationController:
    """
    Controls graceful degradation of system functionality when services fail,
    ensuring core functionality remains available while non-essential features
    are disabled or simplified.
    """
    
    def __init__(self, 
                 error_recovery_manager: Optional[ErrorRecoveryManager] = None,
                 health_monitor: Optional[ServiceHealthMonitor] = None,
                 fallback_manager: Optional[FallbackManager] = None):
        
        self.logger = logging.getLogger(__name__)
        
        # Component dependencies
        self.error_recovery_manager = error_recovery_manager
        self.health_monitor = health_monitor
        self.fallback_manager = fallback_manager
        
        # System state tracking
        self.system_state = SystemState()
        self.degradation_rules: List[DegradationRule] = []
        
        # Service classification
        self.essential_services: Set[str] = set()
        self.optional_services: Set[str] = set()
        self.background_services: Set[str] = set()
        
        # Feature management
        self.feature_dependencies: Dict[str, Set[str]] = {}  # feature -> required services
        self.service_features: Dict[str, Set[str]] = {}      # service -> provided features
        
        # Degradation actions
        self.degradation_actions: Dict[str, Callable] = {}
        self.recovery_actions: Dict[str, Callable] = {}
        
        # Monitoring and alerting
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.state_history: List[SystemState] = []
        
        self._setup_default_rules()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup degradation logging"""
        Path("logs").mkdir(exist_ok=True)
        
        # Create dedicated logger for degradation events
        self.degradation_logger = logging.getLogger("graceful_degradation")
        self.degradation_logger.setLevel(logging.INFO)
        
        # File handler for degradation logs
        handler = logging.FileHandler("logs/graceful_degradation.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.degradation_logger.addHandler(handler)
    
    def _setup_default_rules(self):
        """Setup default degradation rules"""
        # Rule for essential service failures
        self.add_degradation_rule(DegradationRule(
            trigger_condition="essential_service_failed",
            degradation_level=DegradationLevel.SEVERE,
            affected_services=[],
            actions=["activate_emergency_mode", "notify_administrators"],
            priority=1
        ))
        
        # Rule for multiple service failures
        self.add_degradation_rule(DegradationRule(
            trigger_condition="multiple_services_failed",
            degradation_level=DegradationLevel.MODERATE,
            affected_services=[],
            actions=["activate_fallbacks", "disable_non_essential_features"],
            priority=2
        ))
        
        # Rule for optional service failures
        self.add_degradation_rule(DegradationRule(
            trigger_condition="optional_service_failed",
            degradation_level=DegradationLevel.MINOR,
            affected_services=[],
            actions=["activate_fallback", "log_degradation"],
            priority=3
        ))
    
    def register_service_classification(self, service_name: str, 
                                      classification: ServiceClassification):
        """Register a service with its classification"""
        if classification == ServiceClassification.ESSENTIAL:
            self.essential_services.add(service_name)
        elif classification == ServiceClassification.OPTIONAL:
            self.optional_services.add(service_name)
        elif classification == ServiceClassification.BACKGROUND:
            self.background_services.add(service_name)
        
        self.logger.info(f"Registered service {service_name} as {classification.value}")
    
    def register_feature_dependency(self, feature_name: str, required_services: List[str]):
        """Register a feature and its service dependencies"""
        self.feature_dependencies[feature_name] = set(required_services)
        
        # Update reverse mapping
        for service in required_services:
            if service not in self.service_features:
                self.service_features[service] = set()
            self.service_features[service].add(feature_name)
        
        self.logger.info(f"Registered feature {feature_name} with dependencies: {required_services}")
    
    def add_degradation_rule(self, rule: DegradationRule):
        """Add a degradation rule"""
        self.degradation_rules.append(rule)
        # Sort by priority (lower number = higher priority)
        self.degradation_rules.sort(key=lambda r: r.priority)
        
        self.logger.info(f"Added degradation rule: {rule.trigger_condition} -> {rule.degradation_level.value}")
    
    def register_degradation_action(self, action_name: str, action_func: Callable):
        """Register a degradation action function"""
        self.degradation_actions[action_name] = action_func
        self.logger.info(f"Registered degradation action: {action_name}")
    
    def register_recovery_action(self, action_name: str, action_func: Callable):
        """Register a recovery action function"""
        self.recovery_actions[action_name] = action_func
        self.logger.info(f"Registered recovery action: {action_name}")
    
    async def handle_service_failure(self, service_name: str, error: Exception):
        """Handle a service failure and determine degradation response"""
        self.degradation_logger.warning(f"Handling service failure: {service_name} - {error}")
        
        # Update system state
        self.system_state.failed_services.add(service_name)
        self.system_state.last_update = datetime.now()
        
        # Determine degradation level and actions
        await self._evaluate_degradation_rules(service_name)
        
        # Execute degradation actions
        await self._execute_degradation_actions(service_name)
        
        # Update feature availability
        await self._update_feature_availability()
        
        # Save state history
        self._save_state_snapshot()
    
    async def handle_service_recovery(self, service_name: str):
        """Handle a service recovery and potential system recovery"""
        self.degradation_logger.info(f"Handling service recovery: {service_name}")
        
        # Update system state
        self.system_state.failed_services.discard(service_name)
        self.system_state.degraded_services.discard(service_name)
        self.system_state.last_update = datetime.now()
        
        # Check if we can improve degradation level
        await self._evaluate_recovery_potential()
        
        # Execute recovery actions
        await self._execute_recovery_actions(service_name)
        
        # Update feature availability
        await self._update_feature_availability()
        
        # Save state history
        self._save_state_snapshot()
    
    async def _evaluate_degradation_rules(self, failed_service: str):
        """Evaluate degradation rules and determine appropriate response"""
        previous_level = self.system_state.degradation_level
        
        # Check if essential service failed
        if failed_service in self.essential_services:
            await self._apply_degradation_rule("essential_service_failed", failed_service)
        
        # Check for multiple failures
        elif len(self.system_state.failed_services) >= 3:
            await self._apply_degradation_rule("multiple_services_failed", failed_service)
        
        # Optional service failure
        elif failed_service in self.optional_services:
            await self._apply_degradation_rule("optional_service_failed", failed_service)
        
        # Background service failure (usually no degradation)
        elif failed_service in self.background_services:
            self.degradation_logger.info(f"Background service {failed_service} failed - no degradation needed")
        
        # Log degradation level change
        if self.system_state.degradation_level != previous_level:
            self.degradation_logger.warning(
                f"System degradation level changed: {previous_level.value} -> {self.system_state.degradation_level.value}"
            )
    
    async def _apply_degradation_rule(self, trigger_condition: str, service_name: str):
        """Apply a specific degradation rule"""
        for rule in self.degradation_rules:
            if rule.trigger_condition == trigger_condition:
                # Update degradation level if more severe
                if rule.degradation_level.value > self.system_state.degradation_level.value:
                    self.system_state.degradation_level = rule.degradation_level
                    self.system_state.degradation_reason = f"{trigger_condition}: {service_name}"
                
                # Execute rule actions
                for action in rule.actions:
                    await self._execute_action(action, service_name)
                
                break
    
    async def _execute_degradation_actions(self, service_name: str):
        """Execute degradation actions for a failed service"""
        # Try to activate fallback if available
        if self.fallback_manager:
            try:
                if await self.fallback_manager.activate_fallback(service_name):
                    self.system_state.active_fallbacks.add(service_name)
                    self.system_state.degraded_services.add(service_name)
                    self.degradation_logger.info(f"Activated fallback for {service_name}")
                else:
                    self.degradation_logger.warning(f"No fallback available for {service_name}")
            except Exception as e:
                self.degradation_logger.error(f"Failed to activate fallback for {service_name}: {e}")
        
        # Disable dependent features if no fallback
        if service_name not in self.system_state.active_fallbacks:
            affected_features = self.service_features.get(service_name, set())
            for feature in affected_features:
                await self._disable_feature(feature)
    
    async def _execute_recovery_actions(self, service_name: str):
        """Execute recovery actions for a recovered service"""
        # Deactivate fallback if active
        if service_name in self.system_state.active_fallbacks:
            if self.fallback_manager:
                try:
                    await self.fallback_manager.deactivate_fallback(service_name)
                    self.system_state.active_fallbacks.discard(service_name)
                    self.degradation_logger.info(f"Deactivated fallback for {service_name}")
                except Exception as e:
                    self.degradation_logger.error(f"Failed to deactivate fallback for {service_name}: {e}")
        
        # Re-enable dependent features
        affected_features = self.service_features.get(service_name, set())
        for feature in affected_features:
            await self._enable_feature(feature)
    
    async def _execute_action(self, action_name: str, service_name: str):
        """Execute a specific degradation or recovery action"""
        if action_name in self.degradation_actions:
            try:
                action_func = self.degradation_actions[action_name]
                if asyncio.iscoroutinefunction(action_func):
                    await action_func(service_name)
                else:
                    action_func(service_name)
            except Exception as e:
                self.logger.error(f"Failed to execute degradation action {action_name}: {e}")
        
        elif action_name in self.recovery_actions:
            try:
                action_func = self.recovery_actions[action_name]
                if asyncio.iscoroutinefunction(action_func):
                    await action_func(service_name)
                else:
                    action_func(service_name)
            except Exception as e:
                self.logger.error(f"Failed to execute recovery action {action_name}: {e}")
        
        else:
            # Built-in actions
            await self._execute_builtin_action(action_name, service_name)
    
    async def _execute_builtin_action(self, action_name: str, service_name: str):
        """Execute built-in degradation actions"""
        if action_name == "activate_emergency_mode":
            await self._activate_emergency_mode()
        
        elif action_name == "notify_administrators":
            await self._notify_administrators(f"Critical service failure: {service_name}")
        
        elif action_name == "activate_fallbacks":
            await self._activate_all_available_fallbacks()
        
        elif action_name == "disable_non_essential_features":
            await self._disable_non_essential_features()
        
        elif action_name == "activate_fallback":
            if self.fallback_manager:
                await self.fallback_manager.activate_fallback(service_name)
        
        elif action_name == "log_degradation":
            self.degradation_logger.warning(f"Service degradation: {service_name}")
    
    async def _activate_emergency_mode(self):
        """Activate emergency mode - minimal functionality only"""
        self.degradation_logger.critical("Activating emergency mode")
        
        # Disable all non-essential features
        await self._disable_non_essential_features()
        
        # Stop background services
        for service in self.background_services:
            try:
                # Import here to avoid circular imports
                from .service_lifecycle_manager import ServiceLifecycleManager
                lifecycle_manager = ServiceLifecycleManager()
                await lifecycle_manager.suspend_service(service)
            except Exception as e:
                self.logger.error(f"Failed to suspend background service {service}: {e}")
    
    async def _notify_administrators(self, message: str):
        """Notify administrators of critical issues"""
        self.degradation_logger.critical(f"ADMIN ALERT: {message}")
        
        # Send alert through error recovery manager if available
        if self.error_recovery_manager:
            await self.error_recovery_manager._send_alert(message, "critical")
    
    async def _activate_all_available_fallbacks(self):
        """Activate fallbacks for all failed services where available"""
        if not self.fallback_manager:
            return
        
        for service in self.system_state.failed_services:
            if service not in self.system_state.active_fallbacks:
                try:
                    if await self.fallback_manager.activate_fallback(service):
                        self.system_state.active_fallbacks.add(service)
                        self.system_state.degraded_services.add(service)
                except Exception as e:
                    self.logger.error(f"Failed to activate fallback for {service}: {e}")
    
    async def _disable_non_essential_features(self):
        """Disable all non-essential features"""
        for feature_name, required_services in self.feature_dependencies.items():
            # Check if any required service is failed and has no fallback
            has_failed_dependency = False
            for service in required_services:
                if (service in self.system_state.failed_services and 
                    service not in self.system_state.active_fallbacks):
                    has_failed_dependency = True
                    break
            
            if has_failed_dependency:
                await self._disable_feature(feature_name)
    
    async def _disable_feature(self, feature_name: str):
        """Disable a specific feature"""
        if feature_name not in self.system_state.disabled_features:
            self.system_state.disabled_features.add(feature_name)
            self.degradation_logger.info(f"Disabled feature: {feature_name}")
    
    async def _enable_feature(self, feature_name: str):
        """Enable a specific feature if dependencies are available"""
        required_services = self.feature_dependencies.get(feature_name, set())
        
        # Check if all required services are available (either healthy or with fallback)
        all_available = True
        for service in required_services:
            if (service in self.system_state.failed_services and 
                service not in self.system_state.active_fallbacks):
                all_available = False
                break
        
        if all_available and feature_name in self.system_state.disabled_features:
            self.system_state.disabled_features.discard(feature_name)
            self.degradation_logger.info(f"Re-enabled feature: {feature_name}")
    
    async def _update_feature_availability(self):
        """Update availability of all features based on current service status"""
        for feature_name in list(self.feature_dependencies.keys()):
            required_services = self.feature_dependencies[feature_name]
            
            # Check if all required services are available
            all_available = True
            for service in required_services:
                if (service in self.system_state.failed_services and 
                    service not in self.system_state.active_fallbacks):
                    all_available = False
                    break
            
            if all_available:
                await self._enable_feature(feature_name)
            else:
                await self._disable_feature(feature_name)
    
    async def _evaluate_recovery_potential(self):
        """Evaluate if system can recover to a better degradation level"""
        # Count current issues
        failed_essential = len([s for s in self.system_state.failed_services if s in self.essential_services])
        total_failed = len(self.system_state.failed_services)
        
        # Determine new degradation level
        new_level = DegradationLevel.NORMAL
        
        if failed_essential > 0:
            new_level = DegradationLevel.SEVERE
        elif total_failed >= 3:
            new_level = DegradationLevel.MODERATE
        elif total_failed > 0:
            new_level = DegradationLevel.MINOR
        
        # Update if improved
        if new_level.value < self.system_state.degradation_level.value:
            previous_level = self.system_state.degradation_level
            self.system_state.degradation_level = new_level
            self.degradation_logger.info(
                f"System degradation level improved: {previous_level.value} -> {new_level.value}"
            )
    
    def _save_state_snapshot(self):
        """Save current system state to history"""
        # Create a copy of current state
        state_copy = SystemState(
            degradation_level=self.system_state.degradation_level,
            failed_services=self.system_state.failed_services.copy(),
            degraded_services=self.system_state.degraded_services.copy(),
            active_fallbacks=self.system_state.active_fallbacks.copy(),
            disabled_features=self.system_state.disabled_features.copy(),
            last_update=self.system_state.last_update,
            degradation_reason=self.system_state.degradation_reason
        )
        
        self.state_history.append(state_copy)
        
        # Keep only last 100 states
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]
    
    async def start_monitoring(self):
        """Start continuous degradation monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started graceful degradation monitoring")
    
    async def stop_monitoring(self):
        """Stop degradation monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped graceful degradation monitoring")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop for system degradation"""
        while self.monitoring_active:
            try:
                # Check for service status changes
                if self.health_monitor:
                    await self._check_service_status_changes()
                
                # Evaluate current degradation level
                await self._evaluate_recovery_potential()
                
                # Generate status report
                await self._generate_status_report()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in degradation monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_service_status_changes(self):
        """Check for changes in service health status"""
        if not self.health_monitor:
            return
        
        all_health = await self.health_monitor.get_all_service_health()
        
        for service_name, health_metrics in all_health.items():
            if health_metrics.status == ServiceStatus.FAILED:
                if service_name not in self.system_state.failed_services:
                    await self.handle_service_failure(service_name, Exception("Health check failed"))
            
            elif health_metrics.status == ServiceStatus.HEALTHY:
                if service_name in self.system_state.failed_services:
                    await self.handle_service_recovery(service_name)
    
    async def _generate_status_report(self):
        """Generate degradation status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "degradation_level": self.system_state.degradation_level.value,
            "degradation_reason": self.system_state.degradation_reason,
            "failed_services": list(self.system_state.failed_services),
            "degraded_services": list(self.system_state.degraded_services),
            "active_fallbacks": list(self.system_state.active_fallbacks),
            "disabled_features": list(self.system_state.disabled_features),
            "service_counts": {
                "essential": len(self.essential_services),
                "optional": len(self.optional_services),
                "background": len(self.background_services),
                "failed": len(self.system_state.failed_services),
                "degraded": len(self.system_state.degraded_services)
            }
        }
        
        # Save report to file
        report_path = Path("logs/degradation_status.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system degradation status"""
        return {
            "degradation_level": self.system_state.degradation_level.value,
            "degradation_reason": self.system_state.degradation_reason,
            "failed_services": list(self.system_state.failed_services),
            "degraded_services": list(self.system_state.degraded_services),
            "active_fallbacks": list(self.system_state.active_fallbacks),
            "disabled_features": list(self.system_state.disabled_features),
            "last_update": self.system_state.last_update.isoformat(),
            "monitoring_active": self.monitoring_active
        }
    
    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a feature is currently available"""
        return feature_name not in self.system_state.disabled_features
    
    def get_degradation_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get degradation history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            {
                "timestamp": state.last_update.isoformat(),
                "degradation_level": state.degradation_level.value,
                "degradation_reason": state.degradation_reason,
                "failed_services": list(state.failed_services),
                "disabled_features": list(state.disabled_features)
            }
            for state in self.state_history
            if state.last_update >= cutoff_time
        ]


# Global instance for easy access
_graceful_degradation_controller = None

def get_graceful_degradation_controller() -> GracefulDegradationController:
    """Get global graceful degradation controller instance"""
    global _graceful_degradation_controller
    if _graceful_degradation_controller is None:
        from .error_recovery_manager import get_error_recovery_manager
        from .service_health_monitor import get_service_health_monitor
        from .fallback_mechanisms import get_fallback_manager
        
        _graceful_degradation_controller = GracefulDegradationController(
            error_recovery_manager=get_error_recovery_manager(),
            health_monitor=get_service_health_monitor(),
            fallback_manager=get_fallback_manager()
        )
    return _graceful_degradation_controller