import pytest

from ai_karen_engine.integrations.fallback_manager import FallbackManagerRemovedError, get_fallback_manager


def test_legacy_fallback_manager_is_removed():
    """Verify legacy fallback manager cannot be instantiated or used.

    The legacy integrations fallback manager has been removed and replaced with
    ExpressionGateway for expression generation.
    """
    # Factory function raises error
    with pytest.raises(FallbackManagerRemovedError, match="Legacy FallbackManager has been removed"):
        get_fallback_manager()
