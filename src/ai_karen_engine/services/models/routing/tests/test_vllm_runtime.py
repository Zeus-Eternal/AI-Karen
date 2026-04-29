"""
Integration tests for VLLMRuntime adapter.

These tests verify that the vLLM adapter:
1. Raises ProviderNotAvailable when not configured
2. Generates text when vLLM is available
3. Does NOT silently fall back to other providers
4. Returns honest health check status
5. Properly handles streaming
6. Exposes accurate metadata
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from unittest.mock import Mock

# Import VLLMRuntime and related classes
from ai_karen_engine.inference.vllm_runtime import VLLMRuntime
from ai_karen_engine.integrations.llm_utils import ProviderNotAvailable, GenerationFailed


class TestVLLMRuntimeConfig:
    """Test suite for VLLMRuntime configuration and initialization."""

    def test_vllm_runtime_without_base_url_raises_on_use(self):
        """Test that VLLMRuntime raises ProviderNotAvailable when base_url is not configured."""
        # Create runtime without base_url
        vllm = VLLMRuntime(model="test-model", base_url=None)

        # Attempting to generate should raise ProviderNotAvailable
        with pytest.raises(ProviderNotAvailable) as exc_info:
            vllm.generate("Hello, vLLM!")

        # Verify error message mentions configuration
        error_msg = str(exc_info.value)
        assert "base_url not configured" in error_msg.lower()
        assert "docker compose --profile vllm" in error_msg.lower()

    def test_vllm_runtime_with_base_url_configured(self):
        """Test that VLLMRuntime can be initialized with a base_url."""
        vllm = VLLMRuntime(
            model="test-model",
            base_url="http://localhost:8001/v1"
        )

        assert vllm.base_url == "http://localhost:8001/v1"
        assert vllm.model == "test-model"
        assert vllm.provider_name == "builtin_vllm"

    def test_vllm_runtime_uses_env_variable(self, monkeypatch):
        """Test that VLLMRuntime reads VLLM_BASE_URL from environment."""
        # Set environment variable
        monkeypatch.setenv("VLLM_BASE_URL", "http://env-localhost:8001/v1")

        vllm = VLLMRuntime()

        assert vllm.base_url == "http://env-localhost:8001/v1"

    def test_vllm_runtime_singleton_pattern(self):
        """Test that VLLMRuntime uses singleton pattern correctly."""
        instance1 = VLLMRuntime(base_url="http://localhost:8001/v1")
        instance2 = VLLMRuntime.get_instance()

        assert instance1 is instance2

    def test_vllm_runtime_api_key_handling(self, monkeypatch):
        """Test that VLLMRuntime handles API keys correctly."""
        monkeypatch.setenv("VLLM_API_KEY", "test-api-key")

        vllm = VLLMRuntime(base_url="http://localhost:8001/v1")

        assert vllm.api_key == "test-api-key"


class TestVLLMRuntimeHealthCheck:
    """Test suite for VLLMRuntime health check functionality."""

    def test_health_check_without_base_url_returns_unavailable(self):
        """Test that health check returns honest 'unavailable' status when base_url is not configured."""
        vllm = VLLMRuntime(base_url=None)

        status = vllm.health_check()

        assert status["provider"] == "builtin_vllm"
        assert status["runtime"] == "vllm"
        assert status["mode"] == "unavailable"
        assert status["status"] == "unhealthy"
        assert status["configured"] is False
        assert "error" in status

    def test_health_check_with_base_url_calls_provider(self):
        """Test that health check delegates to OpenAI-compatible provider when configured."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider
            mock_provider = MagicMock()
            mock_provider.health_check.return_value = {
                "status": "healthy",
                "model": "test-model"
            }
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            status = vllm.health_check()

            # Verify provider was called
            mock_provider.health_check.assert_called_once()

            # Verify status structure
            assert status["provider"] == "builtin_vllm"
            assert status["runtime"] == "vllm"
            assert status["mode"] == "live_vllm"

    def test_health_check_with_provider_error_returns_unhealthy(self):
        """Test that health check returns unhealthy when provider raises exception."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider that raises error
            mock_provider = MagicMock()
            mock_provider.health_check.side_effect = Exception("Connection refused")
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            status = vllm.health_check()

            # Verify error status
            assert status["status"] == "unhealthy"
            assert status["mode"] == "unavailable"
            assert "error" in status
            assert "Connection refused" in status["error"]


class TestVLLMRuntimeGeneration:
    """Test suite for VLLMRuntime text generation."""

    def test_generate_without_base_url_raises_error(self):
        """Test that generate() raises ProviderNotAvailable when base_url is not configured."""
        vllm = VLLMRuntime(base_url=None)

        with pytest.raises(ProviderNotAvailable):
            vllm.generate("Hello, vLLM!")

    def test_generate_with_base_url_calls_provider(self):
        """Test that generate() delegates to OpenAI-compatible provider when configured."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider
            mock_provider = MagicMock()
            mock_provider.generate_text.return_value = "Generated response from vLLM"
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            result = vllm.generate("Hello, vLLM!")

            # Verify provider was called
            mock_provider.generate_text.assert_called_once_with("Hello, vLLM!")

            # Verify result
            assert result == "Generated response from vLLM"

    def test_generate_with_provider_error_raises_generation_failed(self):
        """Test that generate() raises GenerationFailed when provider fails."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider that raises error
            mock_provider = MagicMock()
            mock_provider.generate_text.side_effect = Exception("API error")
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")

            with pytest.raises(GenerationFailed) as exc_info:
                vllm.generate("Hello, vLLM!")

            # Verify error message
            assert "vLLM generation failed" in str(exc_info.value)

    def test_generate_text_interface_method(self):
        """Test that generate_text() interface method delegates to generate()."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.generate_text.return_value = "Response"
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            result = vllm.generate_text("Test")

            assert result == "Response"

    def test_generate_response_interface_method(self):
        """Test that generate_response() interface method delegates to generate()."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.generate_text.return_value = "Response"
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            result = vllm.generate_response("Test")

            assert result == "Response"

    def test_no_silent_fallback_to_transformers(self):
        """Test that VLLMRuntime does NOT silently fall back to Transformers when vLLM fails."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider that fails
            mock_provider = MagicMock()
            mock_provider.generate_text.side_effect = Exception("vLLM unavailable")
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")

            # Should raise GenerationFailed, NOT return Transformers response
            with pytest.raises(GenerationFailed):
                vllm.generate("Test prompt")


