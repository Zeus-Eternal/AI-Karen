"""
Tests for Provider Categorization

This module tests that providers are properly categorized as LLM vs non-LLM providers,
ensuring CopilotKit is excluded from LLM provider lists and interfaces.
"""

import pytest
from unittest.mock import Mock, patch

from ai_karen_engine.integrations.registry import (
    LLMRegistry,
    ProviderSpec,
    get_registry,
    initialize_registry
)
from ai_karen_engine.integrations.dynamic_provider_system import (
    DynamicProviderManager,
    DynamicProviderSpec,
    get_dynamic_provider_manager
)


class TestProviderCategorization:
    """Test provider categorization functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Initialize fresh registry for each test
        self.registry = initialize_registry()
        self.provider_manager = DynamicProviderManager()
    
    def test_llm_provider_categorization(self):
        """Test that LLM providers are properly categorized."""
        # Get LLM providers
        llm_providers = self.provider_manager.get_llm_providers()
        
        # Verify expected LLM providers are included
        expected_llm_providers = {"openai", "gemini", "deepseek", "huggingface", "local"}
        actual_llm_providers = set(llm_providers)
        
        assert expected_llm_providers.issubset(actual_llm_providers), \
            f"Missing LLM providers: {expected_llm_providers - actual_llm_providers}"
        
        # Verify all returned providers are actually LLM providers
        for provider_name in llm_providers:
            spec = self.registry.get_provider_spec(provider_name)
            assert spec is not None, f"Provider {provider_name} not found in registry"
            assert spec.category == "LLM", f"Provider {provider_name} is not categorized as LLM"
    
    def test_copilotkit_not_in_llm_providers(self):
        """Test that CopilotKit is not included in LLM provider lists."""
        llm_providers = self.provider_manager.get_llm_providers()
        
        # CopilotKit should not be in LLM providers
        assert "copilotkit" not in llm_providers, \
            "CopilotKit should not be included in LLM provider lists"
    
    def test_copilotkit_in_non_llm_providers(self):
        """Test that CopilotKit is included in non-LLM provider lists."""
        non_llm_providers = self.provider_manager.get_non_llm_providers()
        
        # CopilotKit should be in non-LLM providers
        assert "copilotkit" in non_llm_providers, \
            "CopilotKit should be included in non-LLM provider lists"
    
    def test_copilotkit_provider_spec(self):
        """Test that CopilotKit has correct provider specification."""
        spec = self.registry.get_provider_spec("copilotkit")
        
        assert spec is not None, "CopilotKit provider spec not found"
        assert spec.category == "UI_FRAMEWORK", \
            f"CopilotKit category should be UI_FRAMEWORK, got {spec.category}"
        assert not spec.requires_api_key, \
            "CopilotKit should not require API key"
        
        # Check if it's a DynamicProviderSpec with is_llm_provider flag
        if isinstance(spec, DynamicProviderSpec):
            assert not spec.is_llm_provider, \
                "CopilotKit should have is_llm_provider=False"
            assert spec.provider_type == "ui_framework", \
                f"CopilotKit provider_type should be ui_framework, got {spec.provider_type}"
    
    def test_registry_list_providers_llm_only_filter(self):
        """Test that registry list_providers respects llm_only filter."""
        # Get all providers
        all_providers = self.registry.list_providers(llm_only=False)
        
        # Get only LLM providers
        llm_only_providers = self.registry.list_providers(llm_only=True)
        
        # LLM-only list should be a subset of all providers
        assert set(llm_only_providers).issubset(set(all_providers)), \
            "LLM-only providers should be a subset of all providers"
        
        # CopilotKit should be in all providers but not in LLM-only
        assert "copilotkit" in all_providers, \
            "CopilotKit should be in all providers list"
        assert "copilotkit" not in llm_only_providers, \
            "CopilotKit should not be in LLM-only providers list"
        
        # Verify all LLM-only providers are actually LLM providers
        for provider_name in llm_only_providers:
            spec = self.registry.get_provider_spec(provider_name)
            assert spec.category == "LLM", \
                f"Provider {provider_name} in LLM-only list is not categorized as LLM"
    
    def test_provider_info_categorization(self):
        """Test that provider info correctly reflects categorization."""
        # Test LLM provider info
        openai_info = self.provider_manager.get_provider_info("openai")
        assert openai_info is not None, "OpenAI provider info not found"
        assert openai_info["category"] == "LLM", \
            f"OpenAI category should be LLM, got {openai_info['category']}"
        assert openai_info["is_llm_provider"] is True, \
            "OpenAI should be marked as LLM provider"
        
        # Test non-LLM provider info
        copilotkit_info = self.provider_manager.get_provider_info("copilotkit")
        assert copilotkit_info is not None, "CopilotKit provider info not found"
        assert copilotkit_info["category"] == "UI_FRAMEWORK", \
            f"CopilotKit category should be UI_FRAMEWORK, got {copilotkit_info['category']}"
        assert copilotkit_info["is_llm_provider"] is False, \
            "CopilotKit should not be marked as LLM provider"
        assert copilotkit_info["provider_type"] == "ui_framework", \
            f"CopilotKit provider_type should be ui_framework, got {copilotkit_info['provider_type']}"
    
    def test_custom_provider_categorization(self):
        """Test categorization of custom providers."""
        # Register a custom LLM provider
        custom_llm_spec = DynamicProviderSpec(
            name="custom_llm",
            requires_api_key=True,
            description="Custom LLM provider for testing",
            category="LLM",
            is_llm_provider=True,
            provider_type="remote"
        )
        self.registry.register_provider(custom_llm_spec)
        
        # Register a custom non-LLM provider
        custom_tool_spec = DynamicProviderSpec(
            name="custom_tool",
            requires_api_key=False,
            description="Custom tool provider for testing",
            category="TOOL",
            is_llm_provider=False,
            provider_type="local"
        )
        self.registry.register_provider(custom_tool_spec)
        
        # Test LLM provider filtering
        llm_providers = self.provider_manager.get_llm_providers()
        assert "custom_llm" in llm_providers, \
            "Custom LLM provider should be in LLM providers list"
        assert "custom_tool" not in llm_providers, \
            "Custom tool provider should not be in LLM providers list"
        
        # Test non-LLM provider filtering
        non_llm_providers = self.provider_manager.get_non_llm_providers()
        assert "custom_tool" in non_llm_providers, \
            "Custom tool provider should be in non-LLM providers list"
        assert "custom_llm" not in non_llm_providers, \
            "Custom LLM provider should not be in non-LLM providers list"
    
    def test_provider_capabilities_categorization(self):
        """Test that provider capabilities are correctly categorized."""
        # Test LLM provider capabilities
        openai_info = self.provider_manager.get_provider_info("openai")
        assert "streaming" in openai_info["capabilities"], \
            "OpenAI should have streaming capability"
        assert "function_calling" in openai_info["capabilities"], \
            "OpenAI should have function_calling capability"
        
        # Test CopilotKit capabilities (should be different from LLM capabilities)
        copilotkit_info = self.provider_manager.get_provider_info("copilotkit")
        assert "ui_assistance" in copilotkit_info["capabilities"], \
            "CopilotKit should have ui_assistance capability"
        assert "code_suggestions" in copilotkit_info["capabilities"], \
            "CopilotKit should have code_suggestions capability"
        assert "development_tools" in copilotkit_info["capabilities"], \
            "CopilotKit should have development_tools capability"
        
        # CopilotKit should not have typical LLM capabilities
        assert "streaming" not in copilotkit_info["capabilities"], \
            "CopilotKit should not have streaming capability (it's not an LLM)"
        assert "function_calling" not in copilotkit_info["capabilities"], \
            "CopilotKit should not have function_calling capability (it's not an LLM)"


# Note: API endpoint tests are handled separately in integration tests
# since they require the full FastAPI application context


if __name__ == "__main__":
    pytest.main([__file__])