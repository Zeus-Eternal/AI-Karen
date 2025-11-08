"""
Extension Scaling Manager

Manages horizontal scaling capabilities for extensions.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from ..models import ExtensionRecord, ExtensionManifest
from .resource_optimizer import ResourceUsage, ExtensionResourceOptimizer


class ScalingStrategy(Enum):
    """Extension scaling strategies."""
    NONE = "none"                    # No scaling
    HORIZONTAL = "horizontal"        # Scale by adding instances
    VERTICAL = "vertical"           # Scale by increasing resources
    AUTO = "auto"                   # Automatic scaling based on metrics


class ScalingTrigger(Enum):
    """Triggers for scaling actions."""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"
    CUSTOM_METRIC = "custom_metric"


@dataclass
class ScalingRule:
    """Rule for triggering scaling actions."""
    trigger: ScalingTrigger
    threshold_up: float      # Scale up when metric exceeds this
    threshold_down: float    # Scale down when metric falls below this
    cooldown_seconds: float  # Minimum time between scaling actions
    min_instances: int       # Minimum number of instances
    max_instances: int       # Maximum number of instances
    scale_up_step: int       # Number of instances to add when scaling up
    scale_down_step: int     # Number of instances to remove when scaling down


@dataclass
class ExtensionInstance:
    """Represents a running instance of an extension."""
    instance_id: str
    extension_name: str
    process_id: int
    host: str
    port: Optional[int]
    status: str  # 'starting', 'running', 'stopping', 'stopped', 'failed'
    created_at: float
    last_health_check: float
    resource_usage: Optional[ResourceUsage] = None


@dataclass
class ScalingMetrics:
    """Metrics used for scaling decisions."""
    extension_name: str
    timestamp: float
    cpu_usage: float
    memory_usage: float
    request_rate: float
    response_time: float
    queue_length: int
    active_instances: int
    custom_metrics: Dict[str, float]


@dataclass
class ScalingAction:
    """Represents a scaling action to be performed."""
    extension_name: str
    action_type: str  # 'scale_up', 'scale_down'
    target_instances: int
    reason: str
    timestamp: float


class LoadBalancer:
    """Simple load balancer for extension instances."""
    
    def __init__(self):
        self._instances: Dict[str, List[ExtensionInstance]] = {}
        self._current_index: Dict[str, int] = {}
    
    def register_instance(self, instance: ExtensionInstance) -> None:
        """Register an extension instance."""
        if instance.extension_name not in self._instances:
            self._instances[instance.extension_name] = []
            self._current_index[instance.extension_name] = 0
        
        self._instances[instance.extension_name].append(instance)
    
    def unregister_instance(self, extension_name: str, instance_id: str) -> None:
        """Unregister an extension instance."""
        if extension_name in self._instances:
            self._instances[extension_name] = [
                inst for inst in self._instances[extension_name]
                if inst.instance_id != instance_id
            ]
    
    def get_next_instance(self, extension_name: str) -> Optional[ExtensionInstance]:
        """Get the next instance using round-robin load balancing."""
        instances = self._instances.get(extension_name, [])
        if not instances:
            return None
        
        # Filter healthy instances
        healthy_instances = [
            inst for inst in instances
            if inst.status == 'running'
        ]
        
        if not healthy_instances:
            return None
        
        # Round-robin selection
        current_idx = self._current_index.get(extension_name, 0)
        instance = healthy_instances[current_idx % len(healthy_instances)]
        self._current_index[extension_name] = (current_idx + 1) % len(healthy_instances)
        
        return instance
    
    def get_all_instances(self, extension_name: str) -> List[ExtensionInstance]:
        """Get all instances for an extension."""
        return self._instances.get(extension_name, [])


class ExtensionScalingManager:
    """
    Manages horizontal scaling capabilities for extensions.
    
    Features:
    - Automatic scaling based on metrics
    - Load balancing across instances
    - Health monitoring and failover
    - Custom scaling rules
    - Resource-aware scaling decisions
    """
    
    def __init__(
        self,
        resource_optimizer: ExtensionResourceOptimizer,
        metrics_collection_interval: float = 30.0,
        scaling_evaluation_interval: float = 60.0,
        health_check_interval: float = 30.0
    ):
        self.resource_optimizer = resource_optimizer
        self.metrics_collection_interval = metrics_collection_interval
        self.scaling_evaluation_interval = scaling_evaluation_interval
        self.health_check_interval = health_check_interval
        
        self._scaling_rules: Dict[str, List[ScalingRule]] = {}
        self._extension_instances: Dict[str, List[ExtensionInstance]] = {}
        self._scaling_metrics_history: Dict[str, List[ScalingMetrics]] = {}
        self._last_scaling_action: Dict[str, float] = {}
        self._load_balancer = LoadBalancer()
        
        self._metrics_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start the scaling manager."""
        if self._running:
            return
        
        self._running = True
        self._metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self._scaling_task = asyncio.create_task(self._scaling_evaluation_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        self.logger.info("Extension scaling manager started")
    
    async def stop(self) -> None:
        """Stop the scaling manager."""
        self._running = False
        
        for task in [self._metrics_task, self._scaling_task, self._health_check_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.logger.info("Extension scaling manager stopped")
    
    async def configure_scaling(
        self,
        extension_name: str,
        strategy: ScalingStrategy,
        rules: List[ScalingRule]
    ) -> None:
        """Configure scaling strategy and rules for an extension."""
        if strategy == ScalingStrategy.NONE:
            self._scaling_rules.pop(extension_name, None)
        else:
            self._scaling_rules[extension_name] = rules
        
        self.logger.info(f"Configured scaling for {extension_name}: {strategy.value}")
    
    async def register_instance(
        self,
        extension_name: str,
        instance_id: str,
        process_id: int,
        host: str = "localhost",
        port: Optional[int] = None
    ) -> ExtensionInstance:
        """Register a new extension instance."""
        instance = ExtensionInstance(
            instance_id=instance_id,
            extension_name=extension_name,
            process_id=process_id,
            host=host,
            port=port,
            status="starting",
            created_at=time.time(),
            last_health_check=time.time()
        )
        
        if extension_name not in self._extension_instances:
            self._extension_instances[extension_name] = []
        
        self._extension_instances[extension_name].append(instance)
        self._load_balancer.register_instance(instance)
        
        self.logger.info(f"Registered instance {instance_id} for extension {extension_name}")
        return instance
    
    async def unregister_instance(
        self,
        extension_name: str,
        instance_id: str
    ) -> None:
        """Unregister an extension instance."""
        if extension_name in self._extension_instances:
            self._extension_instances[extension_name] = [
                inst for inst in self._extension_instances[extension_name]
                if inst.instance_id != instance_id
            ]
        
        self._load_balancer.unregister_instance(extension_name, instance_id)
        self.logger.info(f"Unregistered instance {instance_id} for extension {extension_name}")
    
    async def get_instance_for_request(
        self,
        extension_name: str
    ) -> Optional[ExtensionInstance]:
        """Get an available instance for handling a request."""
        return self._load_balancer.get_next_instance(extension_name)
    
    async def get_extension_instances(
        self,
        extension_name: str
    ) -> List[ExtensionInstance]:
        """Get all instances for an extension."""
        return self._extension_instances.get(extension_name, [])
    
    async def scale_extension(
        self,
        extension_name: str,
        target_instances: int,
        reason: str = "manual"
    ) -> bool:
        """Manually scale an extension to target number of instances."""
        current_instances = len(self._extension_instances.get(extension_name, []))
        
        if target_instances == current_instances:
            return True
        
        if target_instances > current_instances:
            # Scale up
            instances_to_add = target_instances - current_instances
            success = await self._scale_up(extension_name, instances_to_add, reason)
        else:
            # Scale down
            instances_to_remove = current_instances - target_instances
            success = await self._scale_down(extension_name, instances_to_remove, reason)
        
        if success:
            self._last_scaling_action[extension_name] = time.time()
        
        return success
    
    async def get_scaling_metrics(
        self,
        extension_name: str,
        time_window: Optional[float] = None
    ) -> List[ScalingMetrics]:
        """Get scaling metrics history for an extension."""
        history = self._scaling_metrics_history.get(extension_name, [])
        
        if time_window is None:
            return history
        
        cutoff_time = time.time() - time_window
        return [metrics for metrics in history if metrics.timestamp >= cutoff_time]
    
    async def _metrics_collection_loop(self) -> None:
        """Background loop for collecting scaling metrics."""
        while self._running:
            try:
                await self._collect_scaling_metrics()
                await asyncio.sleep(self.metrics_collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.metrics_collection_interval)
    
    async def _scaling_evaluation_loop(self) -> None:
        """Background loop for evaluating scaling decisions."""
        while self._running:
            try:
                await self._evaluate_scaling_decisions()
                await asyncio.sleep(self.scaling_evaluation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scaling evaluation error: {e}")
                await asyncio.sleep(self.scaling_evaluation_interval)
    
    async def _health_check_loop(self) -> None:
        """Background loop for health checking instances."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _collect_scaling_metrics(self) -> None:
        """Collect metrics for scaling decisions."""
        current_time = time.time()
        
        for extension_name in self._scaling_rules.keys():
            try:
                instances = self._extension_instances.get(extension_name, [])
                active_instances = len([i for i in instances if i.status == 'running'])
                
                # Aggregate resource usage from all instances
                total_cpu = 0.0
                total_memory = 0.0
                instance_count = 0
                
                for instance in instances:
                    if instance.resource_usage:
                        total_cpu += instance.resource_usage.cpu_percent
                        total_memory += instance.resource_usage.memory_mb
                        instance_count += 1
                
                avg_cpu = total_cpu / instance_count if instance_count > 0 else 0.0
                avg_memory = total_memory / instance_count if instance_count > 0 else 0.0
                
                # Create scaling metrics
                metrics = ScalingMetrics(
                    extension_name=extension_name,
                    timestamp=current_time,
                    cpu_usage=avg_cpu,
                    memory_usage=avg_memory,
                    request_rate=0.0,  # Would be collected from actual metrics
                    response_time=0.0,  # Would be collected from actual metrics
                    queue_length=0,     # Would be collected from actual metrics
                    active_instances=active_instances,
                    custom_metrics={}   # Would be collected from extension
                )
                
                # Store metrics history
                if extension_name not in self._scaling_metrics_history:
                    self._scaling_metrics_history[extension_name] = []
                
                history = self._scaling_metrics_history[extension_name]
                history.append(metrics)
                
                # Keep only last 1000 entries
                if len(history) > 1000:
                    history.pop(0)
                
            except Exception as e:
                self.logger.error(f"Failed to collect metrics for {extension_name}: {e}")
    
    async def _evaluate_scaling_decisions(self) -> None:
        """Evaluate whether scaling actions are needed."""
        for extension_name, rules in self._scaling_rules.items():
            try:
                # Get recent metrics
                recent_metrics = self._scaling_metrics_history.get(extension_name, [])
                if len(recent_metrics) < 3:  # Need sufficient data
                    continue
                
                latest_metrics = recent_metrics[-1]
                
                # Check each scaling rule
                for rule in rules:
                    await self._evaluate_scaling_rule(extension_name, rule, latest_metrics)
                
            except Exception as e:
                self.logger.error(f"Scaling evaluation failed for {extension_name}: {e}")
    
    async def _evaluate_scaling_rule(
        self,
        extension_name: str,
        rule: ScalingRule,
        metrics: ScalingMetrics
    ) -> None:
        """Evaluate a specific scaling rule."""
        # Check cooldown period
        last_action = self._last_scaling_action.get(extension_name, 0)
        if time.time() - last_action < rule.cooldown_seconds:
            return
        
        # Get metric value based on trigger type
        metric_value = self._get_metric_value(rule.trigger, metrics)
        
        current_instances = metrics.active_instances
        
        # Check if scaling up is needed
        if (metric_value > rule.threshold_up and 
            current_instances < rule.max_instances):
            
            target_instances = min(
                current_instances + rule.scale_up_step,
                rule.max_instances
            )
            
            reason = f"{rule.trigger.value} {metric_value:.1f} > {rule.threshold_up}"
            await self.scale_extension(extension_name, target_instances, reason)
        
        # Check if scaling down is needed
        elif (metric_value < rule.threshold_down and 
              current_instances > rule.min_instances):
            
            target_instances = max(
                current_instances - rule.scale_down_step,
                rule.min_instances
            )
            
            reason = f"{rule.trigger.value} {metric_value:.1f} < {rule.threshold_down}"
            await self.scale_extension(extension_name, target_instances, reason)
    
    def _get_metric_value(self, trigger: ScalingTrigger, metrics: ScalingMetrics) -> float:
        """Get the metric value for a scaling trigger."""
        if trigger == ScalingTrigger.CPU_USAGE:
            return metrics.cpu_usage
        elif trigger == ScalingTrigger.MEMORY_USAGE:
            return metrics.memory_usage
        elif trigger == ScalingTrigger.REQUEST_RATE:
            return metrics.request_rate
        elif trigger == ScalingTrigger.RESPONSE_TIME:
            return metrics.response_time
        elif trigger == ScalingTrigger.QUEUE_LENGTH:
            return float(metrics.queue_length)
        else:
            return 0.0
    
    async def _scale_up(
        self,
        extension_name: str,
        instances_to_add: int,
        reason: str
    ) -> bool:
        """Scale up an extension by adding instances."""
        try:
            self.logger.info(f"Scaling up {extension_name} by {instances_to_add} instances: {reason}")
            
            # In a real implementation, this would:
            # 1. Start new processes/containers
            # 2. Wait for them to be healthy
            # 3. Register them with the load balancer
            
            # For now, simulate the scaling
            for i in range(instances_to_add):
                instance_id = f"{extension_name}-{int(time.time())}-{i}"
                await self.register_instance(
                    extension_name=extension_name,
                    instance_id=instance_id,
                    process_id=0,  # Would be actual process ID
                    host="localhost"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Scale up failed for {extension_name}: {e}")
            return False
    
    async def _scale_down(
        self,
        extension_name: str,
        instances_to_remove: int,
        reason: str
    ) -> bool:
        """Scale down an extension by removing instances."""
        try:
            self.logger.info(f"Scaling down {extension_name} by {instances_to_remove} instances: {reason}")
            
            instances = self._extension_instances.get(extension_name, [])
            running_instances = [i for i in instances if i.status == 'running']
            
            # Remove oldest instances first
            instances_to_stop = sorted(
                running_instances,
                key=lambda x: x.created_at
            )[:instances_to_remove]
            
            for instance in instances_to_stop:
                await self._stop_instance(instance)
                await self.unregister_instance(extension_name, instance.instance_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Scale down failed for {extension_name}: {e}")
            return False
    
    async def _stop_instance(self, instance: ExtensionInstance) -> None:
        """Stop an extension instance."""
        try:
            instance.status = "stopping"
            
            # In a real implementation, this would:
            # 1. Send graceful shutdown signal
            # 2. Wait for graceful shutdown
            # 3. Force kill if necessary
            
            instance.status = "stopped"
            
        except Exception as e:
            self.logger.error(f"Failed to stop instance {instance.instance_id}: {e}")
            instance.status = "failed"
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all instances."""
        for extension_name, instances in self._extension_instances.items():
            for instance in instances:
                try:
                    # Simple health check - in reality would ping the instance
                    if instance.status == "starting":
                        # Simulate startup time
                        if time.time() - instance.created_at > 30:  # 30 seconds
                            instance.status = "running"
                    
                    instance.last_health_check = time.time()
                    
                    # Update resource usage
                    resource_usage = await self.resource_optimizer.get_resource_usage(
                        extension_name, time_window=60
                    )
                    if resource_usage:
                        instance.resource_usage = resource_usage[-1]
                
                except Exception as e:
                    self.logger.error(f"Health check failed for instance {instance.instance_id}: {e}")
                    instance.status = "failed"