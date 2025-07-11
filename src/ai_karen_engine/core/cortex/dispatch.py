"""
Kari CORTEX Dispatch Core
- Central intent/command dispatcher for Kari AI
- Local-first, plugin/routing/intent aware
- Handles: prediction, memory, action, plugins, error capture
- 100% backend: no UI, no Streamlit, no mercy
"""

from typing import Any, Dict, Optional, List
from ai_karen_engine.core.cortex.intent import resolve_intent
from ai_karen_engine.core.plugin_registry import plugin_registry, execute_plugin
from ai_karen_engine.core.memory.manager import recall_context, update_memory
from ai_karen_engine.core.cortex.errors import CortexDispatchError, UnsupportedIntentError
from ai_karen_engine.core.predictors import predictor_registry, run_predictor

def dispatch(
    user_ctx: Dict[str, Any],
    query: str,
    mode: str = "auto",
    context: Optional[Dict[str, Any]] = None,
    memory_enabled: bool = True,
    plugin_enabled: bool = True,
    predictor_enabled: bool = True,
    trace: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    CORTEX unified entrypoint: routes query to correct module (plugin, ML, memory, etc).
    Args:
        user_ctx: User/session context.
        query: User's raw request or message.
        mode: 'auto' | 'plugin' | 'predictor' | 'memory' | 'manual'
        context: Optional preloaded context for dispatch.
        memory_enabled: If True, recalls context and writes to memory.
        plugin_enabled: If True, allows plugin execution.
        predictor_enabled: If True, allows ML/LLM predictors.
        trace: Optional trace/debug output (appends steps).
    Returns:
        Dict with result, intent, and metadata.
    Raises:
        CortexDispatchError for any system error.
    """
    trace = trace or []
    try:
        # 1. Resolve intent
        intent, intent_meta = resolve_intent(query, user_ctx)
        trace.append({"stage": "intent_resolved", "intent": intent, "meta": intent_meta})

        # 2. Recall recent context (if enabled)
        memory_ctx = None
        if memory_enabled:
            memory_ctx = recall_context(user_ctx, query, limit=10)
            trace.append({"stage": "memory_recalled", "context_len": len(memory_ctx or [])})

        # 3. Dispatch by mode or plugin/predictor logic
        result = None
        handler = None

        # Prefer explicit mode if set
        if mode == "plugin" or (plugin_enabled and intent in plugin_registry):
            handler = plugin_registry.get(intent)
            if handler is None:
                raise UnsupportedIntentError(f"No plugin registered for intent '{intent}'")
            result = execute_plugin(handler, user_ctx, query, context or memory_ctx)
            trace.append({"stage": "plugin_executed", "plugin": intent})

        elif mode == "predictor" or (predictor_enabled and intent in predictor_registry):
            handler = predictor_registry.get(intent)
            if handler is None:
                raise UnsupportedIntentError(f"No predictor registered for intent '{intent}'")
            result = run_predictor(handler, user_ctx, query, context or memory_ctx)
            trace.append({"stage": "predictor_executed", "predictor": intent})

        elif mode == "memory" or memory_ctx:
            # Fallback to memory/contextual recall
            result = {
                "type": "memory",
                "context": memory_ctx,
                "message": "Result sourced from memory/context recall.",
            }
            trace.append({"stage": "memory_fallback"})

        else:
            raise UnsupportedIntentError(f"No handler for intent: {intent}")

        # 4. Optionally update memory
        if memory_enabled and result:
            update_memory(user_ctx, query, result)
            trace.append({"stage": "memory_updated"})

        return {
            "result": result,
            "intent": intent,
            "intent_meta": intent_meta,
            "trace": trace,
        }

    except Exception as ex:
        trace.append({"stage": "dispatch_error", "error": str(ex)})
        raise CortexDispatchError(f"CORTEX dispatch failed: {ex}") from ex

__all__ = ["dispatch", "CortexDispatchError"]
