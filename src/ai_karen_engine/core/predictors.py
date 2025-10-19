"""
Kari Core Predictors Registry
- Unified registry for ML/LLM predictors.
- Plug-and-play: register new predictors dynamically.
- Run predictors by intent, with context.
"""

from typing import Any, Dict, Callable, Optional
import inspect

# Global registry: {intent_name: predictor_fn}
predictor_registry: Dict[str, Callable[[Dict[str, Any], str, Optional[Dict[str, Any]]], Any]] = {}


def register_predictor(
    intent: str,
    handler: Callable[[Dict[str, Any], str, Optional[Dict[str, Any]]], Any],
) -> None:
    """Register a predictor function for a specific intent."""
    predictor_registry[intent] = handler


async def run_predictor(
    handler: Callable[[Dict[str, Any], str, Optional[Dict[str, Any]]], Any],
    user_ctx: Dict[str, Any],
    query: str,
    context: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute a registered predictor handler, awaiting async handlers if needed."""
    result = handler(user_ctx, query, context)
    if inspect.isawaitable(result):
        return await result
    return result


__all__ = ["predictor_registry", "register_predictor", "run_predictor"]