class TestVLLMRuntimeStreaming:
    """Test suite for VLLMRuntime streaming functionality."""

    def test_stream_without_base_url_raises_error(self):
        """Test that stream() raises ProviderNotAvailable when base_url is not configured."""
        vllm = VLLMRuntime(base_url=None)

        with pytest.raises(ProviderNotAvailable):
            list(vllm.stream("Hello, vLLM!"))

    def test_stream_with_base_url_calls_provider(self):
        """Test that stream() delegates to OpenAI-compatible provider when configured."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider with streaming
            mock_provider = MagicMock()
            mock_provider.stream_generate.return_value = iter(["Hello", " from", " vLLM", "!"])
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            tokens = list(vllm.stream("Hello, vLLM!"))

            # Verify provider was called
            mock_provider.stream_generate.assert_called_once_with("Hello, vLLM!")

            # Verify tokens
            assert tokens == ["Hello", " from", " vLLM", "!"]

    def test_stream_with_provider_error_raises_generation_failed(self):
        """Test that stream() raises GenerationFailed when provider fails."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider that fails
            mock_provider = MagicMock()
            mock_provider.stream_generate.side_effect = Exception("Stream error")
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")

            with pytest.raises(GenerationFailed):
                list(vllm.stream("Test"))

    def test_stream_generate_interface_method(self):
        """Test that stream_generate() interface method delegates to stream()."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.stream_generate.return_value = iter(["Token"])
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            tokens = list(vllm.stream_generate("Test"))

            assert tokens == ["Token"]


class TestVLLMRuntimeEmbeddings:
    """Test suite for VLLMRuntime embedding functionality."""

    def test_embed_without_base_url_raises_error(self):
        """Test that embed() raises error when base_url is not configured."""
        vllm = VLLMRuntime(base_url=None)

        with pytest.raises(ProviderNotAvailable):
            vllm.embed("test text")

    def test_embed_with_provider_support(self):
        """Test that embed() uses provider when embeddings are supported."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider with embed method
            mock_provider = MagicMock()
            mock_provider.embed.return_value = [0.1, 0.2, 0.3]
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            result = vllm.embed("test")

            # Verify provider was called
            mock_provider.embed.assert_called_once_with("test")
            assert result == [0.1, 0.2, 0.3]

    def test_embed_without_provider_support_raises_not_implemented(self):
        """Test that embed() raises NotImplementedError when provider doesn't support embeddings."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            # Setup mock provider without embed method
            mock_provider = MagicMock(spec=[])  # No methods
            delattr(mock_provider, 'embed')  # Ensure embed doesn't exist
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")

            with pytest.raises(NotImplementedError) as exc_info:
                vllm.embed("test")

            assert "vLLM server does not support embeddings" in str(exc_info.value)
            assert "builtin_transformers" in str(exc_info.value)


class TestVLLMRuntimeWarmCache:
    """Test suite for VLLMRuntime cache warming."""

    def test_warm_cache_calls_generate(self):
        """Test that warm_cache() calls generate with minimal request."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.generate_text.return_value = "ok"
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")

            # Should not raise exception
            vllm.warm_cache()

            # Verify it called generate_text with minimal prompt
            mock_provider.generate_text.assert_called_once_with("hello", max_tokens=1)

    def test_warm_cache_silently_fails(self):
        """Test that warm_cache() doesn't raise exceptions on failure."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.generate_text.side_effect = Exception("Server unavailable")
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")

            # Should not raise exception
            vllm.warm_cache()


class TestVLLMRuntimeModelLoading:
    """Test suite for VLLMRuntime model loading."""

    def test_load_model_updates_model_path(self):
        """Test that load_model() updates the model path."""
        vllm = VLLMRuntime(base_url="http://localhost:8001/v1", model="old-model")

        assert vllm.model == "old-model"

        # Load new model
        result = vllm.load_model("new-model")

        assert result is True
        assert vllm.model == "new-model"


class TestVLLMRuntimeMetadata:
    """Test suite for VLLMRuntime metadata accuracy."""

    def test_runtime_uses_correct_provider_name(self):
        """Test that VLLMRuntime uses the correct provider name in metadata."""
        vllm = VLLMRuntime(
            base_url="http://localhost:8001/v1",
            provider_name="builtin_vllm"
        )

        assert vllm.provider_name == "builtin_vllm"
        assert vllm._provider.provider_name == "builtin_vllm"
        assert vllm._provider.display_name == "vLLM"

    def test_health_check_includes_runtime_metadata(self):
        """Test that health check includes runtime metadata."""
        with patch('ai_karen_engine.inference.vllm_runtime.OpenAICompatibleProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.health_check.return_value = {"status": "ok"}
            mock_provider_class.return_value = mock_provider

            vllm = VLLMRuntime(base_url="http://localhost:8001/v1")
            status = vllm.health_check()

            # Verify runtime metadata
            assert status["provider"] == "builtin_vllm"
            assert status["runtime"] == "vllm"
            assert status["mode"] == "live_vllm"


class TestVLLMRuntimeIntegration:
    """Integration tests for VLLMRuntime with the routing layer."""

    @pytest.mark.asyncio
    async def test_vllm_in_fallback_chain(self):
        """Test that VLLMRuntime properly integrates with the fallback chain."""
        from ai_karen_engine.services.models.routing.llm_router_service import LLMRouter, ChatRequest

        router = LLMRouter()
        request = ChatRequest(
            message="Test message",
            conversation_id="test-123",
            platform="web",
            stream=False,
        )

        # This test verifies that VLLMRuntime raises ProviderNotAvailable
        # when vLLM is not running, allowing the router to fallback to Transformers
        with patch.object(router, "registry") as mock_registry:
            # Create mock VLLM instance that raises ProviderNotAvailable
            mock_vllm = MagicMock()
            mock_vllm.generate_response.side_effect = ProviderNotAvailable("vLLM not configured")

            # Create mock Transformers instance that succeeds
            mock_transformers = MagicMock()
            mock_transformers.generate_response.return_value = "Response from Transformers"

            def get_provider_side_effect(name):
                if name == "builtin_vllm":
                    return mock_vllm
                if name == "builtin_transformers":
                    return mock_transformers
                return None

            mock_registry.get_provider.side_effect = get_provider_side_effect
            mock_registry.get_provider_info.return_value = {"default_model": "test-model"}

            router._is_provider_healthy = AsyncMock(return_value=True)

            # Execute fallback - should skip vLLM and use Transformers
            result = await router.generate_with_degraded_runtime_fallback(
                request=request,
                requested_provider="builtin_vllm",
                requested_model="test-model",
                failure_reason="vLLM unavailable"
            )

            # Verify Transformers was used
            assert result["metadata"]["llm"]["provider"] == "builtin_transformers"
            assert result["metadata"]["llm"]["fallback_level"] == 1

    @pytest.mark.skipif(
        os.getenv("KAREN_RUN_VLLM_SMOKE") != "1",
        reason="vLLM smoke test requires KAREN_RUN_VLLM_SMOKE=1"
    )
    def test_vllm_smoke_test_with_real_server(self):
        """Smoke test that requires a real vLLM server to be running."""
        # This test only runs when KAREN_RUN_VLLM_SMOKE=1 is set
        base_url = os.getenv("KAREN_VLLM_BASE_URL", "http://localhost:8001/v1")
        model = os.getenv("KAREN_VLLM_MODEL", "karen-vllm-local")

        vllm = VLLMRuntime(base_url=base_url, model=model)

        # Test health check
        health = vllm.health_check()
        assert health["configured"] is True
        assert health.get("status") != "unhealthy"

        # Test generation
        response = vllm.generate("Say vLLM smoke test passed in one sentence.")
        assert response
        assert isinstance(response, str)
        assert len(response) > 0
        assert "smoke test" in response.lower() or "passed" in response.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
