"""
Integration tests for Provider Registry with existing system components
"""

import os
import pytest
from unittest.mock import patch, Mock

from src.ai_karen_engine.services.provider_registry import (
    ProviderRegistryService,
    ProviderCapability,
    get_provider_registry_service
)
from src.ai_karen_engine.services.provider_health_monitor import HealthStatus


class MockLLMProvider:
    """Mock LLM provider for integration testing"""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def generate_text(self, prompt: str) -> str:
        return f"Generated: {prompt}"
    
    def get_embeddings(self, text: str):
        return [0.1, 0.2, 0.3]


class TestProviderRegistryIntegration:
    """Test provider registry integration with existing components"""
    
    def setup_method(self):
        """Setup test with fresh service"""
        self.service = ProviderRegistryService(use_global_registry=False)
    
    def teardown_method(self):
        """Cleanup after tests"""
        if hasattr(self, 'service'):
            self.service.shutdown()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_openai_provider_with_api_key(self):
        """Test OpenAI provider registration and availability with API key"""
        
        # Register OpenAI provider
        self.service.register_provider(
            name="openai",
            provider_class=MockLLMProvider,
            description="OpenAI GPT models",
            requires_api_key=True,
            capabilities={ProviderCapability.TEXT_GENERATION, ProviderCapability.EMBEDDINGS}
        )
        
        # Check provider status
        status = self.service.get_provider_status("openai")
        assert status is not None
        assert status.name == "openai"
        assert status.has_api_key is True
        assert status.is_available is True
        assert ProviderCapability.TEXT_GENERATION in status.capabilities
        assert ProviderCapability.EMBEDDINGS in status.capabilities
        
        # Should be available for selection
        available_providers = self.service.get_available_providers()
        assert "openai" in available_providers
        
        # Should be selectable as preferred provider
        selected = self.service.select_provider_with_fallback(preferred_provider="openai")
        assert selected == "openai"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_openai_provider_without_api_key(self):
        """Test OpenAI provider behavior without API key"""
        
        # Register OpenAI provider
        self.service.register_provider(
            name="openai",
            provider_class=MockLLMProvider,
            description="OpenAI GPT models",
            requires_api_key=True
        )
        
        # Check provider status
        status = self.service.get_provider_status("openai")
        assert status is not None
        assert status.has_api_key is False
        assert status.is_available is False
        
        # Should not be available for selection
        available_providers = self.service.get_available_providers()
        assert "openai" not in available_providers
        
        # Should not be selectable as preferred provider
        selected = self.service.select_provider_with_fallback(preferred_provider="openai")
        assert selected is None
    
    def test_ollama_provider_no_api_key_required(self):
        """Test Ollama provider that doesn't require API key"""
        
        # Register Ollama provider
        self.service.register_provider(
            name="ollama",
            provider_class=MockLLMProvider,
            description="Local Ollama server",
            requires_api_key=False
        )
        
        # Check provider status
        status = self.service.get_provider_status("ollama")
        assert status is not None
        assert status.has_api_key is True  # Should be True since no key required
        assert status.is_available is True
        
        # Should be available for selection
        available_providers = self.service.get_available_providers()
        assert "ollama" in available_providers
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_fallback_chain_with_mixed_providers(self):
        """Test fallback chain with providers that have different API key requirements"""
        
        # Register OpenAI provider (requires API key, available)
        self.service.register_provider(
            name="openai",
            provider_class=MockLLMProvider,
            description="OpenAI GPT models",
            requires_api_key=True
        )
        
        # Register Ollama provider (no API key required, available)
        self.service.register_provider(
            name="ollama",
            provider_class=MockLLMProvider,
            description="Local Ollama server",
            requires_api_key=False
        )
        
        # Register Gemini provider (requires API key, not available)
        self.service.register_provider(
            name="gemini",
            provider_class=MockLLMProvider,
            description="Google Gemini models",
            requires_api_key=True  # No GOOGLE_API_KEY set
        )
        
        # Create custom fallback chain: Gemini -> OpenAI -> Ollama
        self.service.create_fallback_chain(
            name="mixed_chain",
            primary="gemini",
            fallbacks=["openai", "ollama"]
        )
        
        # Select provider using fallback chain
        selected = self.service.select_provider_with_fallback(fallback_chain_name="mixed_chain")
        
        # Should fallback to OpenAI since Gemini is unavailable
        assert selected == "openai"
    
    def test_provider_recommendations_for_missing_api_keys(self):
        """Test provider recommendations when API keys are missing"""
        
        # Register providers with missing API keys
        with patch.dict(os.environ, {}, clear=True):
            self.service.register_provider(
                name="openai",
                provider_class=MockLLMProvider,
                requires_api_key=True
            )
            
            self.service.register_provider(
                name="gemini",
                provider_class=MockLLMProvider,
                requires_api_key=True
            )
        
        # Get recommendations for failed OpenAI provider
        recommendations = self.service.get_provider_recommendations("openai")
        
        assert recommendations["failed_provider"] == "openai"
        assert len(recommendations["configuration_guidance"]) > 0
        assert "OPENAI_API_KEY" in recommendations["configuration_guidance"][0]
        
        # Since both providers lack API keys, no alternatives should be available
        # This is correct behavior - only available providers are suggested as alternatives
        assert len(recommendations["alternatives"]) == 0
    
    def test_system_status_with_mixed_provider_states(self):
        """Test system status reporting with providers in different states"""
        
        # Register available provider
        self.service.register_provider(
            name="ollama",
            provider_class=MockLLMProvider,
            requires_api_key=False
        )
        
        # Register unavailable provider (missing API key)
        with patch.dict(os.environ, {}, clear=True):
            self.service.register_provider(
                name="openai",
                provider_class=MockLLMProvider,
                requires_api_key=True
            )
        
        # Get system status
        status = self.service.get_system_status()
        
        assert status["total_providers"] == 2
        assert status["available_providers"] == 1
        assert status["providers_missing_api_keys"] == 1
        
        # Check provider details
        assert "ollama" in status["provider_details"]
        assert "openai" in status["provider_details"]
        
        assert status["provider_details"]["ollama"]["is_available"] is True
        assert status["provider_details"]["openai"]["is_available"] is False
        assert status["provider_details"]["openai"]["has_api_key"] is False
        
        # Should have recommendations
        assert len(status["recommendations"]) > 0
        assert any("missing API keys" in rec for rec in status["recommendations"])
    
    def test_capability_based_provider_selection(self):
        """Test provider selection based on capabilities"""
        
        # Register text-only provider
        self.service.register_provider(
            name="text_provider",
            provider_class=MockLLMProvider,
            requires_api_key=False,
            capabilities={ProviderCapability.TEXT_GENERATION}
        )
        
        # Register provider with embeddings
        self.service.register_provider(
            name="embedding_provider",
            provider_class=MockLLMProvider,
            requires_api_key=False,
            capabilities={ProviderCapability.TEXT_GENERATION, ProviderCapability.EMBEDDINGS}
        )
        
        # Select provider for text generation (both should work)
        text_providers = self.service.get_available_providers(
            capability=ProviderCapability.TEXT_GENERATION
        )
        assert len(text_providers) == 2
        assert "text_provider" in text_providers
        assert "embedding_provider" in text_providers
        
        # Select provider for embeddings (only one should work)
        embedding_providers = self.service.get_available_providers(
            capability=ProviderCapability.EMBEDDINGS
        )
        assert len(embedding_providers) == 1
        assert "embedding_provider" in embedding_providers
        
        # Select provider with embedding capability
        selected = self.service.select_provider_with_fallback(
            capability=ProviderCapability.EMBEDDINGS
        )
        assert selected == "embedding_provider"
    
    def test_global_service_instance(self):
        """Test global service instance behavior"""
        
        # Get global instance
        global_service = get_provider_registry_service()
        assert global_service is not None
        
        # Should be singleton
        global_service2 = get_provider_registry_service()
        assert global_service is global_service2
        
        # Should use global registry by default
        assert global_service.base_registry is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])