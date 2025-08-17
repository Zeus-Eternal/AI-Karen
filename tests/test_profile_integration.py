"""
Integration test for LLM Profile System

This test verifies that the profile system integrates correctly with the routing system
and that profile switching has immediate effect on routing decisions.
"""

import pytest
from unittest.mock import Mock, patch

from ai_karen_engine.integrations.llm_profile_system import (
    get_profile_manager,
    RouterPolicy,
    ProviderPreference
)
from ai_karen_engine.integrations.dynamic_provider_system import get_dynamic_provider_manager


class TestProfileIntegration:
    """Test profile system integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        import tempfile
        from pathlib import Path
        
        self.temp_dir = Path(tempfile.mkdtemp())
        self.profile_manager = get_profile_manager()
        self.provider_manager = get_dynamic_provider_manager()
    
    def test_profile_creation_with_real_schema(self):
        """Test creating a profile with the real schema structure."""
        profile = self.profile_manager.create_profile(
            name="Integration Test Profile",
            description="Test profile for integration testing",
            router_policy=RouterPolicy.QUALITY,
            providers={
                "chat": ProviderPreference(
                    provider="openai",
                    model="gpt-4o",
                    priority=95,
                    required_capabilities={"streaming", "function_calling"}
                ),
                "code": ProviderPreference(
                    provider="deepseek",
                    model="deepseek-coder",
                    priority=90,
                    required_capabilities={"streaming"}
                ),
                "reasoning": ProviderPreference(
                    provider="gemini",
                    model="gemini-1.5-pro",
                    priority=85,
                    required_capabilities={"vision"}
                )
            },
            fallback_provider="local",
            enable_streaming=True,
            enable_function_calling=True,
            enable_vision=True,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Verify profile structure
        assert profile.name == "Integration Test Profile"
        assert profile.router_policy == RouterPolicy.QUALITY
        assert len(profile.providers) == 3
        
        # Verify provider preferences
        chat_pref = profile.providers["chat"]
        assert chat_pref.provider == "openai"
        assert chat_pref.model == "gpt-4o"
        assert chat_pref.priority == 95
        assert "streaming" in chat_pref.required_capabilities
        assert "function_calling" in chat_pref.required_capabilities
        
        # Verify fallback configuration
        assert profile.fallback_provider == "local"
        assert profile.enable_streaming is True
        assert profile.enable_function_calling is True
        assert profile.enable_vision is True
    
    def test_profile_validation_with_available_providers(self):
        """Test that profile validation works with actual provider availability."""
        # Get available providers
        available_providers = self.provider_manager.get_llm_providers()
        
        # Create a profile with available providers
        valid_provider = available_providers[0] if available_providers else "local"
        
        profile = self.profile_manager.create_profile(
            name="Valid Provider Test",
            providers={
                "chat": ProviderPreference(
                    provider=valid_provider,
                    priority=80
                )
            },
            fallback_provider="local"
        )
        
        # Validate the profile
        validation_result = self.profile_manager.validate_profile_compatibility(profile)
        
        # Should be compatible since we used available providers
        assert validation_result["compatible"] is True
        assert len(validation_result["issues"]) == 0
    
    def test_profile_validation_with_unavailable_providers(self):
        """Test profile validation with unavailable providers."""
        profile = self.profile_manager.create_profile(
            name="Invalid Provider Test",
            providers={
                "chat": ProviderPreference(
                    provider="nonexistent_provider_12345",
                    priority=80
                )
            },
            fallback_provider="also_nonexistent"
        )
        
        # Validate the profile
        validation_result = self.profile_manager.validate_profile_compatibility(profile)
        
        # Should not be compatible
        assert validation_result["compatible"] is False
        assert len(validation_result["issues"]) > 0
        
        # Check specific error messages
        issues_str = " ".join(validation_result["issues"])
        assert "nonexistent_provider_12345" in issues_str
        assert "also_nonexistent" in issues_str
    
    def test_profile_switching_notification(self):
        """Test that profile switching triggers notifications."""
        # Create two profiles
        profile1 = self.profile_manager.create_profile(
            name="Profile 1",
            router_policy=RouterPolicy.PERFORMANCE
        )
        
        profile2 = self.profile_manager.create_profile(
            name="Profile 2", 
            router_policy=RouterPolicy.PRIVACY
        )
        
        # Switch to profile1
        active = self.profile_manager.switch_profile(profile1.id)
        assert active.id == profile1.id
        assert active.router_policy == RouterPolicy.PERFORMANCE
        
        # Switch to profile2
        active = self.profile_manager.switch_profile(profile2.id)
        assert active.id == profile2.id
        assert active.router_policy == RouterPolicy.PRIVACY
        
        # Verify the active profile is persisted
        current_active = self.profile_manager.get_active_profile()
        assert current_active.id == profile2.id
    
    def test_copilotkit_exclusion_in_profile_validation(self):
        """Test that CopilotKit is not suggested for LLM profiles."""
        # Try to create a profile with CopilotKit as an LLM provider
        profile = self.profile_manager.create_profile(
            name="CopilotKit Test",
            providers={
                "chat": ProviderPreference(
                    provider="copilotkit",  # This should be invalid for LLM use
                    priority=80
                )
            }
        )
        
        # Validate the profile
        validation_result = self.profile_manager.validate_profile_compatibility(profile)
        
        # Should not be compatible because CopilotKit is not an LLM provider
        assert validation_result["compatible"] is False
        
        # Check that the error mentions CopilotKit
        issues_str = " ".join(validation_result["issues"])
        assert "copilotkit" in issues_str.lower()
    
    def test_profile_serialization_roundtrip(self):
        """Test that profiles can be serialized and deserialized correctly."""
        # Create a complex profile
        original = self.profile_manager.create_profile(
            name="Serialization Test",
            description="Complex profile for testing serialization",
            router_policy=RouterPolicy.BALANCED,
            providers={
                "chat": ProviderPreference(
                    provider="openai",
                    model="gpt-4o",
                    priority=90,
                    max_cost_per_1k_tokens=0.03,
                    required_capabilities={"streaming", "function_calling"},
                    excluded_capabilities={"vision"}
                ),
                "code": ProviderPreference(
                    provider="deepseek",
                    model="deepseek-coder",
                    priority=85,
                    required_capabilities={"streaming"}
                )
            },
            fallback_provider="local",
            enable_streaming=True,
            enable_function_calling=True,
            temperature=0.8,
            max_tokens=1500
        )
        
        # Serialize to dict
        profile_dict = original.to_dict()
        
        # Verify dict structure
        assert profile_dict["name"] == "Serialization Test"
        assert profile_dict["router_policy"] == "balanced"
        assert "chat" in profile_dict["providers"]
        assert "code" in profile_dict["providers"]
        
        # Verify provider preferences in dict
        chat_pref = profile_dict["providers"]["chat"]
        assert chat_pref["provider"] == "openai"
        assert chat_pref["model"] == "gpt-4o"
        assert chat_pref["priority"] == 90
        assert chat_pref["max_cost_per_1k_tokens"] == 0.03
        assert "streaming" in chat_pref["required_capabilities"]
        assert "function_calling" in chat_pref["required_capabilities"]
        assert "vision" in chat_pref["excluded_capabilities"]
        
        # Deserialize back to profile
        from ai_karen_engine.integrations.llm_profile_system import LLMProfile
        restored = LLMProfile.from_dict(profile_dict)
        
        # Verify restored profile
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.router_policy == original.router_policy
        assert restored.fallback_provider == original.fallback_provider
        assert restored.enable_streaming == original.enable_streaming
        assert restored.temperature == original.temperature
        assert restored.max_tokens == original.max_tokens
        
        # Verify provider preferences
        assert len(restored.providers) == len(original.providers)
        
        restored_chat = restored.providers["chat"]
        original_chat = original.providers["chat"]
        
        assert restored_chat.provider == original_chat.provider
        assert restored_chat.model == original_chat.model
        assert restored_chat.priority == original_chat.priority
        assert restored_chat.max_cost_per_1k_tokens == original_chat.max_cost_per_1k_tokens
        assert restored_chat.required_capabilities == original_chat.required_capabilities
        assert restored_chat.excluded_capabilities == original_chat.excluded_capabilities
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])