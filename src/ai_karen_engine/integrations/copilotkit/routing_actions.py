"""
CopilotKit KIRE action registration stub.

Ensures routing actions are registered via the predictor registry and provides
a convenience function for explicit initialization if desired.
"""

from __future__ import annotations


def ensure_kire_actions_registered() -> None:
    """Import side-effects register routing actions in predictor registry."""
    # Import routing.actions to populate predictor_registry with routing.* handlers
    try:
        import ai_karen_engine.routing.actions  # noqa: F401
    except Exception:
        # Best-effort; higher-level startup already tries to import actions
        pass


# Import at module import time as well
ensure_kire_actions_registered()

__all__ = ["ensure_kire_actions_registered"]

