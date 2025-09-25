"""
Tests for Provider Registry with Health Monitoring and Graceful Fallbacks
"""

import os
import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ai_karen_engine.services.provider_registry import (
    ProviderRegistryService,
    ProviderCapability,
    FallbackChain,
    ProviderStatus,
    get_provider_registry_service,
    initialize_provider_registry_service
)
from src.ai_karen_engine.services.provider_health_monitor import HealthStatus
from src.ai_karen_engine.integrations.provider_registry import ModelInfo


class MockProvider:
    """Mock provider class for testing"""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def generate_text(self, prompt: str) -> str:
        return f"Generated: {prompt}"
    
    def stream_response(self, prompt: str):
        yield f"Stream: {prompt}"


class MockProviderWithEmbeddings(MockProvider):
    """Mock provider with embeddings capability"""
    
    def get_embeddings(self, text: str):
        return [0.1, 0.2, 0.3]


class TestProviderRegistryService:
    """Test the provider registry service"""
    
    def setup_method(self):
        """Setup test registry service"""
        self.service = ProviderRegistryService(use_global_registry=False)
    
    def teardown_method(self):
        """Cleanup after tests"""
        if hasattr(self, 'service'):
            self.service.shutdown()
    
    def test_provider_registration(self):
        """Test provider registration with capability detection"""
        
        # Register a basic provider
        self.service.register_provider(
            name="test_provider",
            provider_class=MockProvider,
            description="Test provider",
            requires_api_key=False
        )
        
        # Check registration
        status = self.service.get_provider_status("test_provider")
        assert status is not None
        assert status.name == "test_provider"
        assert status.has_api_key is True  # No API key required
        assert ProviderCapability.TEXT_GENERATION in status.capabilities
        assert ProviderCapability.STREAMING in status.capabilities
    
    def test_provider_registration_with_embeddings(self):
        """Test provider registration with embeddings capability"""
        
        self.service.register_provider(
            name="embedding_provider",
            provider_class=MockProviderWithEmbeddings,
            description="Provider with embeddings",
            requires_api_key=False
        )
        
        status = self.service.get_provider_status("embedding_provider")
        assert status is not None
        assert ProviderCapability.TEXT_GENERATION in status.capabilities
        assert ProviderCapability.EMBEDDINGS in status.capabilities
        assert ProviderCapability.STREAMING in status.capabilities
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_api_key_detection_available(self):
        """Test API key detection when key is available"""
        
        self.service.register_provider(
            name="openai",
            provider_class=MockProvider,
            description="OpenAI provider",
            requires_api_key=True
        )
        
        status = self.service.get_provider_status("openai")
        assert status is not None
        assert status.has_api_key is True
        assert status.is_available is True  # Should be available with API key
    
    @patch.dict(os.environ, {}, clear=True)
    def test_api_key_detection_missing(self):
        """Test API key detection when key is missing"""
        
        self.service.register_provider(
            name="openai",
            provider_class=MockProvider,
            description="OpenAI provider",
            requires_api_key=True
        )
        
        status = self.service.get_provider_status("openai")
        assert status is not None
        assert status.has_api_key is False
        assert status.is_available is False  # Should not be available without API key
    
    def test_get_available_providers(self):
        """Test getting available providers with filtering"""
        
        # Register providers with different capabilities
        self.service.register_provider(
            name="text_provider",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        self.service.register_provider(
            name="embedding_provider",
            provider_class=MockProviderWithEmbeddings,
            requires_api_key=False
        )
        
        # Get all available providers
        all_providers = self.service.get_available_providers()
        assert "text_provider" in all_providers
        assert "embedding_provider" in all_providers
        
        # Get providers with text generation capability
        text_providers = self.service.get_available_providers(
            capability=ProviderCapability.TEXT_GENERATION
        )
        assert "text_provider" in text_providers
        assert "embedding_provider" in text_providers
        
        # Get providers with embeddings capability
        embedding_providers = self.service.get_available_providers(
            capability=ProviderCapability.EMBEDDINGS
        )
        assert "text_provider" not in embedding_providers
        assert "embedding_provider" in embedding_providers
    
    def test_provider_selection_with_preferred(self):
        """Test provider selection with preferred provider"""
        
        # Register multiple providers
        self.service.register_provider(
            name="provider1",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        self.service.register_provider(
            name="provider2",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        # Select with preferred provider
        selected = self.service.select_provider_with_fallback(
            preferred_provider="provider2"
        )
        assert selected == "provider2"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_provider_selection_with_fallback(self):
        """Test provider selection with fallback when preferred is unavailable"""
        
        # Register providers - one requiring API key (unavailable), one not
        self.service.register_provider(
            name="unavailable_provider",
            provider_class=MockProvider,
            requires_api_key=True  # Will be unavailable without API key
        )
        
        self.service.register_provider(
            name="available_provider",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        # Create custom fallback chain
        self.service.create_fallback_chain(
            name="test_chain",
            primary="unavailable_provider",
            fallbacks=["available_provider"]
        )
        
        # Select with fallback
        selected = self.service.select_provider_with_fallback(
            fallback_chain_name="test_chain"
        )
        assert selected == "available_provider"
    
    def test_fallback_chain_creation(self):
        """Test creating custom fallback chains"""
        
        self.service.create_fallback_chain(
            name="custom_chain",
            primary="primary_provider",
            fallbacks=["fallback1", "fallback2"],
            capability_required=ProviderCapability.TEXT_GENERATION
        )
        
        # Check that chain was created
        assert "custom_chain" in self.service._fallback_chains
        chain = self.service._fallback_chains["custom_chain"]
        assert chain.primary == "primary_provider"
        assert chain.fallbacks == ["fallback1", "fallback2"]
        assert chain.capability_required == ProviderCapability.TEXT_GENERATION
    
    @patch.dict(os.environ, {}, clear=True)
    def test_provider_recommendations(self):
        """Test getting provider recommendations when one fails"""
        
        # Register providers
        self.service.register_provider(
            name="failed_provider",
            provider_class=MockProvider,
            requires_api_key=True  # Will fail due to missing API key
        )
        
        self.service.register_provider(
            name="alternative_provider",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        # Get recommendations
        recommendations = self.service.get_provider_recommendations("failed_provider")
        
        assert recommendations["failed_provider"] == "failed_provider"
        assert "alternative_provider" in recommendations["alternatives"]
        assert len(recommendations["configuration_guidance"]) > 0
        assert "FAILED_PROVIDER_API_KEY" in recommendations["configuration_guidance"][0]
    
    def test_system_status(self):
        """Test getting overall system status"""
        
        # Register providers with different states
        self.service.register_provider(
            name="available_provider",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        with patch.dict(os.environ, {}, clear=True):
            self.service.register_provider(
                name="missing_key_provider",
                provider_class=MockProvider,
                requires_api_key=True
            )
        
        status = self.service.get_system_status()
        
        assert status["total_providers"] == 2
        assert status["available_providers"] == 1
        assert status["providers_missing_api_keys"] == 1
        assert "available_provider" in status["provider_details"]
        assert "missing_key_provider" in status["provider_details"]
        assert len(status["recommendations"]) > 0
    
    def test_provider_status_caching(self):
        """Test that provider status is cached and refreshed appropriately"""
        
        self.service.register_provider(
            name="cached_provider",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        # Get status (should cache it)
        status1 = self.service.get_provider_status("cached_provider")
        assert status1 is not None
        
        # Get status again immediately (should use cache)
        status2 = self.service.get_provider_status("cached_provider")
        assert status2 is not None
        assert status1.last_check == status2.last_check
        
        # Manually expire cache by setting old timestamp
        status1.last_check = datetime.utcnow() - timedelta(minutes=2)
        self.service._provider_status_cache["cached_provider"] = status1
        
        # Get status again (should refresh cache)
        status3 = self.service.get_provider_status("cached_provider")
        assert status3 is not None
        assert status3.last_check > status1.last_check
    
    def test_capability_filtering(self):
        """Test provider selection based on capabilities"""
        
        # Register provider without embeddings
        self.service.register_provider(
            name="text_only",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        # Register provider with embeddings
        self.service.register_provider(
            name="with_embeddings",
            provider_class=MockProviderWithEmbeddings,
            requires_api_key=False
        )
        
        # Select provider for text generation (both should work)
        selected_text = self.service.select_provider_with_fallback(
            capability=ProviderCapability.TEXT_GENERATION
        )
        assert selected_text in ["text_only", "with_embeddings"]
        
        # Select provider for embeddings (only one should work)
        selected_embeddings = self.service.select_provider_with_fallback(
            capability=ProviderCapability.EMBEDDINGS
        )
        assert selected_embeddings == "with_embeddings"
    
    def test_no_available_providers(self):
        """Test behavior when no providers are available"""
        
        # Don't register any providers or register only unavailable ones
        with patch.dict(os.environ, {}, clear=True):
            self.service.register_provider(
                name="unavailable",
                provider_class=MockProvider,
                requires_api_key=True  # No API key available
            )
        
        # Try to select a provider
        selected = self.service.select_provider_with_fallback()
        assert selected is None
        
        # Check system status
        status = self.service.get_system_status()
        assert status["available_providers"] == 0
        # Should have recommendation about missing API keys since we have 1 provider missing keys
        assert len(status["recommendations"]) > 0
        assert any("missing API keys" in rec or "No providers are currently available" in rec 
                  for rec in status["recommendations"])


class TestGlobalProviderRegistryService:
    """Test global provider registry service functions"""
    
    def test_singleton_behavior(self):
        """Test that global service is a singleton"""
        service1 = get_provider_registry_service()
        service2 = get_provider_registry_service()
        assert service1 is service2
    
    def test_service_initialization(self):
        """Test service initialization"""
        service = initialize_provider_registry_service()
        assert service is not None
        assert isinstance(service, ProviderRegistryService)
        
        # Should be the same as global instance
        global_service = get_provider_registry_service()
        assert service is global_service


class TestFallbackChain:
    """Test FallbackChain dataclass"""
    
    def test_fallback_chain_creation(self):
        """Test creating fallback chain"""
        chain = FallbackChain(
            primary="primary",
            fallbacks=["fallback1", "fallback2"],
            capability_required=ProviderCapability.TEXT_GENERATION,
            max_fallback_attempts=2
        )
        
        assert chain.primary == "primary"
        assert chain.fallbacks == ["fallback1", "fallback2"]
        assert chain.capability_required == ProviderCapability.TEXT_GENERATION
        assert chain.max_fallback_attempts == 2


class TestProviderStatus:
    """Test ProviderStatus dataclass"""
    
    def test_provider_status_creation(self):
        """Test creating provider status"""
        capabilities = {ProviderCapability.TEXT_GENERATION, ProviderCapability.STREAMING}
        
        status = ProviderStatus(
            name="test_provider",
            is_available=True,
            has_api_key=True,
            health_status=HealthStatus.HEALTHY,
            capabilities=capabilities,
            last_check=datetime.utcnow(),
            error_message=None
        )
        
        assert status.name == "test_provider"
        assert status.is_available is True
        assert status.has_api_key is True
        assert status.health_status == HealthStatus.HEALTHY
        assert ProviderCapability.TEXT_GENERATION in status.capabilities
        assert status.error_message is None


class TestProviderCapability:
    """Test ProviderCapability enum"""
    
    def test_capability_values(self):
        """Test capability enum values"""
        assert ProviderCapability.TEXT_GENERATION.value == "text_generation"
        assert ProviderCapability.EMBEDDINGS.value == "embeddings"
        assert ProviderCapability.STREAMING.value == "streaming"
        assert ProviderCapability.FUNCTION_CALLING.value == "function_calling"
        assert ProviderCapability.VISION.value == "vision"
        assert ProviderCapability.AUDIO.value == "audio"


class TestIntegrationWithHealthMonitor:
    """Test integration with health monitor"""
    
    def setup_method(self):
        """Setup test with mocked health monitor"""
        self.service = ProviderRegistryService(use_global_registry=False)
    
    def teardown_method(self):
        """Cleanup after tests"""
        if hasattr(self, 'service'):
            self.service.shutdown()
    
    @patch('src.ai_karen_engine.services.provider_registry.get_health_monitor')
    def test_health_status_integration(self, mock_get_health_monitor):
        """Test integration with health monitor"""
        
        # Mock health monitor
        mock_health_monitor = Mock()
        mock_health_info = Mock()
        mock_health_info.status = HealthStatus.HEALTHY
        mock_health_info.error_message = None
        mock_health_monitor.get_provider_health.return_value = mock_health_info
        mock_get_health_monitor.return_value = mock_health_monitor
        
        # Create new service with mocked health monitor
        service = ProviderRegistryService()
        
        # Register provider
        service.register_provider(
            name="test_provider",
            provider_class=MockProvider,
            requires_api_key=False
        )
        
        # Check that health monitor was called
        status = service.get_provider_status("test_provider")
        assert status is not None
        assert status.health_status == HealthStatus.HEALTHY
        
        service.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])