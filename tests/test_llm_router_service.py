import pytest  # type: ignore[import-not-found]

from ai_karen_engine.integrations.llm_router import (  # type: ignore[import-not-found]
    LLMRouter,
)
from ai_karen_engine.integrations.llm_utils import (  # type: ignore[import-not-found]
    LLMProviderBase,
)


class DummyProvider(LLMProviderBase):  # type: ignore[misc]
    def __init__(self, name: str) -> None:
        self.provider_name = name

    def generate_text(
        self, prompt: str, **kwargs: object
    ) -> str:  # pragma: no cover - trivial
        return f"{self.provider_name}:{prompt}"

    def embed(
        self, text: str, **kwargs: object
    ) -> list[float]:  # pragma: no cover - trivial
        return []

    def get_provider_info(self) -> dict[str, str]:  # pragma: no cover - simple
        return {"name": self.provider_name}


class DummyRegistry:
    def __init__(self, status_map: dict[str, str]) -> None:
        self.status_map = status_map

    def list_providers(self) -> list[str]:
        return list(self.status_map.keys())

    def default_chain(self, healthy_only: bool = False) -> list[str]:
        names = self.list_providers()
        if healthy_only:
            names = [n for n in names if self.status_map.get(n) == "healthy"]
        return names

    def get_provider(self, name: str) -> DummyProvider | None:
        if self.status_map.get(name) != "fail_create":
            return DummyProvider(name)
        return None

    def health_check(self, name: str) -> dict[str, str]:
        status = self.status_map.get(name, "unknown")
        if status == "fail_create":
            return {"status": "failed_to_create"}
        return {"status": status}


def test_local_provider_preferred() -> None:
    registry = DummyRegistry({"ollama": "healthy", "openai": "healthy"})
    router = LLMRouter(registry=registry)
    provider = router.select_provider()
    assert provider.provider_name == "ollama"


def test_fallback_to_remote_provider() -> None:
    registry = DummyRegistry({"ollama": "failed_to_create", "openai": "healthy"})
    router = LLMRouter(registry=registry)
    provider = router.select_provider()
    assert provider.provider_name == "openai"


def test_user_preference_respected() -> None:
    registry = DummyRegistry({"ollama": "healthy", "openai": "healthy"})
    router = LLMRouter(registry=registry)
    provider = router.select_provider(user_preferences={"provider": "openai"})
    assert provider.provider_name == "openai"


@pytest.mark.asyncio  # type: ignore[misc]
async def test_generate_uses_selected_provider() -> None:
    registry = DummyRegistry({"ollama": "healthy"})
    router = LLMRouter(registry=registry)
    result = await router.generate("hi")
    assert result == "ollama:hi"
