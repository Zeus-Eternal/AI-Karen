"""
Tests for the provider and runtime registry system.
"""

import pytest
from unittest.mock import Mock, patch

from src.ai_karen_engine.integrations.registry import (
    LLMRegistry,
    ProviderSpec,
    RuntimeSpec,
    ModelMetadata,
    HealthStatus,
    get_registry,
    initialize_registry
)


class TestLLMRegistry:
    """Test the LLM registry system."""
    
    def setup_method(self):
        """Setup test registry."""
        self.registry = LLMRegistry()
    
    def test_provider_registration(self):
        """Test provider registration and retrieval."""
        # Create a test provider spec
        provider_spec = ProviderSpec(
            name="test_provider",
            requires_api_key=True,
            description="Test provider",
            category="LLM",
            capabilities={"streaming", "embeddings"}
        )
        
        # Register provider
        self.registry.register_provider(provider_spec)
        
        # Check registration
        assert "test_provider" in self.registry.list_providers()
        
        # Get provider spec
        retrieved_spec = self.registry.get_provider_spec("test_provider")
        assert retrieved_spec is not None
        assert retrieved_spec.name == "test_provider"
        assert retrieved_spec.requires_api_key is True
        assert "streaming" in retrieved_spec.capabilities
    
    def test_runtime_registration(self):
        """Test runtime registration and retrieval."""
        # Create a test runtime spec
        runtime_spec = RuntimeSpec(
            name="test_runtime",
            description="Test runtime",
            family=["llama", "mistral"],
            supports=["gguf", "safetensors"],
            requires_gpu=False,
            memory_efficient=True,
            supports_streaming=True,
            priority=50
        )
        
        # Register runtime
        self.registry.register_runtime(runtime_spec)
        
        # Check registration
        assert "test_runtime" in self.registry.list_runtimes()
        
        # Get runtime spec
        retrieved_spec = self.registry.get_runtime_spec("test_runtime")
        assert retrieved_spec is not None
        assert retrieved_spec.name == "test_runtime"
        assert "llama" in retrieved_spec.family
        assert "gguf" in retrieved_spec.supports
    
    def test_compatibility_matching(self):
        """Test model-runtime compatibility matching."""
        # Register a test runtime
        runtime_spec = RuntimeSpec(
            name="test_runtime",
            family=["llama"],
            supports=["gguf"],
            priority=50
        )
        self.registry.register_runtime(runtime_spec)
        
        # Create a compatible model
        model_meta = ModelMetadata(
            id="test_model",
            name="Test Model",
            provider="test",
            family="llama",
            format="gguf"
        )
        
        # Check compatibility
        compatible = self.registry.compatible_runtimes(model_meta)
        assert "test_runtime" in compatible
        
        # Create an incompatible model
        incompatible_model = ModelMetadata(
            id="incompatible_model",
            name="Incompatible Model",
            provider="test",
            family="bert",
            format="safetensors"
        )
        
        # Check incompatibility
        compatible = self.registry.compatible_runtimes(incompatible_model)
        assert "test_runtime" not in compatible
    
    def test_optimal_runtime_selection(self):
        """Test optimal runtime selection based on requirements."""
        # Register multiple runtimes with different priorities
        high_priority_runtime = RuntimeSpec(
            name="high_priority",
            family=["llama"],
            supports=["gguf"],
            requires_gpu=True,
            priority=90
        )
        
        low_priority_runtime = RuntimeSpec(
            name="low_priority",
            family=["llama"],
            supports=["gguf"],
            requires_gpu=False,
            priority=50
        )
        
        self.registry.register_runtime(high_priority_runtime)
        self.registry.register_runtime(low_priority_runtime)
        
        # Create a test model
        model_meta = ModelMetadata(
            id="test_model",
            name="Test Model",
            provider="test",
            family="llama",
            format="gguf"
        )
        
        # Test without requirements (should select highest priority)
        optimal = self.registry.optimal_runtime(model_meta)
        assert optimal == "high_priority"
        
        # Test with GPU requirement
        optimal_gpu = self.registry.optimal_runtime(
            model_meta, 
            requirements={"requires_gpu": True}
        )
        assert optimal_gpu == "high_priority"
        
        # Test without GPU requirement (should still get highest priority compatible)
        optimal_no_gpu = self.registry.optimal_runtime(
            model_meta,
            requirements={"requires_gpu": False}
        )
        # Both runtimes are compatible, should get highest priority
        assert optimal_no_gpu == "high_priority"
    
    def test_health_checking(self):
        """Test health checking functionality."""
        # Register a provider with health check
        def mock_health_check():
            return {"status": "healthy", "message": "All good"}
        
        provider_spec = ProviderSpec(
            name="test_provider",
            requires_api_key=False,
            health_check=mock_health_check
        )
        
        self.registry.register_provider(provider_spec)
        
        # Perform health check
        health = self.registry.health_check("provider:test_provider")
        assert health.status == "healthy"
        assert health.last_check is not None
        assert health.response_time is not None
    
    def test_provider_filtering(self):
        """Test provider filtering by category and health."""
        # Register providers with different categories
        llm_provider = ProviderSpec(
            name="llm_provider",
            requires_api_key=False,
            category="LLM"
        )
        
        embedding_provider = ProviderSpec(
            name="embedding_provider",
            requires_api_key=False,
            category="embedding"
        )
        
        self.registry.register_provider(llm_provider)
        self.registry.register_provider(embedding_provider)
        
        # Test category filtering
        llm_providers = self.registry.list_providers(category="LLM")
        assert "llm_provider" in llm_providers
        assert "embedding_provider" not in llm_providers
        
        embedding_providers = self.registry.list_providers(category="embedding")
        assert "embedding_provider" in embedding_providers
        assert "llm_provider" not in embedding_providers
    
    def test_unregistration(self):
        """Test provider and runtime unregistration."""
        # Register a provider
        provider_spec = ProviderSpec(
            name="temp_provider",
            requires_api_key=False
        )
        self.registry.register_provider(provider_spec)
        
        # Verify registration
        assert "temp_provider" in self.registry.list_providers()
        
        # Unregister
        result = self.registry.unregister_provider("temp_provider")
        assert result is True
        
        # Verify unregistration
        assert "temp_provider" not in self.registry.list_providers()
        
        # Try to unregister non-existent provider
        result = self.registry.unregister_provider("non_existent")
        assert result is False


