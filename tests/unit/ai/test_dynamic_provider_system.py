"""
Tests for Dynamic Provider System

This module tests the dynamic provider system functionality including:
- Provider registration and discovery
- API key validation
- Model discovery
- LLM profile management
- Provider filtering (excluding CopilotKit from LLM providers)
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.integrations.dynamic_provider_system import (
    DynamicProviderSpec,
    DynamicProviderManager,
    get_dynamic_provider_manager
)
from ai_karen_engine.integrations.llm_profile_system import (
    LLMProfile,
    LLMProfileManager,
    RouterPolicy,
    ProviderPreference,
    get_profile_manager
)


class TestDynamicProviderSystem:
    """Test the dynamic provider system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider_manager = DynamicProviderManager()
    
    def test_provider_registration(self):
        """Test that providers are registered correctly."""
        providers = self.provider_manager.registry.list_providers()
        
        # Check that core providers are registered
        assert "openai" in providers
        assert "gemini" in providers
        assert "deepseek" in providers
        assert "huggingface" in providers
        assert "local" in providers
        assert "copilotkit" in providers
    
    def test_llm_provider_filtering(self):
        """Test that LLM providers are correctly filtered (excluding CopilotKit)."""
        llm_providers = self.provider_manager.get_llm_providers()
        non_llm_providers = self.provider_manager.get_non_llm_providers()
        
        # CopilotKit should not be in LLM providers
        assert "copilotkit" not in llm_providers
        assert "copilotkit" in non_llm_providers
        
        # Other providers should be in LLM providers
        assert "openai" in llm_providers
        assert "gemini" in llm_providers
        assert "deepseek" in llm_providers
        assert "local" in llm_providers
    
    def test_provider_info(self):
        """Test getting provider information."""
        openai_info = self.provider_manager.get_provider_info("openai")
        
        assert openai_info["name"] == "openai"
        assert openai_info["requires_api_key"] is True
        assert openai_info["is_llm_provider"] is True
        assert openai_info["provider_type"] == "remote"
        assert "streaming" in openai_info["capabilities"]
        
        # Test CopilotKit info
        copilotkit_info = self.provider_manager.get_provider_info("copilotkit")
        assert copilotkit_info["is_llm_provider"] is False
        assert copilotkit_info["category"] == "UI_FRAMEWORK"
    
    @pytest.mark.asyncio
    async def test_api_key_validation(self):
        """Test API key validation."""
        # Test valid API key (mocked)
        with patch.object(self.provider_manager, '_perform_api_key_validation') as mock_validate:
            mock_validate.return_value = {"valid": True, "message": "API key is valid"}
            
            result = await self.provider_manager.validate_api_key("openai", {"api_key": "test-key"})
            
            assert result["valid"] is True
            assert result["message"] == "API key is valid"
        
        # Test invalid API key
        with patch.object(self.provider_manager, '_perform_api_key_validation') as mock_validate:
            mock_validate.return_value = {"valid": False, "message": "Invalid API key"}
            
            result = await self.provider_manager.validate_api_key("openai", {"api_key": "invalid-key"})
            
            assert result["valid"] is False
            assert result["message"] == "Invalid API key"
        
        # Test provider that doesn't require API key
        result = await self.provider_manager.validate_api_key("local", {})
        assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_model_discovery(self):
        """Test model discovery functionality."""
        # Test local model discovery
        with patch.object(self.provider_manager, '_discover_local_models') as mock_discover:
            mock_discover.return_value = [
                {
                    "id": "test-model",
                    "name": "Test Model",
                    "family": "llama",
                    "format": "gguf",
                    "capabilities": ["text"]
                }
            ]
            
            models = await self.provider_manager.discover_models("local")
            
            assert len(models) == 1
            assert models[0]["id"] == "test-model"
            assert models[0]["family"] == "llama"
        
        # Test remote model discovery fallback
        models = await self.provider_manager.discover_models("openai")
        
        # Should return fallback models
        assert len(models) > 0
        assert any(model["id"] == "gpt-4o" for model in models)
    
    def test_health_check(self):
        """Test provider health checking."""
        # Test local provider health
        health = self.provider_manager.health_check("local")
        assert health["status"] == "healthy"
        
        # Test remote provider health (mocked)
        health = self.provider_manager.health_check("openai")
        assert health["status"] in ["healthy", "unhealthy", "unknown"]
    
    def test_model_list_parsers(self):
        """Test model list parsing functions."""
        # Test OpenAI model parsing
        openai_response = {
            "data": [
                {"id": "gpt-4", "object": "model"},
                {"id": "gpt-3.5-turbo", "object": "model"},
                {"id": "text-davinci-003", "object": "model"}  # Should be filtered out
            ]
        }
        
        models = self.provider_manager._parse_openai_models(openai_response)
        
        # Should only include GPT models
        assert len(models) == 2
        assert any(model["id"] == "gpt-4" for model in models)
        assert any(model["id"] == "gpt-3.5-turbo" for model in models)
        assert not any(model["id"] == "text-davinci-003" for model in models)
    
    def test_context_length_estimation(self):
        """Test context length estimation."""
        assert self.provider_manager._estimate_context_length("gpt-4") == 8192
        assert self.provider_manager._estimate_context_length("gpt-4-turbo") == 128000
        assert self.provider_manager._estimate_context_length("gpt-3.5-turbo") == 4096
        assert self.provider_manager._estimate_context_length("gemini-1.5-pro") == 2097152
        assert self.provider_manager._estimate_context_length("unknown-model") == 4096


