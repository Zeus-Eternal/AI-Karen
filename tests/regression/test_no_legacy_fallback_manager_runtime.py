import pytest

from ai_karen_engine.integrations.fallback_manager import FallbackManager, FallbackManagerDeprecatedError


def test_legacy_fallback_manager_runtime_is_disabled():
    manager = FallbackManager()
    with pytest.raises(FallbackManagerDeprecatedError):
        manager.construct_fallback_chain(request={}, failed_providers=[])

    with pytest.raises(FallbackManagerDeprecatedError):
        manager.execute_fallback(request={}, fallback_chain=[])