class TestGlobalRegistry:
    """Test global registry functions."""
    
    def test_global_registry_singleton(self):
        """Test that global registry is a singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        # Initialize fresh registry
        registry = initialize_registry()
        
        # Should have core providers registered
        providers = registry.list_providers()
        assert len(providers) > 0
        
        # Should have core runtimes registered (if available)
        runtimes = registry.list_runtimes()
        # May be empty if runtime dependencies are not installed
        assert isinstance(runtimes, list)


class TestModelMetadata:
    """Test ModelMetadata functionality."""
    
    def test_model_metadata_creation(self):
        """Test creating model metadata."""
        metadata = ModelMetadata(
            id="test_model",
            name="Test Model",
            provider="test_provider",
            family="llama",
            format="gguf",
            size=1024*1024*1024,  # 1GB
            parameters="7B",
            quantization="Q4_K_M",
            context_length=2048,
            capabilities={"text", "code"},
            local_path="/path/to/model",
            license="MIT"
        )
        
        assert metadata.id == "test_model"
        assert metadata.family == "llama"
        assert metadata.format == "gguf"
        assert "text" in metadata.capabilities
        assert metadata.size == 1024*1024*1024


class TestHealthStatus:
    """Test HealthStatus functionality."""
    
    def test_health_status_creation(self):
        """Test creating health status."""
        status = HealthStatus(
            status="healthy",
            last_check=1234567890.0,
            error_message=None,
            response_time=0.1,
            capabilities={"streaming": True}
        )
        
        assert status.status == "healthy"
        assert status.last_check == 1234567890.0
        assert status.error_message is None
        assert status.response_time == 0.1
        assert status.capabilities["streaming"] is True


if __name__ == "__main__":
    pytest.main([__file__])