import pytest

from ai_karen_engine.integrations.provider_registry import (
    get_provider_registry,
    initialize_provider_registry,
)
from ai_karen_engine.integrations.copilotkit_provider import CopilotKitProvider


def test_copilotkit_not_auto_registered():
    registry = initialize_provider_registry()
    assert not registry.is_provider_registered("copilotkit")


def test_manual_copilotkit_registration():
    registry = get_provider_registry()
    registry.register_provider("copilotkit", CopilotKitProvider)
    assert registry.is_provider_registered("copilotkit")
