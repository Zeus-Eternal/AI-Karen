"""Tests for the deterministic fallback LLM provider."""

import importlib.util
import os
import sys
import types
from contextlib import contextmanager
from pathlib import Path

os.environ.setdefault("KARI_DUCKDB_PASSWORD", "test-password")


def _install_database_stubs() -> None:
    if "ai_karen_engine.database.client" not in sys.modules:
        client_module = types.ModuleType("ai_karen_engine.database.client")

        @contextmanager
        def _ctx_manager():
            class _DummySession:
                def query(self, *args, **kwargs):
                    return self

                def filter_by(self, **kwargs):
                    return self

                def first(self):
                    return None

                def add(self, obj):
                    return None

                def commit(self):
                    return None

            yield _DummySession()

        client_module.get_db_session_context = _ctx_manager  # type: ignore[attr-defined]
        sys.modules["ai_karen_engine.database.client"] = client_module

    if "ai_karen_engine.database.models" not in sys.modules:
        models_module = types.ModuleType("ai_karen_engine.database.models")

        class _LLMProvider:
            id = None

        class _LLMRequest:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        class _GenericModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        def _module_getattr(name: str):
            return _GenericModel

        models_module.LLMProvider = _LLMProvider  # type: ignore[attr-defined]
        models_module.LLMRequest = _LLMRequest  # type: ignore[attr-defined]
        models_module.__getattr__ = _module_getattr  # type: ignore[attr-defined]
        sys.modules["ai_karen_engine.database.models"] = models_module

    if "ai_karen_engine.services.metrics_service" not in sys.modules:
        metrics_module = types.ModuleType("ai_karen_engine.services.metrics_service")

        class _Metrics:
            def record_llm_latency(self, *args, **kwargs):
                return None

        metrics_module.get_metrics_service = lambda: _Metrics()  # type: ignore[attr-defined]
        sys.modules["ai_karen_engine.services.metrics_service"] = metrics_module


def _load_fallback_provider():
    _install_database_stubs()

    module_name = "ai_karen_engine.integrations.providers.fallback_provider"
    module_path = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "ai_karen_engine"
        / "integrations"
        / "providers"
        / "fallback_provider.py"
    )

    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        fallback_module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(fallback_module)
        sys.modules[module_name] = fallback_module
    else:
        fallback_module = sys.modules[module_name]

    providers_name = "ai_karen_engine.integrations.providers"
    if providers_name not in sys.modules:
        providers_module = types.ModuleType(providers_name)
        fallback_cls = fallback_module.FallbackProvider

        class _DummyProvider:  # pragma: no cover - placeholder
            def __init__(self, *args, **kwargs):
                return None

        providers_module.HuggingFaceProvider = _DummyProvider  # type: ignore[attr-defined]
        providers_module.LlamaCppProvider = _DummyProvider  # type: ignore[attr-defined]
        providers_module.OpenAIProvider = _DummyProvider  # type: ignore[attr-defined]
        providers_module.GeminiProvider = _DummyProvider  # type: ignore[attr-defined]
        providers_module.DeepseekProvider = _DummyProvider  # type: ignore[attr-defined]
        providers_module.CopilotKitProvider = _DummyProvider  # type: ignore[attr-defined]
        providers_module.FallbackProvider = fallback_cls  # type: ignore[attr-defined]
        providers_module.__all__ = [
            "HuggingFaceProvider",
            "LlamaCppProvider",
            "OpenAIProvider",
            "GeminiProvider",
            "DeepseekProvider",
            "CopilotKitProvider",
            "FallbackProvider",
        ]
        sys.modules[providers_name] = providers_module

    return fallback_module.FallbackProvider


class TestFallbackProvider:
    """Ensure the fallback provider keeps the prompt/response loop alive."""

    def test_generate_text_acknowledges_prompt(self):
        provider_cls = _load_fallback_provider()
        provider = provider_cls()
        prompt = "Summarise offline readiness steps"

        response = provider.generate_text(prompt)

        assert "fallback assistant" in response.lower()
        assert "summarise" in response.lower()

    def test_embeddings_are_deterministic(self):
        provider_cls = _load_fallback_provider()
        provider = provider_cls()
        text = "deterministic embedding"

        first = provider.embed(text)
        second = provider.embed(text)

        assert first == second
        assert all(-1.0 <= value <= 1.0 for value in first)

    def test_llm_utils_uses_fallback_when_primary_missing(self):
        provider_cls = _load_fallback_provider()
        _install_database_stubs()

        class _DummyRegistry:
            def __init__(self):
                self.calls = []

            def get_available_providers(self):
                return ["fallback"]

            def list_providers(self):
                return ["fallback", "openai"]

            def auto_select_provider(self, _requirements):
                return "fallback"

            def get_provider(self, name, **_kwargs):
                self.calls.append(name)
                if name == "fallback":
                    return provider_cls()
                return None

        registry_module = types.ModuleType(
            "ai_karen_engine.integrations.llm_registry"
        )
        dummy_registry = _DummyRegistry()
        registry_module.get_registry = lambda: dummy_registry  # type: ignore[attr-defined]
        registry_module.list_providers = dummy_registry.list_providers  # type: ignore[attr-defined]
        original_module = sys.modules.get(
            "ai_karen_engine.integrations.llm_registry"
        )
        sys.modules["ai_karen_engine.integrations.llm_registry"] = registry_module

        try:
            from ai_karen_engine.integrations.llm_utils import LLMUtils

            utils = LLMUtils(use_registry=True)
            response = utils.generate_text(
                "Verify fallback readiness", provider="openai"
            )

            assert "fallback assistant" in response.lower()
            assert dummy_registry.calls == ["openai", "fallback"]
        finally:
            if original_module is not None:
                sys.modules["ai_karen_engine.integrations.llm_registry"] = (
                    original_module
                )
            else:
                del sys.modules["ai_karen_engine.integrations.llm_registry"]

