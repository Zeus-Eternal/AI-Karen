"""PluginManager with metrics, memory hooks, and unified registry integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import time

from ai_karen_engine.plugin_router import PluginRouter
from ai_karen_engine.core.memory.manager import update_memory
from ai_karen_engine.integrations.llm_utils import embed_text
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes
from extensions.core.registry.plugin_registry import get_registry

try:
    from prometheus_client import Counter, Histogram, REGISTRY
    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional dependency
    METRICS_ENABLED = False

    class _DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def inc(self, n: int = 1) -> None:
            pass
        
        def observe(self, value: float) -> None:
            pass

    Counter = _DummyMetric  # type: ignore
    Histogram = _DummyMetric  # type: ignore

if METRICS_ENABLED:
    if "plugin_calls_total" not in REGISTRY._names_to_collectors:
        PLUGIN_CALLS = Counter(
            "plugin_calls_total",
            "Total plugin calls",
            ["plugin"],
        )
    else:  # pragma: no cover - reuse collector under reload
        PLUGIN_CALLS = REGISTRY._names_to_collectors["plugin_calls_total"]

    if "plugin_failure_rate" not in REGISTRY._names_to_collectors:
        PLUGIN_FAILURES = Counter(
            "plugin_failure_rate",
            "Plugin failures",
            ["plugin"],
        )
    else:  # pragma: no cover - reuse collector
        PLUGIN_FAILURES = REGISTRY._names_to_collectors["plugin_failure_rate"]

    if "memory_writes_total" not in REGISTRY._names_to_collectors:
        MEMORY_WRITES = Counter(
            "memory_writes_total",
            "Memory writes from plugins",
        )
    else:  # pragma: no cover - reuse collector
        MEMORY_WRITES = REGISTRY._names_to_collectors["memory_writes_total"]
    
    # Hook-specific metrics
    if "plugin_hooks_triggered_total" not in REGISTRY._names_to_collectors:
        PLUGIN_HOOKS_TRIGGERED = Counter(
            "plugin_hooks_triggered_total",
            "Total plugin hooks triggered",
            ["plugin", "hook_type", "source"],
        )
    else:  # pragma: no cover - reuse collector
        PLUGIN_HOOKS_TRIGGERED = REGISTRY._names_to_collectors["plugin_hooks_triggered_total"]
    
    if "plugin_hooks_failed_total" not in REGISTRY._names_to_collectors:
        PLUGIN_HOOKS_FAILED = Counter(
            "plugin_hooks_failed_total",
            "Failed plugin hooks",
            ["plugin", "hook_type", "error_type"],
        )
    else:  # pragma: no cover - reuse collector
        PLUGIN_HOOKS_FAILED = REGISTRY._names_to_collectors["plugin_hooks_failed_total"]
    
    if "plugin_hook_execution_duration_seconds" not in REGISTRY._names_to_collectors:
        PLUGIN_HOOK_DURATION = Histogram(
            "plugin_hook_execution_duration_seconds",
            "Plugin hook execution duration",
            ["plugin", "hook_type"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
    else:  # pragma: no cover - reuse collector
        PLUGIN_HOOK_DURATION = REGISTRY._names_to_collectors["plugin_hook_execution_duration_seconds"]
    
    if "plugin_workflow_executions_total" not in REGISTRY._names_to_collectors:
        PLUGIN_WORKFLOW_EXECUTIONS = Counter(
            "plugin_workflow_executions_total",
            "Total plugin workflow executions",
            ["workflow", "status"],
        )
    else:  # pragma: no cover - reuse collector
        PLUGIN_WORKFLOW_EXECUTIONS = REGISTRY._names_to_collectors["plugin_workflow_executions_total"]

else:  # pragma: no cover - metrics disabled
    PLUGIN_CALLS = Counter()
    PLUGIN_FAILURES = Counter()
    MEMORY_WRITES = Counter()
    PLUGIN_HOOKS_TRIGGERED = Counter()
    PLUGIN_HOOKS_FAILED = Counter()
    PLUGIN_HOOK_DURATION = Histogram()
    PLUGIN_WORKFLOW_EXECUTIONS = Counter()

logger = logging.getLogger("kari.plugin_manager")


class PluginManager(HookMixin):
    """Manage plugin execution with metrics, memory persistence, and unified registry."""

    def __init__(self, router: Optional[PluginRouter] = None) -> None:
        super().__init__()
        self.router = router or PluginRouter()
        self.registry = get_registry()  # Single source of truth for packages
        self.name = "plugin_manager"
        self._setup_hook_monitoring()
    
    def _setup_hook_monitoring(self):
        """Set up hook monitoring and metrics collection."""
        # Override the trigger_hooks method to add metrics
        original_trigger_hooks = super().trigger_hooks
        
        async def monitored_trigger_hooks(hook_type, data, user_context=None, timeout_seconds=30.0):
            plugin_name = data.get("plugin_name", "unknown")
            start_time = time.time()
            
            # Increment hook trigger counter
            PLUGIN_HOOKS_TRIGGERED.labels(
                plugin=plugin_name,
                hook_type=hook_type,
                source="plugin_manager"
            ).inc()
            
            try:
                result = await original_trigger_hooks(hook_type, data, user_context, timeout_seconds)
                
                # Record successful execution time
                execution_time = time.time() - start_time
                PLUGIN_HOOK_DURATION.labels(
                    plugin=plugin_name,
                    hook_type=hook_type
                ).observe(execution_time)
                
                return result
                
            except Exception as e:
                # Record hook failure
                PLUGIN_HOOKS_FAILED.labels(
                    plugin=plugin_name,
                    hook_type=hook_type,
                    error_type=type(e).__name__
                ).inc()
                
                # Still record execution time for failed hooks
                execution_time = time.time() - start_time
                PLUGIN_HOOK_DURATION.labels(
                    plugin=plugin_name,
                    hook_type=hook_type
                ).observe(execution_time)
                
                raise
        
        # Replace the method
        self.trigger_hooks = monitored_trigger_hooks
    
    def get_plugin_metrics(self) -> Dict[str, Any]:
        """Get comprehensive plugin metrics including hook statistics."""
        try:
            metrics = {
                "plugin_calls": self._get_metric_value(PLUGIN_CALLS),
                "plugin_failures": self._get_metric_value(PLUGIN_FAILURES),
                "memory_writes": self._get_metric_value(MEMORY_WRITES),
                "hook_metrics": {
                    "hooks_triggered": self._get_metric_value(PLUGIN_HOOKS_TRIGGERED),
                    "hooks_failed": self._get_metric_value(PLUGIN_HOOKS_FAILED),
                    "hook_duration_stats": self._get_histogram_stats(PLUGIN_HOOK_DURATION)
                },
                "workflow_metrics": {
                    "workflow_executions": self._get_metric_value(PLUGIN_WORKFLOW_EXECUTIONS)
                }
            }
            
            # Add hook statistics from parent class
            hook_stats = self.get_hook_stats()
            metrics["hook_system"] = hook_stats
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Failed to collect plugin metrics: {e}")
            return {"error": str(e)}
    
    def _get_metric_value(self, metric) -> Dict[str, Any]:
        """Extract value from Prometheus metric."""
        if not METRICS_ENABLED:
            return {"enabled": False}
        
        try:
            # For Counter metrics, get the total value
            if hasattr(metric, '_value'):
                val_obj = getattr(metric, '_value', None)
                val = getattr(val_obj, '_value', 0.0) if val_obj else 0.0
                return {"total": float(val), "enabled": True}
            elif hasattr(metric, 'collect'):
                samples = list(metric.collect())[0].samples
                return {"samples": len(samples), "total": sum(s.value for s in samples), "enabled": True}
            else:
                return {"available": False, "enabled": True}
        except Exception:
            return {"error": "failed_to_collect", "enabled": True}
    
    def _get_histogram_stats(self, histogram) -> Dict[str, Any]:
        """Extract statistics from Prometheus histogram."""
        if not METRICS_ENABLED:
            return {"enabled": False}
        
        try:
            if hasattr(histogram, 'collect'):
                samples = list(histogram.collect())[0].samples
                buckets: Dict[str, Any] = {}
                stats: Dict[str, Any] = {
                    "sample_count": len(samples),
                    "buckets": buckets
                }
                
                for sample in samples:
                    if sample.name.endswith('_bucket'):
                        bucket_le = sample.labels.get('le', 'inf')
                        buckets[bucket_le] = sample.value
                    elif sample.name.endswith('_count'):
                        stats["total_count"] = sample.value
                    elif sample.name.endswith('_sum'):
                        stats["total_sum"] = sample.value
                
                return stats
            else:
                return {"available": False}
        except Exception:
            return {"error": "failed_to_collect"}

    async def discover_extensions(self, directories: Optional[list[str]] = None) -> dict[str, Any]:
        """Discover plugins across multiple directories."""
        import os, json
        from extensions.core.registry.plugin_registry import PluginStatus
        
        if directories is None:
            directories = ["plugins", "extensions"]
            
        manifests = {}
        for directory in directories:
            if not os.path.exists(directory):
                continue
            for entry in os.listdir(directory):
                plugin_dir = os.path.join(directory, entry)
                if os.path.isdir(plugin_dir):
                    manifest_path = os.path.join(plugin_dir, "manifest.json")
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r') as f:
                                manifest_data = json.load(f)
                                # Validate Prompt-First
                                if self.registry.register(entry, manifest_data):
                                    # Try to adapt manifest structure to internal model
                                    manifests[entry] = self.registry.get_plugin(entry).manifest
                        except Exception as e:
                            logger.error(f"Failed to read manifest for {entry}: {e}")
        return manifests

    def get_extension_status(self, name: str) -> dict | None:
        """Get the status of an extension."""
        record = self.registry.get_plugin(name)
        if not record:
            return None
        return {
            "name": record.manifest.name,
            "version": record.manifest.version,
            "status": record.status.value,
            "loaded_at": record.loaded_at,
            "error_message": record.error_message,
        }

    async def load_extension(self, name: str):
        """Load an extension and initialize it."""
        from datetime import datetime
        from extensions.core.registry.plugin_registry import PluginStatus
        record = self.registry.get_plugin(name)
        if not record:
            raise ValueError(f"Plugin {name} not found")
        record.status = PluginStatus.LOADED
        record.loaded_at = datetime.utcnow()
        record.error_message = None
        return record

    async def unload_extension(self, name: str):
        """Unload an extension."""
        from extensions.core.registry.plugin_registry import PluginStatus
        record = self.registry.get_plugin(name)
        if not record:
            raise ValueError(f"Plugin {name} not found")
        record.status = PluginStatus.UNLOADED
        record.loaded_at = None

    async def reload_extension(self, name: str):
        """Reload an extension."""
        await self.unload_extension(name)
        return await self.load_extension(name)

    def get_health_summary(self) -> dict:
        """Get the overall health of the extension system."""
        plugins = self.registry.list_extensions()
        total = len(plugins)
        loaded = sum(1 for p in plugins if p.status.value == "loaded")
        error_count = sum(1 for p in plugins if p.status.value == "error")
        status = "healthy" if error_count == 0 else "degraded"
        return {
            "total_extensions": total,
            "healthy_extensions": loaded,
            "error_extensions": error_count,
            "status": status,
            "overall_status": status
        }

    async def run_plugin(
        self,
        name: str,
        params: Dict[str, Any],
        user_ctx: Dict[str, Any],
    ) -> Any:
        """Execute a plugin using the Prompt-First registry contract and record metrics/memory."""
        # 1. Validation Layer (Prompt-First)
        plugin_manifest = self.registry.get_plugin(name)
        if not plugin_manifest:
            logger.warning(f"Plugin {name} not found in unified registry. Proceeding with legacy routing, but this should be migrated.")

        PLUGIN_CALLS.labels(plugin=name).inc()
        logger.info("Running plugin %s with params=%s", name, params)
        
        # 2. Trigger pre-execution hooks with enhanced context
        timestamp = None
        if logger.handlers and getattr(logger.handlers[0], 'formatter', None):
            try:
                timestamp = logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    name, 20, __file__, 0, "", (), None, None
                ))
            except Exception:
                pass

        pre_hook_context = {
            "plugin_name": name,
            "params": params,
            "user_context": user_ctx,
            "execution_id": f"plugin_{name}_{id(params)}",
            "timestamp": timestamp
        }
        
        await self.trigger_hook_safe(
            HookTypes.PLUGIN_EXECUTION_START,
            pre_hook_context,
            user_ctx
        )
        
        # 3. Execution Layer
        try:
            result, out, err = await self.router.dispatch(
                name, params, roles=user_ctx.get("roles")
            )
            logger.info("Plugin %s result: %s", name, result)
            if out:
                logger.debug("%s stdout: %s", name, out.strip())
            if err:
                logger.debug("%s stderr: %s", name, err.strip())
                
            # Trigger post-execution hooks with comprehensive results
            post_hook_context = {
                "plugin_name": name,
                "params": params,
                "result": result,
                "stdout": out,
                "stderr": err,
                "success": True,
                "user_context": user_ctx,
                "execution_id": pre_hook_context["execution_id"],
                "execution_time_ms": 0,  # Could be calculated if needed
                "memory_usage": None,  # Could be tracked if needed
                "metrics": {
                    "plugin_calls": float(getattr(getattr(PLUGIN_CALLS, '_value', None), '_value', 0.0)),
                    "memory_writes": float(getattr(getattr(MEMORY_WRITES, '_value', None), '_value', 0.0))
                }
            }
            
            await self.trigger_hook_safe(
                HookTypes.PLUGIN_EXECUTION_END,
                post_hook_context,
                user_ctx
            )
            
        except Exception as ex:  # pragma: no cover - runtime safeguard
            PLUGIN_FAILURES.labels(plugin=name).inc()
            logger.exception("Plugin %s failed: %s", name, ex)
            
            # Trigger error hooks with detailed error information
            error_hook_context = {
                "plugin_name": name,
                "params": params,
                "error": str(ex),
                "error_type": type(ex).__name__,
                "error_traceback": logger.handlers[0].format(logger.makeRecord(
                    name, 40, __file__, 0, str(ex), (), None, None
                )) if logger.handlers else str(ex),
                "user_context": user_ctx,
                "execution_id": pre_hook_context["execution_id"],
                "recovery_suggestions": self._get_error_recovery_suggestions(ex, name)
            }
            
            await self.trigger_hook_safe(
                HookTypes.PLUGIN_ERROR,
                error_hook_context,
                user_ctx
            )
            raise

        # 4. Storage & Persistence Layer
        summary_full = str(result)
        summary = summary_full[:200] if len(summary_full) > 200 else summary_full
        embed_input = f"{name} {summary} {user_ctx}"
        try:
            embed_text(embed_input)
        except Exception:  # pragma: no cover - embedding optional
            logger.debug("Embedding failed for plugin %s", name)

        try:
            update_memory(
                user_ctx,
                name,
                {"params": params, "result": result},
                tenant_id=user_ctx.get("tenant_id"),
            )
            MEMORY_WRITES.inc()
        except Exception:  # pragma: no cover - safety
            logger.warning("Memory update failed for plugin %s", name)

        return result, out, err
    
    def _get_error_recovery_suggestions(self, error: Exception, plugin_name: str) -> list[str]:
        """Generate recovery suggestions based on error type and plugin."""
        suggestions = []
        
        if isinstance(error, FileNotFoundError):
            suggestions.append("Check if required files exist and are accessible")
            suggestions.append("Verify plugin directory structure")
        elif isinstance(error, ImportError):
            suggestions.append("Install missing dependencies")
            suggestions.append("Check Python path and module imports")
        elif isinstance(error, PermissionError):
            suggestions.append("Check user roles and permissions")
            suggestions.append("Verify plugin access requirements")
        elif "timeout" in str(error).lower():
            suggestions.append("Increase plugin execution timeout")
            suggestions.append("Optimize plugin performance")
        else:
            suggestions.append(f"Check plugin {plugin_name} documentation")
            suggestions.append("Review plugin logs for more details")
        
        return suggestions


_plugin_manager: Optional[PluginManager] = None


def create_plugin_manager(router: Optional[PluginRouter] = None) -> PluginManager:
    """Return a new :class:`PluginManager` instance."""
    return PluginManager(router=router)


def get_plugin_manager() -> PluginManager:
    """Return cached PluginManager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


__all__ = [
    "PluginManager",
    "get_plugin_manager",
    "create_plugin_manager",
    "PLUGIN_CALLS",
    "PLUGIN_FAILURES",
    "MEMORY_WRITES",
    "PLUGIN_HOOKS_TRIGGERED",
    "PLUGIN_HOOKS_FAILED",
    "PLUGIN_HOOK_DURATION",
    "PLUGIN_WORKFLOW_EXECUTIONS",
]
