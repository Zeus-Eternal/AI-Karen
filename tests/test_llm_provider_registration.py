#!/usr/bin/env python3
"""
Test script to verify LLM provider registration and basic functionality.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.integrations.llm_utils import get_llm_manager
from ai_karen_engine.integrations.startup import initialize_llm_providers, validate_provider_configuration


def test_provider_registration():
    """Test that all providers are properly registered."""
    print("🔍 Testing LLM Provider Registration...")
    
    # Initialize providers
    init_result = initialize_llm_providers()
    print(f"Initialization result: {init_result}")
    
    # Get registry
    registry = get_registry()
    
    # Check registered providers
    providers = registry.list_providers()
    expected_providers = ["llama-cpp", "openai", "gemini", "deepseek", "huggingface"]
    
    print(f"\n📋 Registered providers: {providers}")
    
    # Verify all expected providers are registered
    missing_providers = set(expected_providers) - set(providers)
    if missing_providers:
        print(f"❌ Missing providers: {missing_providers}")
        return False
    
    print("✅ All expected providers are registered")
    
    # Test provider info retrieval
    print("\n📊 Provider Information:")
    for provider_name in providers:
        info = registry.get_provider_info(provider_name)
        if info:
            print(f"  {provider_name}:")
            print(f"    Description: {info.get('description', 'N/A')}")
            print(f"    Supports streaming: {info.get('supports_streaming', False)}")
            print(f"    Supports embeddings: {info.get('supports_embeddings', False)}")
            print(f"    Requires API key: {info.get('requires_api_key', False)}")
            print(f"    Default model: {info.get('default_model', 'N/A')}")
        else:
            print(f"  {provider_name}: ❌ No info available")
    
    return True


def test_provider_health_checks():
    """Test provider health checks."""
    print("\n🏥 Testing Provider Health Checks...")
    
    registry = get_registry()
    health_results = registry.health_check_all()
    
    print("Health check results:")
    for provider_name, health in health_results.items():
        status = health.get("status", "unknown")
        if status == "healthy":
            print(f"  ✅ {provider_name}: {status}")
        elif status == "unhealthy":
            error = health.get("error", "Unknown error")
            print(f"  ❌ {provider_name}: {status} - {error}")
        else:
            print(f"  ❓ {provider_name}: {status}")
    
    return health_results


def test_llm_manager_integration():
    """Test LLM manager integration with registry."""
    print("\n🔧 Testing LLM Manager Integration...")
    
    try:
        # Create LLM manager with registry
        manager = get_llm_manager(use_registry=True)
        
        # Test listing available providers
        available = manager.list_available_providers()
        print(f"Available providers via manager: {available}")
        
        # Test auto-selection
        auto_selected = manager.auto_select_provider()
        print(f"Auto-selected provider: {auto_selected}")
        
        # Test getting provider instances (without making actual calls)
        for provider_name in available[:2]:  # Test first 2 providers
            try:
                provider = manager.get_provider(provider_name)
                if provider:
                    provider_info = provider.get_provider_info()
                    print(f"  ✅ {provider_name}: Successfully created instance")
                    print(f"    Provider info: {provider_info.get('name', 'N/A')}")
                else:
                    print(f"  ❌ {provider_name}: Failed to create instance")
            except Exception as ex:
                print(f"  ⚠️ {provider_name}: {ex}")
        
        return True
        
    except Exception as ex:
        print(f"❌ LLM Manager integration failed: {ex}")
        return False


def test_configuration_validation():
    """Test provider configuration validation."""
    print("\n⚙️ Testing Configuration Validation...")
    
    validation_results = validate_provider_configuration()
    
    print("Configuration validation results:")
    for provider_name, result in validation_results.items():
        status = result["status"]
        message = result["message"]
        
        if status == "valid":
            print(f"  ✅ {provider_name}: {message}")
        elif status == "warning":
            print(f"  ⚠️ {provider_name}: {message}")
        else:
            print(f"  ❌ {provider_name}: {message}")
    
    return validation_results


def test_provider_models():
    """Test getting available models from providers."""
    print("\n📚 Testing Provider Models...")
    
    registry = get_registry()
    
    for provider_name in registry.list_providers():
        try:
            provider = registry.get_provider(provider_name)
            if provider and hasattr(provider, 'get_models'):
                models = provider.get_models()
                print(f"  {provider_name}: {len(models)} models available")
                if models:
                    print(f"    Sample models: {models[:3]}")  # Show first 3
            else:
                print(f"  {provider_name}: No model listing available")
        except Exception as ex:
            print(f"  {provider_name}: Error getting models - {ex}")


async def main():
    """Main test function."""
    print("🚀 Starting LLM Provider Registration Tests\n")
    
    # Test 1: Provider Registration
    registration_ok = test_provider_registration()
    
    # Test 2: Health Checks
    health_results = test_provider_health_checks()
    
    # Test 3: LLM Manager Integration
    manager_ok = test_llm_manager_integration()
    
    # Test 4: Configuration Validation
    config_results = test_configuration_validation()
    
    # Test 5: Provider Models
    test_provider_models()
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"  Provider Registration: {'✅ PASS' if registration_ok else '❌ FAIL'}")
    print(f"  LLM Manager Integration: {'✅ PASS' if manager_ok else '❌ FAIL'}")
    
    # Count healthy providers
    healthy_count = sum(1 for h in health_results.values() if h.get("status") == "healthy")
    total_count = len(health_results)
    print(f"  Healthy Providers: {healthy_count}/{total_count}")
    
    # Count valid configurations
    valid_count = sum(1 for r in config_results.values() if r.get("status") == "valid")
    total_configs = len(config_results)
    print(f"  Valid Configurations: {valid_count}/{total_configs}")
    
    if registration_ok and manager_ok:
        print("\n🎉 All core tests passed! LLM provider system is working.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)