"""PluginManager with metrics and memory hooks."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ai_karen_engine.plugin_router import PluginRouter
from ai_karen_engine.core.memory.manager import update_memory
from ai_karen_engine.integrations.llm_utils import embed_text
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes
import time

try:
    from prometheus_client import Counter, Histogram, REGISTRY
    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional dependency
    METRICS_ENABLED = False

    class _DummyMetric:
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
    """Manage plugin execution with metrics and memory persistence."""

    def __init__(self, router: Optional[PluginRouter] = None) -> None:
        super().__init__()
        self.router = router or PluginRouter()
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
                return {"total": metric._value._value, "enabled": True}
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
                stats = {
                    "sample_count": len(samples),
                    "buckets": {}
                }
                
                for sample in samples:
                    if sample.name.endswith('_bucket'):
                        bucket_le = sample.labels.get('le', 'inf')
                        stats["buckets"][bucket_le] = sample.value
                    elif sample.name.endswith('_count'):
                        stats["total_count"] = sample.value
                    elif sample.name.endswith('_sum'):
                        stats["total_sum"] = sample.value
                
                return stats
            else:
                return {"available": False}
        except Exception:
            return {"error": "failed_to_collect"}

    async def run_plugin(
        self,
        name: str,
        params: Dict[str, Any],
        user_ctx: Dict[str, Any],
    ) -> Any:
        """Execute a plugin and record metrics/memory."""
        PLUGIN_CALLS.labels(plugin=name).inc()
        logger.info("Running plugin %s with params=%s", name, params)
        
        # Trigger pre-execution hooks with enhanced context
        pre_hook_context = {
            "plugin_name": name,
            "params": params,
            "user_context": user_ctx,
            "execution_id": f"plugin_{name}_{id(params)}",
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name, 20, __file__, 0, "", (), None
            )) if logger.handlers else None
        }
        
        await self.trigger_hook_safe(
            HookTypes.PLUGIN_EXECUTION_START,
            pre_hook_context,
            user_ctx
        )
        
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
                    "plugin_calls": PLUGIN_CALLS._value._value if hasattr(PLUGIN_CALLS, '_value') else 0,
                    "memory_writes": MEMORY_WRITES._value._value if hasattr(MEMORY_WRITES, '_value') else 0
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
                    name, 40, __file__, 0, str(ex), (), ex
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

        summary = str(result)[:200]
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
