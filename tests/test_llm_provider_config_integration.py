#!/usr/bin/env python3
"""
Integration test for LLM Provider Configuration Management

This script tests the enhanced configuration management system to ensure:
- Provider configurations are loaded correctly
- Runtime switching works
- Authentication validation functions
- Startup validation provides useful feedback
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_karen_engine.config.llm_provider_config import (
    LLMProviderConfigManager,
    ProviderConfig,
    ProviderType,
    AuthenticationType
)
from ai_karen_engine.config.runtime_provider_manager import (
    RuntimeProviderManager,
    ProviderSelectionCriteria,
    RequestType
)
from ai_karen_engine.config.provider_authentication import (
    ProviderAuthenticationManager,
    SecureStorageBackend
)
from ai_karen_engine.config.startup_validation import StartupValidationService


async def test_provider_configuration():
    """Test provider configuration management"""
    print("Testing Provider Configuration Management...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "providers"
        
        # Initialize manager with test directory
        config_manager = LLMProviderConfigManager(config_dir)
        
        # Test: List default providers
        providers = config_manager.list_providers()
        print(f"✓ Loaded {len(providers)} default providers")
        
        # Test: Get specific provider
        openai_config = config_manager.get_provider("openai")
        assert openai_config is not None, "OpenAI provider should exist"
        assert openai_config.name == "openai", "Provider name should match"
        print("✓ Retrieved OpenAI provider configuration")
        
        # Test: Update provider configuration
        updated_config = config_manager.update_provider("openai", {"priority": 95})
        assert updated_config.priority == 95, "Priority should be updated"
        print("✓ Updated provider configuration")
        
        # Test: Environment variable override
        os.environ["KARI_OPENAI_ENABLED"] = "false"
        config_manager._apply_env_overrides(openai_config)
        assert not openai_config.enabled, "Provider should be disabled by env var"
        print("✓ Environment variable override works")
        
        # Clean up
        del os.environ["KARI_OPENAI_ENABLED"]
        
        return True


async def test_runtime_provider_management():
    """Test runtime provider management"""
    print("\nTesting Runtime Provider Management...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "providers"
        
        # Initialize managers
        config_manager = LLMProviderConfigManager(config_dir)
        runtime_manager = RuntimeProviderManager(health_check_interval=60)
        
        # Test: Provider selection
        criteria = ProviderSelectionCriteria(
            request_type=RequestType.CHAT,
            preferred_providers=["ollama", "openai"],
            require_streaming=True
        )
        
        selected_provider = runtime_manager.select_provider(criteria)
        print(f"✓ Selected provider for chat: {selected_provider}")
        
        # Test: Enable/disable provider
        success = runtime_manager.enable_provider("gemini")
        assert success, "Should be able to enable provider"
        print("✓ Enabled provider at runtime")
        
        success = runtime_manager.disable_provider("gemini")
        assert success, "Should be able to disable provider"
        print("✓ Disabled provider at runtime")
        
        # Test: Set provider priority
        success = runtime_manager.set_provider_priority("openai", 100)
        assert success, "Should be able to set priority"
        print("✓ Set provider priority at runtime")
        
        # Test: Get runtime status
        status = runtime_manager.get_runtime_status()
        assert "total_providers" in status, "Status should include provider count"
        print(f"✓ Runtime status: {status['total_providers']} total providers")
        
        return True


async def test_provider_authentication():
    """Test provider authentication management"""
    print("\nTesting Provider Authentication...")
    
    # Initialize with memory backend for testing
    auth_manager = ProviderAuthenticationManager(
        storage_backend=SecureStorageBackend.MEMORY,
        cache_duration=60
    )
    
    # Test: Store API key
    test_api_key = "test-api-key-12345"
    success = auth_manager.store_api_key("openai", test_api_key, {"test": True})
    assert success, "Should be able to store API key"
    print("✓ Stored API key securely")
    
    # Test: Retrieve API key
    retrieved_key = auth_manager.get_api_key("openai")
    assert retrieved_key == test_api_key, "Retrieved key should match stored key"
    print("✓ Retrieved API key successfully")
    
    # Test: List stored keys
    stored_keys = auth_manager.list_stored_keys()
    assert "openai" in stored_keys, "OpenAI should be in stored keys"
    print("✓ Listed stored keys")
    
    # Test: Get key info
    key_info = auth_manager.get_key_info("openai")
    assert key_info is not None, "Key info should exist"
    assert key_info.provider_name == "openai", "Provider name should match"
    print("✓ Retrieved key information")
    
    # Test: Authentication summary
    summary = auth_manager.get_authentication_summary()
    assert summary["stored_keys"] == 1, "Should have 1 stored key"
    print(f"✓ Authentication summary: {summary['stored_keys']} stored keys")
    
    # Test: Remove API key
    success = auth_manager.remove_api_key("openai")
    assert success, "Should be able to remove API key"
    print("✓ Removed API key")
    
    return True


async def test_startup_validation():
    """Test startup validation service"""
    print("\nTesting Startup Validation...")
    
    validation_service = StartupValidationService()
    
    # Test: Run startup validation
    results = await validation_service.validate_startup()
    
    assert "overall_status" in results, "Results should include overall status"
    assert "provider_count" in results, "Results should include provider count"
    assert "recommendations" in results, "Results should include recommendations"
    
    print(f"✓ Startup validation completed with status: {results['overall_status']}")
    print(f"✓ Found {results['provider_count']} providers, {results['enabled_count']} enabled")
    
    # Test: Get user-friendly message
    message = validation_service.get_user_friendly_status_message(results)
    assert isinstance(message, str), "Should return a string message"
    print(f"✓ Status message: {message}")
    
    # Test: Get setup instructions
    instructions = validation_service.get_setup_instructions(results)
    assert isinstance(instructions, list), "Should return a list of instructions"
    print(f"✓ Setup instructions: {len(instructions)} steps")
    
    return True


async def main():
    """Run all integration tests"""
    print("LLM Provider Configuration Integration Tests")
    print("=" * 50)
    
    try:
        # Run all tests
        await test_provider_configuration()
        await test_runtime_provider_management()
        await test_provider_authentication()
        await test_startup_validation()
        
        print("\n" + "=" * 50)
        print("✅ All integration tests passed!")
        print("\nThe enhanced LLM provider configuration management system is working correctly:")
        print("- Provider configurations are loaded and managed properly")
        print("- Runtime provider switching functions correctly")
        print("- Authentication management works with secure storage")
        print("- Startup validation provides comprehensive feedback")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)