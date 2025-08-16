from ai_karen_engine.integrations.provider_registry import (
    ProviderRegistry,
    ModelInfo,
    get_provider_registry,
)


class DummyProvider:
    def __init__(self, model: str = "base") -> None:
        self.model = model


def test_register_and_get_provider():
    registry = ProviderRegistry()
    registry.register_provider(
        "dummy",
        DummyProvider,
        description="test",
        models=[ModelInfo(name="base")],
        default_model="base",
    )

    provider = registry.get_provider("dummy")
    assert isinstance(provider, DummyProvider)
    assert provider.model == "base"
    assert registry.list_providers() == ["dummy"]
    assert registry.list_models("dummy") == ["base"]


def test_no_copilotkit_registration_by_default():
    registry = get_provider_registry()
    assert "copilotkit" not in registry.list_providers()

