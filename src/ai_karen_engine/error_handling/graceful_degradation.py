"""
Graceful Degradation System

This module provides comprehensive graceful degradation capabilities with
intelligent service level management and fallback functionality.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .error_classifier import ErrorClassification, ErrorCategory, ErrorSeverity


class DegradationLevel(Enum):
    """Levels of service degradation."""
    
    FULL = "full"                    # 100% functionality
    DEGRADED = "degraded"            # 75% functionality
    LIMITED = "limited"                # 50% functionality
    MINIMAL = "minimal"                # 25% functionality
    EMERGENCY = "emergency"            # 10% functionality
    OFFLINE = "offline"                # 0% functionality


class DegradationTrigger(Enum):
    """Triggers for degradation level changes."""
    
    ERROR_RATE = "error_rate"            # High error rate
    RESPONSE_TIME = "response_time"      # Slow response times
    RESOURCE_USAGE = "resource_usage"    # High resource usage
    EXTERNAL_FAILURE = "external_failure" # External service failure
    MANUAL = "manual"                   # Manual intervention
    SCHEDULED = "scheduled"              # Scheduled maintenance


@dataclass
class DegradationPolicy:
    """Policy for degradation behavior."""
    
    component: str
    current_level: DegradationLevel = DegradationLevel.FULL
    target_level: DegradationLevel = DegradationLevel.FULL
    triggers: List[DegradationTrigger] = field(default_factory=list)
    
    # Thresholds for automatic degradation
    error_rate_threshold: float = 0.1  # 10% error rate
    response_time_threshold: float = 5.0  # 5 seconds
    resource_usage_threshold: float = 0.8  # 80% resource usage
    
    # Recovery settings
    auto_recovery: bool = True
    recovery_check_interval: float = 60.0  # seconds
    recovery_attempts: int = 3
    
    # Fallback settings
    fallback_enabled: bool = True
    fallback_components: List[str] = field(default_factory=list)
    
    # Metadata
    last_degradation: Optional[datetime] = None
    degradation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DegradationAction:
    """Action to take during degradation."""
    
    level: DegradationLevel
    description: str
    action: Callable[[], Any]
    rollback_action: Optional[Callable[[], Any]] = None
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DegradationStrategy(ABC):
    """Base class for degradation strategies."""
    
    def __init__(self, policy: DegradationPolicy):
        self.policy = policy
    
    @abstractmethod
    async def degrade(self, target_level: DegradationLevel) -> bool:
        """Degrade to target level."""
        pass
    
    @abstractmethod
    async def recover(self, target_level: DegradationLevel) -> bool:
        """Recover to target level."""
        pass
    
    @abstractmethod
    def can_degrade_to(self, level: DegradationLevel) -> bool:
        """Check if can degrade to level."""
        pass
    
    @abstractmethod
    def can_recover_to(self, level: DegradationLevel) -> bool:
        """Check if can recover to level."""
        pass


class ComponentDegradationStrategy(DegradationStrategy):
    """Component-specific degradation strategy."""
    
    def __init__(self, policy: DegradationPolicy):
        super().__init__(policy)
        self.level_actions = self._initialize_level_actions()
    
    def _initialize_level_actions(self) -> Dict[DegradationLevel, List[DegradationAction]]:
        """Initialize actions for different degradation levels."""
        return {
            DegradationLevel.FULL: [
                DegradationAction(
                    level=DegradationLevel.FULL,
                    description="Enable full functionality",
                    action=self._enable_full_functionality,
                    priority=100
                )
            ],
            DegradationLevel.DEGRADED: [
                DegradationAction(
                    level=DegradationLevel.DEGRADED,
                    description="Enable degraded functionality (75%)",
                    action=self._enable_degraded_functionality,
                    rollback_action=self._enable_full_functionality,
                    priority=80
                )
            ],
            DegradationLevel.LIMITED: [
                DegradationAction(
                    level=DegradationLevel.LIMITED,
                    description="Enable limited functionality (50%)",
                    action=self._enable_limited_functionality,
                    rollback_action=self._enable_degraded_functionality,
                    priority=60
                )
            ],
            DegradationLevel.MINIMAL: [
                DegradationAction(
                    level=DegradationLevel.MINIMAL,
                    description="Enable minimal functionality (25%)",
                    action=self._enable_minimal_functionality,
                    rollback_action=self._enable_limited_functionality,
                    priority=40
                )
            ],
            DegradationLevel.EMERGENCY: [
                DegradationAction(
                    level=DegradationLevel.EMERGENCY,
                    description="Enable emergency functionality (10%)",
                    action=self._enable_emergency_functionality,
                    rollback_action=self._enable_minimal_functionality,
                    priority=20
                )
            ],
            DegradationLevel.OFFLINE: [
                DegradationAction(
                    level=DegradationLevel.OFFLINE,
                    description="Disable all functionality",
                    action=self._disable_all_functionality,
                    rollback_action=self._enable_emergency_functionality,
                    priority=10
                )
            ]
        }
    
    async def degrade(self, target_level: DegradationLevel) -> bool:
        """Degrade to target level."""
        if not self.can_degrade_to(target_level):
            return False
        
        actions = self.level_actions.get(target_level, [])
        actions.sort(key=lambda x: x.priority, reverse=True)
        
        success_count = 0
        for action in actions:
            try:
                if asyncio.iscoroutinefunction(action.action):
                    await action.action()
                else:
                    action.action()
                success_count += 1
            except Exception as e:
                print(f"Degradation action failed: {e}")
        
        # Update policy
        self.policy.current_level = target_level
        self.policy.last_degradation = datetime.utcnow()
        self.policy.degradation_count += 1
        
        return success_count > 0
    
    async def recover(self, target_level: DegradationLevel) -> bool:
        """Recover to target level."""
        if not self.can_recover_to(target_level):
            return False
        
        # Execute rollback actions from current level to target level
        current_actions = self.level_actions.get(self.policy.current_level, [])
        target_actions = self.level_actions.get(target_level, [])
        
        # Find rollback actions
        rollback_actions = []
        for action in current_actions:
            if action.rollback_action:
                rollback_actions.append(action.rollback_action)
        
        # Execute target level actions
        success_count = 0
        for action in rollback_actions + [a.action for a in target_actions]:
            try:
                if asyncio.iscoroutinefunction(action):
                    await action()
                else:
                    action()
                success_count += 1
            except Exception as e:
                print(f"Recovery action failed: {e}")
        
        # Update policy
        self.policy.current_level = target_level
        
        return success_count > 0
    
    def can_degrade_to(self, level: DegradationLevel) -> bool:
        """Check if can degrade to level."""
        level_order = [
            DegradationLevel.FULL,
            DegradationLevel.DEGRADED,
            DegradationLevel.LIMITED,
            DegradationLevel.MINIMAL,
            DegradationLevel.EMERGENCY,
            DegradationLevel.OFFLINE
        ]
        
        current_index = level_order.index(self.policy.current_level)
        target_index = level_order.index(level)
        
        return target_index > current_index
    
    def can_recover_to(self, level: DegradationLevel) -> bool:
        """Check if can recover to level."""
        level_order = [
            DegradationLevel.FULL,
            DegradationLevel.DEGRADED,
            DegradationLevel.LIMITED,
            DegradationLevel.MINIMAL,
            DegradationLevel.EMERGENCY,
            DegradationLevel.OFFLINE
        ]
        
        current_index = level_order.index(self.policy.current_level)
        target_index = level_order.index(level)
        
        return target_index < current_index
    
    async def _enable_full_functionality(self) -> None:
        """Enable full functionality."""
        # Component-specific implementation
        print(f"Enabling full functionality for {self.policy.component}")
    
    async def _enable_degraded_functionality(self) -> None:
        """Enable degraded functionality."""
        # Component-specific implementation
        print(f"Enabling degraded functionality for {self.policy.component}")
    
    async def _enable_limited_functionality(self) -> None:
        """Enable limited functionality."""
        # Component-specific implementation
        print(f"Enabling limited functionality for {self.policy.component}")
    
    async def _enable_minimal_functionality(self) -> None:
        """Enable minimal functionality."""
        # Component-specific implementation
        print(f"Enabling minimal functionality for {self.policy.component}")
    
    async def _enable_emergency_functionality(self) -> None:
        """Enable emergency functionality."""
        # Component-specific implementation
        print(f"Enabling emergency functionality for {self.policy.component}")
    
    async def _disable_all_functionality(self) -> None:
        """Disable all functionality."""
        # Component-specific implementation
        print(f"Disabling all functionality for {self.policy.component}")


class DegradationManager:
    """
    Comprehensive degradation manager with intelligent decision-making.
    
    Features:
    - Multiple degradation strategies
    - Automatic degradation triggers
    - Recovery mechanisms
    - Component-specific policies
    - Health monitoring
    - Fallback management
    """
    
    def __init__(self):
        self.policies: Dict[str, DegradationPolicy] = {}
        self.strategies: Dict[str, DegradationStrategy] = {}
        self.health_monitors: Dict[str, Callable] = {}
        self.global_level = DegradationLevel.FULL
        
        # Monitoring
        self.monitoring_enabled = True
        self.monitoring_interval = 30.0  # seconds
        self.monitoring_task = None
        
        # Recovery
        self.recovery_enabled = True
        self.recovery_task = None
        
        # Statistics
        self.degradation_history: List[Dict[str, Any]] = []
        self.component_levels: Dict[str, DegradationLevel] = {}
    
    def register_component(
        self,
        component: str,
        policy: DegradationPolicy,
        strategy: Optional[DegradationStrategy] = None,
        health_monitor: Optional[Callable] = None
    ) -> bool:
        """Register component for degradation management."""
        try:
            # Set component name in policy
            policy.component = component
            
            # Store policy
            self.policies[component] = policy
            
            # Create strategy if not provided
            if strategy is None:
                strategy = ComponentDegradationStrategy(policy)
            
            self.strategies[component] = strategy
            
            # Store health monitor
            if health_monitor:
                self.health_monitors[component] = health_monitor
            
            # Initialize component level
            self.component_levels[component] = policy.current_level
            
            return True
            
        except Exception as e:
            print(f"Failed to register component {component}: {e}")
            return False
    
    def unregister_component(self, component: str) -> bool:
        """Unregister component from degradation management."""
        if component in self.policies:
            del self.policies[component]
        
        if component in self.strategies:
            del self.strategies[component]
        
        if component in self.health_monitors:
            del self.health_monitors[component]
        
        if component in self.component_levels:
            del self.component_levels[component]
        
        return True
    
    async def degrade_component(
        self,
        component: str,
        target_level: DegradationLevel,
        trigger: DegradationTrigger = DegradationTrigger.MANUAL
    ) -> bool:
        """Manually degrade component to target level."""
        if component not in self.strategies:
            return False
        
        strategy = self.strategies[component]
        policy = self.policies[component]
        
        # Record degradation
        self._record_degradation(component, policy.current_level, target_level, trigger)
        
        # Execute degradation
        success = await strategy.degrade(target_level)
        
        if success:
            self.component_levels[component] = target_level
            await self._update_global_level()
        
        return success
    
    async def recover_component(
        self,
        component: str,
        target_level: DegradationLevel = DegradationLevel.FULL
    ) -> bool:
        """Recover component to target level."""
        if component not in self.strategies:
            return False
        
        strategy = self.strategies[component]
        policy = self.policies[component]
        
        # Record recovery
        self._record_degradation(component, policy.current_level, target_level, DegradationTrigger.MANUAL)
        
        # Execute recovery
        success = await strategy.recover(target_level)
        
        if success:
            self.component_levels[component] = target_level
            await self._update_global_level()
        
        return success
    
    async def check_component_health(self, component: str) -> Dict[str, Any]:
        """Check health of specific component."""
        if component not in self.health_monitors:
            return {"status": "unknown", "message": "No health monitor configured"}
        
        try:
            health_monitor = self.health_monitors[component]
            
            if asyncio.iscoroutinefunction(health_monitor):
                health_data = await health_monitor()
            else:
                health_data = health_monitor()
            
            return health_data
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {e}"
            }
    
    def get_component_level(self, component: str) -> Optional[DegradationLevel]:
        """Get current degradation level of component."""
        return self.component_levels.get(component)
    
    def get_global_level(self) -> DegradationLevel:
        """Get global degradation level."""
        return self.global_level
    
    def get_degradation_history(
        self,
        component: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get degradation history."""
        history = self.degradation_history
        
        # Filter by component
        if component:
            history = [h for h in history if h.get("component") == component]
        
        # Limit results
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get degradation statistics."""
        # Count by level
        level_counts = {}
        for level in self.component_levels.values():
            level_counts[level.value] = level_counts.get(level.value, 0) + 1
        
        # Count by component
        component_counts = {}
        for component, level in self.component_levels.items():
            component_counts[component] = level.value
        
        return {
            "global_level": self.global_level.value,
            "total_components": len(self.component_levels),
            "components_by_level": level_counts,
            "component_levels": component_counts,
            "degradation_count": len(self.degradation_history),
            "registered_components": list(self.policies.keys())
        }
    
    def start_monitoring(self) -> None:
        """Start background monitoring."""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring_enabled:
            try:
                await self._check_all_components()
                await self._attempt_auto_recovery()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _check_all_components(self) -> None:
        """Check health of all components."""
        for component in list(self.policies.keys()):
            try:
                health_data = await self.check_component_health(component)
                await self._process_health_data(component, health_data)
            except Exception as e:
                print(f"Health check failed for {component}: {e}")
    
    async def _process_health_data(self, component: str, health_data: Dict[str, Any]) -> None:
        """Process health data and trigger degradation if needed."""
        policy = self.policies[component]
        current_level = self.component_levels[component]
        
        # Check error rate
        if "error_rate" in health_data:
            error_rate = health_data["error_rate"]
            if error_rate > policy.error_rate_threshold:
                await self._trigger_auto_degradation(
                    component, DegradationTrigger.ERROR_RATE, health_data
                )
        
        # Check response time
        if "response_time" in health_data:
            response_time = health_data["response_time"]
            if response_time > policy.response_time_threshold:
                await self._trigger_auto_degradation(
                    component, DegradationTrigger.RESPONSE_TIME, health_data
                )
        
        # Check resource usage
        if "resource_usage" in health_data:
            resource_usage = health_data["resource_usage"]
            if resource_usage > policy.resource_usage_threshold:
                await self._trigger_auto_degradation(
                    component, DegradationTrigger.RESOURCE_USAGE, health_data
                )
        
        # Check external failures
        if "external_failure" in health_data and health_data["external_failure"]:
            await self._trigger_auto_degradation(
                component, DegradationTrigger.EXTERNAL_FAILURE, health_data
            )
    
    async def _trigger_auto_degradation(
        self,
        component: str,
        trigger: DegradationTrigger,
        health_data: Dict[str, Any]
    ) -> None:
        """Trigger automatic degradation."""
        policy = self.policies[component]
        current_level = self.component_levels[component]
        
        # Determine target level based on trigger
        target_level = self._calculate_target_level(component, trigger, health_data)
        
        if target_level != current_level:
            await self.degrade_component(component, target_level, trigger)
    
    def _calculate_target_level(
        self,
        component: str,
        trigger: DegradationTrigger,
        health_data: Dict[str, Any]
    ) -> DegradationLevel:
        """Calculate target degradation level based on trigger."""
        policy = self.policies[component]
        current_level = self.component_levels[component]
        
        # Simple degradation logic - can be made more sophisticated
        if trigger == DegradationTrigger.ERROR_RATE:
            error_rate = health_data.get("error_rate", 0)
            if error_rate > 0.2:  # 20% error rate
                return DegradationLevel.EMERGENCY
            elif error_rate > 0.1:  # 10% error rate
                return DegradationLevel.MINIMAL
            elif error_rate > 0.05:  # 5% error rate
                return DegradationLevel.LIMITED
            else:
                return DegradationLevel.DEGRADED
        
        elif trigger == DegradationTrigger.RESPONSE_TIME:
            response_time = health_data.get("response_time", 0)
            if response_time > 10.0:  # 10 seconds
                return DegradationLevel.EMERGENCY
            elif response_time > 5.0:  # 5 seconds
                return DegradationLevel.MINIMAL
            elif response_time > 2.0:  # 2 seconds
                return DegradationLevel.LIMITED
            else:
                return DegradationLevel.DEGRADED
        
        elif trigger == DegradationTrigger.RESOURCE_USAGE:
            resource_usage = health_data.get("resource_usage", 0)
            if resource_usage > 0.95:  # 95% usage
                return DegradationLevel.EMERGENCY
            elif resource_usage > 0.8:  # 80% usage
                return DegradationLevel.MINIMAL
            elif resource_usage > 0.6:  # 60% usage
                return DegradationLevel.LIMITED
            else:
                return DegradationLevel.DEGRADED
        
        elif trigger == DegradationTrigger.EXTERNAL_FAILURE:
            return DegradationLevel.MINIMAL
        
        # Default: no change
        return current_level
    
    async def _attempt_auto_recovery(self) -> None:
        """Attempt automatic recovery for degraded components."""
        if not self.recovery_enabled:
            return
        
        for component, policy in self.policies.items():
            if not policy.auto_recovery:
                continue
            
            current_level = self.component_levels[component]
            if current_level == DegradationLevel.FULL:
                continue
            
            # Check if enough time has passed since degradation
            if policy.last_degradation:
                time_since = (datetime.utcnow() - policy.last_degradation).total_seconds()
                if time_since < policy.recovery_check_interval:
                    continue
            
            # Check health for recovery possibility
            health_data = await self.check_component_health(component)
            if health_data.get("status") == "healthy":
                await self.recover_component(component)
    
    async def _update_global_level(self) -> None:
        """Update global degradation level based on components."""
        if not self.component_levels:
            return
        
        # Find the lowest level (most degraded)
        level_order = [
            DegradationLevel.FULL,
            DegradationLevel.DEGRADED,
            DegradationLevel.LIMITED,
            DegradationLevel.MINIMAL,
            DegradationLevel.EMERGENCY,
            DegradationLevel.OFFLINE
        ]
        
        lowest_index = 0
        for level in self.component_levels.values():
            index = level_order.index(level)
            lowest_index = max(lowest_index, index)
        
        self.global_level = level_order[lowest_index]
    
    def _record_degradation(
        self,
        component: str,
        from_level: DegradationLevel,
        to_level: DegradationLevel,
        trigger: DegradationTrigger
    ) -> None:
        """Record degradation event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "component": component,
            "from_level": from_level.value,
            "to_level": to_level.value,
            "trigger": trigger.value,
            "policy": self.policies[component].__dict__
        }
        
        self.degradation_history.append(event)
        
        # Maintain history size
        if len(self.degradation_history) > 10000:
            self.degradation_history = self.degradation_history[-5000:]


# Global degradation manager instance
degradation_manager = DegradationManager()