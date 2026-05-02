from __future__ import annotations

from typing import Any
from ai_karen_engine.core.logging import get_logger

logger = get_logger("kari.expression.observability")

def emit_expression_event(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Emit an expression event using the centralized runtime logger."""
    # Standardize payload for the central logger
    # These fields will be extracted into the structured log
    logger.event(name, **payload)
    
    return {"event": name, "payload": payload}

def get_expression_events(limit: int = 100) -> list[dict[str, Any]]:
    # This was previously returning a list of dicts. 
    # With centralized logging, we'd ideally query the log sink.
    # For now, we return empty to avoid memory bloat if not used by UI.
    return []
