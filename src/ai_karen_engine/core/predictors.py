"""
Kari Core Predictors Registry
- Unified registry for ML/LLM predictors.
- Plug-and-play: register new predictors dynamically.
- Run predictors by intent, with context.
"""

from typing import Any, Dict, Callable, Optional

# Global registry: {intent_name: predictor_fn}
predictor_registry: Dict[str, Callable[[Dict[str, Any], str, Optional[Dict[str, Any]]], Any]] = {}

def register_predictor(intent: str, handler: Callable[[Dict[str, Any], str, Optional[Dict[str, Any]]], Any]) -> None:
    """
    Register a predictor function for a specific intent.
    Args:
        intent: The name of the intent this predictor handles.
        handler: Callable(user_ctx, query, context) -> Any
    """
    predictor_registry[intent] = handler

def run_predictor(
    handler: Callable[[Dict[str, Any], str, Optional[Dict[str, Any]]], Any],
    user_ctx: Dict[str, Any],
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Execute a registered predictor handler.
    Args:
        handler: Callable
        user_ctx: User/session context dict.
        query: The user's query.
        context: Optional prior context/memory.
    Returns:
        Prediction result.
    """
    return handler(user_ctx, query, context)

__all__ = ["predictor_registry", "register_predictor", "run_predictor"]
