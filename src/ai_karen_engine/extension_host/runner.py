"""
Extension Runner - Executes extensions in the proper order with error isolation.

This module handles the execution of extensions for specific hook points,
including error isolation, timeout handling, and result aggregation.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .base import ExtensionBase, HookPoint, HookContext
from .errors import (
    ExtensionExecutionError,
    ExtensionTimeoutError,
    ExtensionPermissionError,
    ExtensionHookError
)
from .registry import ExtensionRegistry

logger = logging.getLogger(__name__)


class ExtensionRunner:
    """
    Executes extensions for specific hook points.
    
    Handles:
    - Execution of extensions in the proper order
    - Error isolation (one extension cannot crash others)
    - Timeout handling for slow extensions
    - Permission and RBAC checking
    - Aggregation of results from multiple extensions
    - Comprehensive metrics and observability
    """
    
    def __init__(self,
                 registry: ExtensionRegistry,
                 default_timeout: float = 30.0):
        """
        Initialize the extension runner.
        
        Args:
            registry: Extension registry to get extensions from
            default_timeout: Default timeout for extension execution in seconds
        """
        self.registry = registry
        self.default_timeout = default_timeout
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
        self._metrics_enabled = True
        self._prometheus_metrics = {}
        self._initialize_metrics()
    
    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metrics for extension execution."""
        try:
            from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
            
            # Create a custom registry for this runner instance to avoid conflicts
            self._metrics_registry = CollectorRegistry()
            
            # Create metrics if Prometheus is available
            self._prometheus_metrics = {
                'hook_execution_count': Counter(
                    'kari_extensions_hook_execution_count',
                    'Number of times a hook point has been executed',
                    ['hook_point'],
                    registry=self._metrics_registry
                ),
                'hook_execution_duration': Histogram(
                    'kari_extensions_hook_execution_duration_seconds',
                    'Time spent executing hook points',
                    ['hook_point'],
                    registry=self._metrics_registry
                ),
                'extension_execution_count': Counter(
                    'kari_extensions_execution_count',
                    'Number of times an extension has been executed',
                    ['extension_name', 'hook_point'],
                    registry=self._metrics_registry
                ),
                'extension_execution_duration': Histogram(
                    'kari_extensions_execution_duration_seconds',
                    'Time spent executing extensions',
                    ['extension_name', 'hook_point'],
                    registry=self._metrics_registry
                ),
                'extension_errors': Counter(
                    'kari_extensions_errors_total',
                    'Number of errors in extension execution',
                    ['extension_name', 'hook_point', 'error_type'],
                    registry=self._metrics_registry
                ),
                'active_extensions': Gauge(
                    'kari_extensions_active',
                    'Number of currently active extensions',
                    registry=self._metrics_registry
                ),
                'extension_timeout_count': Counter(
                    'kari_extensions_timeouts_total',
                    'Number of extension timeouts',
                    ['extension_name', 'hook_point'],
                    registry=self._metrics_registry
                )
            }
            logger.info("Prometheus metrics initialized for extension execution")
        except ImportError:
            # Prometheus not available, metrics will be stored in memory only
            logger.warning("Prometheus not available, metrics will be stored in memory only")
            self._prometheus_metrics = {}
            self._metrics_registry = None
    
    async def execute_hook(self, 
                          hook_point: HookPoint, 
                          context: HookContext,
                          user_role: Optional[str] = None,
                          timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute all extensions that implement a specific hook point.
        
        Args:
            hook_point: The hook point to execute
            context: The hook context containing data and user context
            user_role: The role of the current user (for RBAC checks)
            timeout: Optional timeout for extension execution
            
        Returns:
            Dictionary containing results from all extensions
            
        Raises:
            ExtensionExecutionError: If there's an error executing the hook
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        # Get extensions for this hook point
        extensions = self.registry.get_extensions_for_hook(hook_point)
        
        if not extensions:
            logger.debug(f"No extensions found for hook point: {hook_point}")
            return {}
        
        logger.info(f"Executing {len(extensions)} extensions for hook point: {hook_point}")
        
        # Update Prometheus metrics for hook execution count
        if 'hook_execution_count' in self._prometheus_metrics:
            self._prometheus_metrics['hook_execution_count'].labels(hook_point=hook_point.value).inc()
        
        # Update active extensions gauge
        if 'active_extensions' in self._prometheus_metrics:
            self._prometheus_metrics['active_extensions'].set(len(extensions))
        
        # Execute extensions in parallel
        tasks = []
        extension_start_times = {}
        
        for extension in extensions:
            # Check if extension is enabled
            if not extension.enabled:
                logger.debug(f"Skipping disabled extension: {extension.manifest.name}")
                continue
                
            # Check RBAC permissions
            if not self._check_rbac_permissions(extension, user_role):
                logger.warning(f"Extension {extension.manifest.name} not allowed for role: {user_role}")
                continue
                
            # Record start time for this extension
            extension_start_times[extension.manifest.name] = time.time()
                
            # Create task for this extension
            task = self._execute_extension_with_timeout(
                extension, hook_point, context, timeout
            )
            tasks.append((extension.manifest.name, task))
        
        # Wait for all tasks to complete
        results = {}
        for extension_name, task in tasks:
            extension_start = extension_start_times.get(extension_name, start_time)
            try:
                result = await task
                results[extension_name] = result
                
                # Update Prometheus metrics for successful extension execution
                if 'extension_execution_count' in self._prometheus_metrics:
                    self._prometheus_metrics['extension_execution_count'].labels(
                        extension_name=extension_name,
                        hook_point=hook_point.value
                    ).inc()
                
                # Update execution duration histogram
                if 'extension_execution_duration' in self._prometheus_metrics:
                    execution_duration = time.time() - extension_start
                    self._prometheus_metrics['extension_execution_duration'].labels(
                        extension_name=extension_name,
                        hook_point=hook_point.value
                    ).observe(execution_duration)
                    
            except asyncio.TimeoutError as e:
                logger.error(f"Timeout executing extension {extension_name}: {e}")
                
                # Update timeout counter
                if 'extension_timeout_count' in self._prometheus_metrics:
                    self._prometheus_metrics['extension_timeout_count'].labels(
                        extension_name=extension_name,
                        hook_point=hook_point.value
                    ).inc()
                
                # Update error counter
                if 'extension_errors' in self._prometheus_metrics:
                    self._prometheus_metrics['extension_errors'].labels(
                        extension_name=extension_name,
                        hook_point=hook_point.value,
                        error_type='timeout'
                    ).inc()
                    
            except Exception as e:
                logger.error(f"Error executing extension {extension_name}: {e}")
                
                # Update error counter
                if 'extension_errors' in self._prometheus_metrics:
                    error_type = type(e).__name__
                    self._prometheus_metrics['extension_errors'].labels(
                        extension_name=extension_name,
                        hook_point=hook_point.value,
                        error_type=error_type
                    ).inc()
                # Continue with other extensions even if one fails
        
        # Update execution stats
        execution_time = time.time() - start_time
        self._update_execution_stats(hook_point, extensions, execution_time, results)
        
        # Update hook execution duration histogram
        if 'hook_execution_duration' in self._prometheus_metrics:
            self._prometheus_metrics['hook_execution_duration'].labels(hook_point=hook_point.value).observe(execution_time)
        
        # Reset active extensions gauge
        if 'active_extensions' in self._prometheus_metrics:
            self._prometheus_metrics['active_extensions'].set(0)
        
        return results
    
    async def _execute_extension_with_timeout(self,
                                            extension: ExtensionBase,
                                            hook_point: HookPoint,
                                            context: HookContext,
                                            timeout: float) -> Dict[str, Any]:
        """
        Execute a single extension with timeout handling.
        
        Args:
            extension: The extension to execute
            hook_point: The hook point being executed
            context: The hook context
            timeout: Timeout in seconds
            
        Returns:
            Dictionary containing the result of the extension
            
        Raises:
            ExtensionTimeoutError: If the extension times out
            ExtensionExecutionError: If there's an error executing the extension
        """
        try:
            # Use asyncio.wait_for to handle timeout
            result = await asyncio.wait_for(
                self._execute_extension_safely(extension, hook_point, context),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            raise ExtensionTimeoutError(
                f"Extension {extension.manifest.name} timed out after {timeout} seconds",
                timeout_seconds=timeout
            )
        except Exception as e:
            if isinstance(e, (ExtensionTimeoutError, ExtensionExecutionError)):
                raise
            raise ExtensionExecutionError(
                f"Error executing extension {extension.manifest.name}: {str(e)}",
                hook_point=hook_point.value
            ) from e
    
    async def _execute_extension_safely(self,
                                        extension: ExtensionBase,
                                        hook_point: HookPoint,
                                        context: HookContext) -> Dict[str, Any]:
        """
        Execute a single extension with error isolation.
        
        Args:
            extension: The extension to execute
            hook_point: The hook point being executed
            context: The hook context
            
        Returns:
            Dictionary containing the result of the extension
            
        Raises:
            ExtensionExecutionError: If there's an error executing the extension
        """
        try:
            # Check if extension is initialized
            if not extension.is_initialized():
                logger.warning(f"Extension {extension.manifest.name} is not initialized, initializing now")
                await extension._initialize()
            
            # Check if extension supports this hook point
            if not extension.supports_hook_point(hook_point):
                logger.warning(f"Extension {extension.manifest.name} does not support hook point: {hook_point}")
                return {"error": "Extension does not support this hook point"}
            
            # Execute the hook
            logger.debug(f"Executing hook {hook_point} in extension {extension.manifest.name}")
            result = await extension.execute_hook(hook_point, context)
            
            # Validate result
            if not isinstance(result, dict):
                logger.warning(f"Extension {extension.manifest.name} returned non-dict result: {type(result)}")
                result = {"data": result}
            
            return result
            
        except Exception as e:
            if isinstance(e, ExtensionExecutionError):
                raise
            raise ExtensionHookError(
                f"Error in hook {hook_point} for extension {extension.manifest.name}: {str(e)}",
                hook_name=hook_point.value
            ) from e
    
    def _check_rbac_permissions(self, 
                               extension: ExtensionBase, 
                               user_role: Optional[str]) -> bool:
        """
        Check if an extension is allowed for the given user role.
        
        Args:
            extension: The extension to check
            user_role: The role of the current user
            
        Returns:
            True if allowed, False otherwise
        """
        if user_role is None:
            # If no role specified, only allow extensions that allow all roles
            return "guest" in [role.value for role in extension.manifest.rbac.allowed_roles]
        
        # Check if the user's role is in the allowed roles
        for role in extension.manifest.rbac.allowed_roles:
            if role.value == user_role:
                return True
        
        return False
    
    def _update_execution_stats(self,
                               hook_point: HookPoint,
                               extensions: List[ExtensionBase],
                               execution_time: float,
                               results: Dict[str, Any]) -> None:
        """
        Update execution statistics for a hook point.
        
        Args:
            hook_point: The hook point that was executed
            extensions: List of extensions that were executed
            execution_time: Total execution time
            results: Results from the extensions
        """
        hook_name = hook_point.value
        
        if hook_name not in self._execution_stats:
            self._execution_stats[hook_name] = {
                "execution_count": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "extension_execution_count": {},
                "extension_errors": {}
            }
        
        stats = self._execution_stats[hook_name]
        stats["execution_count"] += 1
        stats["total_execution_time"] += execution_time
        stats["average_execution_time"] = stats["total_execution_time"] / stats["execution_count"]
        
        # Update per-extension stats
        for extension in extensions:
            ext_name = extension.manifest.name
            if ext_name not in stats["extension_execution_count"]:
                stats["extension_execution_count"][ext_name] = 0
                stats["extension_errors"][ext_name] = 0
            
            stats["extension_execution_count"][ext_name] += 1
            
            # Check if extension had an error
            if ext_name in results and "error" in results[ext_name]:
                stats["extension_errors"][ext_name] += 1
    
    def get_execution_stats(self, hook_point: Optional[HookPoint] = None) -> Dict[str, Any]:
        """
        Get execution statistics for hook points.
        
        Args:
            hook_point: Optional hook point to get stats for
            
        Returns:
            Dictionary containing execution statistics
        """
        if hook_point:
            return self._execution_stats.get(hook_point.value, {})
        return self._execution_stats
    
    def get_prometheus_metrics(self) -> Dict[str, Any]:
        """
        Get Prometheus metrics for extension execution.
        
        Returns:
            Dictionary containing Prometheus metrics
        """
        if not self._prometheus_metrics:
            return {"status": "Prometheus metrics not available"}
            
        metrics = {}
        for metric_name, metric in self._prometheus_metrics.items():
            try:
                # Get all samples for the metric
                samples = []
                for sample in metric.collect()[0].samples:
                    samples.append({
                        "name": sample.name,
                        "labels": dict(sample.labels),
                        "value": sample.value
                    })
                metrics[metric_name] = samples
            except Exception as e:
                logger.error(f"Error collecting Prometheus metric {metric_name}: {e}")
                metrics[metric_name] = {"error": str(e)}
                
        return metrics
    
    def get_extension_metrics(self, extension_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific extension or all extensions.
        
        Args:
            extension_name: Optional extension name to get metrics for
            
        Returns:
            Dictionary containing extension metrics
        """
        if not self._prometheus_metrics:
            return {"status": "Prometheus metrics not available"}
            
        metrics = {}
        
        # Collect metrics from execution stats
        for hook_name, hook_stats in self._execution_stats.items():
            if extension_name:
                if extension_name in hook_stats.get("extension_execution_count", {}):
                    metrics[hook_name] = {
                        "execution_count": hook_stats["extension_execution_count"].get(extension_name, 0),
                        "error_count": hook_stats["extension_errors"].get(extension_name, 0)
                    }
            else:
                metrics[hook_name] = hook_stats.get("extension_execution_count", {})
                
        # If Prometheus metrics are available, add them
        if self._prometheus_metrics:
            prometheus_metrics = self.get_prometheus_metrics()
            if extension_name:
                # Filter metrics for the specific extension
                filtered_metrics = {}
                for metric_name, samples in prometheus_metrics.items():
                    if metric_name == "active_extensions":
                        continue
                        
                    filtered_samples = [
                        sample for sample in samples
                        if sample.get("labels", {}).get("extension_name") == extension_name
                    ]
                    if filtered_samples:
                        filtered_metrics[metric_name] = filtered_samples
                        
                metrics["prometheus"] = filtered_metrics
            else:
                metrics["prometheus"] = prometheus_metrics
                
        return metrics
    
    def get_hook_metrics(self, hook_point: HookPoint) -> Dict[str, Any]:
        """
        Get metrics for a specific hook point.
        
        Args:
            hook_point: The hook point to get metrics for
            
        Returns:
            Dictionary containing hook point metrics
        """
        hook_name = hook_point.value
        
        # Get execution stats for this hook
        execution_stats = self._execution_stats.get(hook_name, {})
        
        metrics = {
            "execution_count": execution_stats.get("execution_count", 0),
            "total_execution_time": execution_stats.get("total_execution_time", 0.0),
            "average_execution_time": execution_stats.get("average_execution_time", 0.0),
            "extensions": execution_stats.get("extension_execution_count", {}),
            "errors": execution_stats.get("extension_errors", {})
        }
        
        # Add Prometheus metrics if available
        if self._prometheus_metrics:
            prometheus_metrics = self.get_prometheus_metrics()
            hook_prometheus_metrics = {}
            
            for metric_name, samples in prometheus_metrics.items():
                if metric_name == "active_extensions":
                    continue
                    
                # Filter samples for this hook point
                filtered_samples = [
                    sample for sample in samples
                    if sample.get("labels", {}).get("hook_point") == hook_name
                ]
                if filtered_samples:
                    hook_prometheus_metrics[metric_name] = filtered_samples
                    
            metrics["prometheus"] = hook_prometheus_metrics
            
        return metrics
    
    def reset_execution_stats(self) -> None:
        """Reset all execution statistics."""
        self._execution_stats = {}