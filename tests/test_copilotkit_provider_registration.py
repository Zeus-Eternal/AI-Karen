"""
Tests for CopilotKit Provider Registration
Validates that the CopilotKit provider is properly registered in the provider registry.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ai_karen_engine.integrations.provider_registry import (
    get_provider_registry,
    initialize_provider_registry,
    ProviderRegistry
)
from ai_karen_engine.integrations.copilotkit_provider import (
    CopilotKitProvider,
    COPILOTKIT_MODELS,
    create_copilotkit_provider
)


class TestCopilotKitProviderRegistration:
    """Test CopilotKit provider registration and discovery."""
    
    def test_provider_registry_initialization(self):
        """Test that provider registry initializes with CopilotKit provider."""
        registry = initialize_provider_registry()
        
        # Verify CopilotKit provider is registered
        assert registry.is_provider_registered("copilotkit")
        
        # Verify provider information
        provider_info = registry.get_provider_info("copilotkit")
        assert provider_info is not None
        assert provider_info.name == "copilotkit"
        assert provider_info.provider_class == CopilotKitProvider
        assert provider_info.description == "AI-powered development assistance with memory integration and action suggestions"
        assert provider_info.requires_api_key is False
        assert provider_info.default_model == "copilot-assist"
        
        # Verify models are registered
        assert len(provider_info.models) == 3
        model_names = [model.name for model in provider_info.models]
        assert "copilot-assist" in model_names
        assert "copilot-memory" in model_names
        assert "copilot-actions" in model_names
    
    def test_provider_models_configuration(self):
        """Test that CopilotKit models are properly configured."""
        registry = get_provider_registry()
        provider_info = registry.get_provider_info("copilotkit")
        
        # Test copilot-assist model
        assist_model = next(m for m in provider_info.models if m.name == "copilot-assist")
        assert "chat_assistance" in assist_model.capabilities
        assert "memory_integration" in assist_model.capabilities
        assert "action_suggestions" in assist_model.capabilities
        assert "context_awareness" in assist_model.capabilities
        assert assist_model.default_settings["top_k"] == 6
        assert assist_model.default_settings["enable_actions"] is True
        
        # Test copilot-memory model
        memory_model = next(m for m in provider_info.models if m.name == "copilot-memory")
        assert "memory_search" in memory_model.capabilities
        assert "memory_commit" in memory_model.capabilities
        assert "tenant_isolation" in memory_model.capabilities
        assert "audit_logging" in memory_model.capabilities
        assert memory_model.default_settings["top_k"] == 12
        assert memory_model.default_settings["enable_audit"] is True
        
        # Test copilot-actions model
        actions_model = next(m for m in provider_info.models if m.name == "copilot-actions")
        assert "action_suggestions" in actions_model.capabilities
        assert "workflow_automation" in actions_model.capabilities
        assert "task_management" in actions_model.capabilities
        assert "document_operations" in actions_model.capabilities
        assert actions_model.default_settings["confidence_threshold"] == 0.6
        assert actions_model.default_settings["max_actions"] == 5
    
    def test_provider_instance_creation(self):
        """Test that provider instances can be created successfully."""
        registry = get_provider_registry()
        
        # Test default instance creation
        provider = registry.get_provider("copilotkit")
        assert isinstance(provider, CopilotKitProvider)
        assert provider.model == "copilot-assist"  # Default model
        assert provider.name == "copilotkit"
        assert provider.version == "1.0.0"
        
        # Test custom instance creation
        custom_provider = registry.get_provider("copilotkit", 
            model="copilot-memory",
            api_base="https://custom.api.com",
            timeout=60
        )
        assert isinstance(custom_provider, CopilotKitProvider)
        assert custom_provider.model == "copilot-memory"
        assert custom_provider.api_base == "https://custom.api.com"
        assert custom_provider.timeout == 60
    
    def test_provider_capabilities_discovery(self):
        """Test that provider capabilities can be discovered."""
        registry = get_provider_registry()
        
        # Get all capabilities
        all_capabilities = registry.get_all_capabilities()
        assert "copilotkit" in all_capabilities
        
        copilot_capabilities = all_capabilities["copilotkit"]
        expected_capabilities = {
            "chat_assistance", "memory_integration", "action_suggestions", 
            "context_awareness", "memory_search", "memory_commit", 
            "tenant_isolation", "audit_logging", "workflow_automation",
            "task_management", "document_operations"
        }
        
        # Verify all expected capabilities are present
        for capability in expected_capabilities:
            assert capability in copilot_capabilities
    
    def test_provider_model_listing(self):
        """Test that provider models can be listed."""
        registry = get_provider_registry()
        
        models = registry.list_models("copilotkit")
        assert len(models) == 3
        assert "copilot-assist" in models
        assert "copilot-memory" in models
        assert "copilot-actions" in models
    
    def test_provider_factory_function(self):
        """Test the provider factory function."""
        provider = create_copilotkit_provider(
            model="copilot-actions",
            api_base="https://test.api.com",
            timeout=45,
            custom_param="test_value"
        )
        
        assert isinstance(provider, CopilotKitProvider)
        assert provider.model == "copilot-actions"
        assert provider.api_base == "https://test.api.com"
        assert provider.timeout == 45
        assert provider.config["custom_param"] == "test_value"
    
    def test_provider_unregistration(self):
        """Test that providers can be unregistered."""
        registry = initialize_provider_registry()
        
        # Verify provider is registered
        assert registry.is_provider_registered("copilotkit")
        
        # Unregister provider
        success = registry.unregister_provider("copilotkit")
        assert success is True
        
        # Verify provider is no longer registered
        assert not registry.is_provider_registered("copilotkit")
        assert registry.get_provider_info("copilotkit") is None
        
        # Test unregistering non-existent provider
        success = registry.unregister_provider("nonexistent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_provider_initialization_and_status(self):
        """Test provider initialization and status reporting."""
        registry = get_provider_registry()
        provider = registry.get_provider("copilotkit")
        
        # Test initial status
        status = provider.get_status()
        assert status["name"] == "copilotkit"
        assert status["version"] == "1.0.0"
        assert status["initialized"] is False
        assert status["health_status"] == "unknown"
        
        # Mock the health check to avoid actual HTTP calls
        provider._health_check = AsyncMock(return_value={
            "status": "healthy",
            "service": "copilot",
            "dependencies": {"memory_service": True, "llm_registry": True}
        })
        
        # Test initialization
        await provider.initialize()
        
        # Test status after initialization
        status = provider.get_status()
        assert status["initialized"] is True
        assert status["health_status"] == "healthy"
        
        # Test capabilities and models
        capabilities = provider.get_capabilities()
        assert "chat_assistance" in capabilities
        assert "memory_integration" in capabilities
        
        models = provider.get_models()
        assert "copilot-assist" in models
        assert "copilot-memory" in models
        assert "copilot-actions" in models
    
    def test_global_registry_singleton(self):
        """Test that global registry maintains singleton behavior."""
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()
        
        # Should be the same instance
        assert registry1 is registry2
        
        # Both should have CopilotKit provider
        assert registry1.is_provider_registered("copilotkit")
        assert registry2.is_provider_registered("copilotkit")
    
    def test_provider_registry_error_handling(self):
        """Test error handling in provider registry."""
        registry = ProviderRegistry()
        
        # Test getting non-existent provider
        provider = registry.get_provider("nonexistent")
        assert provider is None
        
        # Test listing models for non-existent provider
        models = registry.list_models("nonexistent")
        assert models == []
        
        # Test getting info for non-existent provider
        info = registry.get_provider_info("nonexistent")
        assert info is None


if __name__ == "__main__":
    pytest.main([__file__])