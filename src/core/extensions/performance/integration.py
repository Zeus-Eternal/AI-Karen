"""
Performance Integration Module

Integrates all performance optimization components with the extension system.
"""

import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from ..manager import ExtensionManager
from ..models import ExtensionManifest, ExtensionRecord
from .cache_manager import ExtensionCacheManager
from .lazy_loader import ExtensionLazyLoader, LoadingStrategy
from .resource_optimizer import ExtensionResourceOptimizer, ResourceLimits
from .scaling_manager import ExtensionScalingManager, ScalingStrategy, ScalingRule, ScalingTrigger
from .performance_monitor import ExtensionPerformanceMonitor


class PerformanceIntegration:
    """
    Integrates performance optimization components with the extension system.
    
    This class provides a unified interface for all performance-related functionality
    and ensures proper coordination between different performance components.
    """
    
    def __init__(
        self,
        extension_root: Path,
        cache_size_mb: int = 256,
        max_concurrent_loads: int = 5,
        enable_scaling: bool = True,
        enable_monitoring: bool = True
    ):
        self.extension_root = extension_root
        self.enable_scaling = enable_scaling
        self.enable_monitoring = enable_monitoring
        
        # Initialize performance components
        self.cache_manager = ExtensionCacheManager(max_size_mb=cache_size_mb)
        self.lazy_loader = ExtensionLazyLoader(
            extension_root=extension_root,
            cache_manager=self.cache_manager,
            max_concurrent_loads=max_concurrent_loads
        )
        self.resource_optimizer = ExtensionResourceOptimizer()
        
        if enable_scaling:
            self.scaling_manager = ExtensionScalingManager(
                resource_optimizer=self.resource_optimizer
            )
        else:
            self.scaling_manager = None
        
        if enable_monitoring:
            self.performance_monitor = ExtensionPerformanceMonitor(
                cache_manager=self.cache_manager,
                resource_optimizer=self.resource_optimizer,
                scaling_manager=self.scaling_manager or self._create_dummy_scaling_manager()
            )
        else:
            self.performance_monitor = None
        
        self._started = False
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start all performance components."""
        if self._started:
            return
        
        self.logger.info("Starting extension performance integration")
        
        # Start components in order
        await self.cache_manager.start()
        await self.resource_optimizer.start()
        
        if self.scaling_manager:
            await self.scaling_manager.start()
        
        if self.performance_monitor:
            await self.performance_monitor.start()
        
        self._started = True
        self.logger.info("Extension performance integration started")
    
    async def stop(self) -> None:
        """Stop all performance components."""
        if not self._started:
            return
        
        self.logger.info("Stopping extension performance integration")
        
        # Stop components in reverse order
        if self.performance_monitor:
            await self.performance_monitor.stop()
        
        if self.scaling_manager:
            await self.scaling_manager.stop()
        
        await self.resource_optimizer.stop()
        await self.cache_manager.stop()
        await self.lazy_loader.shutdown()
        
        self._started = False
        self.logger.info("Extension performance integration stopped")
    
    async def configure_extension_performance(
        self,
        extension_name: str,
        manifest: ExtensionManifest,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Configure performance settings for an extension."""
        config = config or {}
        
        # Configure loading strategy
        loading_strategy = LoadingStrategy(config.get('loading_strategy', 'lazy'))
        loading_priority = config.get('loading_priority', 100)
        loading_dependencies = config.get('loading_dependencies', [])
        
        await self.lazy_loader.configure_loading_strategy(
            extension_name=extension_name,
            strategy=loading_strategy,
            priority=loading_priority,
            dependencies=loading_dependencies
        )
        
        # Configure resource limits
        resource_limits = config.get('resource_limits', {})
        if resource_limits:
            limits = ResourceLimits(
                max_memory_mb=resource_limits.get('max_memory_mb'),
                max_cpu_percent=resource_limits.get('max_cpu_percent'),
                max_disk_io_mb_per_sec=resource_limits.get('max_disk_io_mb_per_sec'),
                max_network_io_mb_per_sec=resource_limits.get('max_network_io_mb_per_sec'),
                max_file_handles=resource_limits.get('max_file_handles'),
                max_threads=resource_limits.get('max_threads')
            )
            
            # Resource limits would be applied when the extension is registered
            # with the resource optimizer (when it starts running)
        
        # Configure scaling
        if self.scaling_manager:
            scaling_config = config.get('scaling', {})
            if scaling_config.get('enabled', False):
                strategy = ScalingStrategy(scaling_config.get('strategy', 'auto'))
                rules = []
                
                for rule_config in scaling_config.get('rules', []):
                    rule = ScalingRule(
                        trigger=ScalingTrigger(rule_config['trigger']),
                        threshold_up=rule_config['threshold_up'],
                        threshold_down=rule_config['threshold_down'],
                        cooldown_seconds=rule_config.get('cooldown_seconds', 300),
                        min_instances=rule_config.get('min_instances', 1),
                        max_instances=rule_config.get('max_instances', 5),
                        scale_up_step=rule_config.get('scale_up_step', 1),
                        scale_down_step=rule_config.get('scale_down_step', 1)
                    )
                    rules.append(rule)
                
                await self.scaling_manager.configure_scaling(
                    extension_name=extension_name,
                    strategy=strategy,
                    rules=rules
                )
        
        # Configure monitoring
        if self.performance_monitor:
            monitoring_config = config.get('monitoring', {})
            thresholds = monitoring_config.get('thresholds', {})
            
            if thresholds:
                await self.performance_monitor.configure_thresholds(
                    extension_name=extension_name,
                    thresholds=thresholds
                )
        
        self.logger.info(f"Configured performance settings for extension {extension_name}")
    
    async def load_extensions_optimized(
        self,
        manifests: Dict[str, ExtensionManifest]
    ) -> Dict[str, Any]:
        """Load extensions using optimized loading strategies."""
        self.logger.info(f"Loading {len(manifests)} extensions with performance optimization")
        
        # Warm cache with extension manifests
        await self.cache_manager.warm_cache(None, list(manifests.keys()))
        
        # Load extensions using lazy loading
        loaded_extensions = await self.lazy_loader.load_extensions(manifests)
        
        self.logger.info(f"Loaded {len(loaded_extensions)} extensions with optimization")
        return loaded_extensions
    
    async def register_extension_instance(
        self,
        extension_name: str,
        process_id: int,
        resource_limits: Optional[ResourceLimits] = None
    ) -> None:
        """Register an extension instance for performance monitoring."""
        # Register with resource optimizer
        await self.resource_optimizer.register_extension(
            extension_name=extension_name,
            process_id=process_id,
            limits=resource_limits
        )
        
        # Register with scaling manager if enabled
        if self.scaling_manager:
            instance_id = f"{extension_name}-{process_id}"
            await self.scaling_manager.register_instance(
                extension_name=extension_name,
                instance_id=instance_id,
                process_id=process_id
            )
        
        self.logger.info(f"Registered extension instance {extension_name} (PID: {process_id})")
    
    async def unregister_extension_instance(
        self,
        extension_name: str,
        process_id: int
    ) -> None:
        """Unregister an extension instance from performance monitoring."""
        # Unregister from resource optimizer
        await self.resource_optimizer.unregister_extension(extension_name)
        
        # Unregister from scaling manager if enabled
        if self.scaling_manager:
            instance_id = f"{extension_name}-{process_id}"
            await self.scaling_manager.unregister_instance(extension_name, instance_id)
        
        self.logger.info(f"Unregistered extension instance {extension_name} (PID: {process_id})")
    
    async def get_performance_status(self) -> Dict[str, Any]:
        """Get overall performance status of the extension system."""
        status = {
            'cache_stats': await self.cache_manager.get_stats(),
            'system_resources': await self.resource_optimizer.get_system_resource_usage(),
            'loading_metrics': await self.lazy_loader.get_loading_metrics()
        }
        
        if self.scaling_manager:
            # Get scaling status for all extensions
            status['scaling_status'] = {}
            # This would be implemented to get status from scaling manager
        
        if self.performance_monitor:
            status['active_alerts'] = await self.performance_monitor.get_active_alerts()
        
        return status
    
    async def optimize_extension(self, extension_name: str) -> Dict[str, Any]:
        """Perform optimization for a specific extension."""
        results = {}
        
        # Memory optimization
        memory_optimized = await self.resource_optimizer.optimize_extension_memory(extension_name)
        results['memory_optimized'] = memory_optimized
        
        # CPU optimization
        cpu_optimized = await self.resource_optimizer.optimize_extension_cpu(extension_name)
        results['cpu_optimized'] = cpu_optimized
        
        # Get optimization recommendations
        recommendations = await self.resource_optimizer.get_optimization_recommendations()
        extension_recommendations = [
            rec for rec in recommendations 
            if rec.extension_name == extension_name
        ]
        results['recommendations'] = extension_recommendations
        
        self.logger.info(f"Optimization completed for {extension_name}: {results}")
        return results
    
    async def scale_extension(
        self,
        extension_name: str,
        target_instances: int,
        reason: str = "manual"
    ) -> bool:
        """Scale an extension to the target number of instances."""
        if not self.scaling_manager:
            self.logger.warning("Scaling manager not enabled")
            return False
        
        return await self.scaling_manager.scale_extension(
            extension_name=extension_name,
            target_instances=target_instances,
            reason=reason
        )
    
    async def get_extension_performance_summary(
        self,
        extension_name: str,
        time_period_hours: float = 24.0
    ) -> Optional[Dict[str, Any]]:
        """Get performance summary for an extension."""
        if not self.performance_monitor:
            return None
        
        summary = await self.performance_monitor.get_performance_summary(
            extension_name=extension_name,
            time_period_hours=time_period_hours
        )
        
        return summary.__dict__ if summary else None
    
    def _create_dummy_scaling_manager(self):
        """Create a dummy scaling manager for when scaling is disabled."""
        class DummyScalingManager:
            async def get_scaling_metrics(self, extension_name: str, time_window: Optional[float] = None):
                return []
        
        return DummyScalingManager()


async def integrate_with_extension_manager(
    extension_manager: ExtensionManager,
    performance_integration: PerformanceIntegration
) -> None:
    """Integrate performance optimization with the extension manager."""
    
    # Replace the extension manager's loading mechanism with optimized loading
    original_load_extensions = extension_manager.load_extensions
    
    async def optimized_load_extensions(manifests: Dict[str, ExtensionManifest]):
        """Optimized extension loading wrapper."""
        return await performance_integration.load_extensions_optimized(manifests)
    
    extension_manager.load_extensions = optimized_load_extensions
    
    # Hook into extension lifecycle events
    original_register_extension = extension_manager.register_extension
    
    async def register_extension_with_performance(extension_record: ExtensionRecord):
        """Register extension with performance monitoring."""
        result = await original_register_extension(extension_record)
        
        # Register with performance system if extension is running
        if hasattr(extension_record, 'process_id') and extension_record.process_id:
            await performance_integration.register_extension_instance(
                extension_name=extension_record.name,
                process_id=extension_record.process_id
            )
        
        return result
    
    extension_manager.register_extension = register_extension_with_performance
    
    logging.getLogger(__name__).info("Performance integration configured with extension manager")