class TestLLMProfileSystem:
    """Test the LLM profile system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a temporary directory for testing
        import tempfile
        from pathlib import Path
        
        self.temp_dir = Path(tempfile.mkdtemp())
        self.profile_manager = LLMProfileManager(profiles_dir=self.temp_dir)
    
    def test_default_profiles_creation(self):
        """Test that default profiles are created."""
        profiles = self.profile_manager.list_profiles()
        
        assert len(profiles) > 0
        
        # Check that we have expected default profiles
        profile_names = [p.name for p in profiles]
        assert "Balanced" in profile_names
        assert "Performance" in profile_names
        assert "Quality" in profile_names
        assert "Privacy" in profile_names
    
    def test_profile_creation(self):
        """Test creating a new profile."""
        profile = self.profile_manager.create_profile(
            name="Test Profile",
            description="A test profile",
            router_policy=RouterPolicy.PERFORMANCE
        )
        
        assert profile.name == "Test Profile"
        assert profile.description == "A test profile"
        assert profile.router_policy == RouterPolicy.PERFORMANCE
        assert profile.id == "test_profile"
    
    def test_profile_update(self):
        """Test updating a profile."""
        # Create a profile first
        profile = self.profile_manager.create_profile(
            name="Update Test",
            description="Original description"
        )
        
        # Update it
        updated_profile = self.profile_manager.update_profile(
            profile.id,
            description="Updated description",
            temperature=0.5
        )
        
        assert updated_profile.description == "Updated description"
        assert updated_profile.temperature == 0.5
        assert updated_profile.updated_at > profile.created_at
    
    def test_profile_switching(self):
        """Test switching between profiles."""
        # Create a test profile
        test_profile = self.profile_manager.create_profile(
            name="Switch Test",
            router_policy=RouterPolicy.PRIVACY
        )
        
        # Switch to it
        active_profile = self.profile_manager.switch_profile(test_profile.id)
        
        assert active_profile.id == test_profile.id
        assert self.profile_manager.get_active_profile().id == test_profile.id
    
    def test_profile_validation(self):
        """Test profile validation."""
        # Create a profile with invalid provider
        profile = self.profile_manager.create_profile(
            name="Invalid Test",
            providers={
                "chat": ProviderPreference(
                    provider="nonexistent_provider",
                    priority=80
                )
            }
        )
        
        validation_result = self.profile_manager.validate_profile_compatibility(profile)
        
        assert validation_result["compatible"] is False
        assert len(validation_result["issues"]) > 0
        assert "nonexistent_provider" in str(validation_result["issues"])
    
    def test_profile_serialization(self):
        """Test profile serialization and deserialization."""
        # Create a profile with complex configuration
        original_profile = self.profile_manager.create_profile(
            name="Serialization Test",
            providers={
                "chat": ProviderPreference(
                    provider="openai",
                    model="gpt-4",
                    priority=90,
                    required_capabilities={"streaming", "function_calling"}
                )
            }
        )
        
        # Convert to dict and back
        profile_dict = original_profile.to_dict()
        restored_profile = LLMProfile.from_dict(profile_dict)
        
        assert restored_profile.name == original_profile.name
        assert restored_profile.router_policy == original_profile.router_policy
        assert "chat" in restored_profile.providers
        assert restored_profile.providers["chat"].provider == "openai"
        assert restored_profile.providers["chat"].model == "gpt-4"
        assert "streaming" in restored_profile.providers["chat"].required_capabilities
    
    def test_profile_deletion(self):
        """Test profile deletion."""
        # Create a profile
        profile = self.profile_manager.create_profile(name="Delete Test")
        profile_id = profile.id
        
        # Verify it exists
        assert self.profile_manager.get_profile(profile_id) is not None
        
        # Delete it
        success = self.profile_manager.delete_profile(profile_id)
        
        assert success is True
        assert self.profile_manager.get_profile(profile_id) is None
    
    def test_cannot_delete_active_profile(self):
        """Test that active profile cannot be deleted."""
        active_profile = self.profile_manager.get_active_profile()
        
        with pytest.raises(ValueError, match="Cannot delete the active profile"):
            self.profile_manager.delete_profile(active_profile.id)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestIntegration:
    """Test integration between provider system and profile system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider_manager = get_dynamic_provider_manager()
        
        import tempfile
        from pathlib import Path
        self.temp_dir = Path(tempfile.mkdtemp())
        self.profile_manager = LLMProfileManager(profiles_dir=self.temp_dir)
    
    def test_profile_provider_compatibility(self):
        """Test that profiles are validated against available providers."""
        # Get available LLM providers
        llm_providers = self.provider_manager.get_llm_providers()
        
        # Create a profile using available providers
        valid_profile = self.profile_manager.create_profile(
            name="Valid Integration Test",
            providers={
                "chat": ProviderPreference(
                    provider=llm_providers[0] if llm_providers else "local",
                    priority=80
                )
            }
        )
        
        validation_result = self.profile_manager.validate_profile_compatibility(valid_profile)
        assert validation_result["compatible"] is True
    
    def test_copilotkit_exclusion_in_profiles(self):
        """Test that CopilotKit is not suggested for LLM profiles."""
        llm_providers = self.provider_manager.get_llm_providers()
        
        # CopilotKit should not be in the list of LLM providers
        assert "copilotkit" not in llm_providers
        
        # But it should be available as a non-LLM provider
        non_llm_providers = self.provider_manager.get_non_llm_providers()
        assert "copilotkit" in non_llm_providers
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])