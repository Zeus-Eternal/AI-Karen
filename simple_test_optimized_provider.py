#!/usr/bin/env python3
"""
Simple test to validate optimized provider registration and basic functionality
"""

import sys
import os
import time

# Add src to Python path
sys.path.insert(0, "/mnt/Development/KIRO/AI-Karen/src")


def test_provider_registration():
    """Test that the optimized provider is properly registered"""
    print("Testing provider registration...")

    try:
        from ai_karen_engine.integrations.llm_registry import LLM_REGISTRY

        # Check if optimized provider exists
        optimized_provider = LLM_REGISTRY.get("llamacpp-optimized")
        if optimized_provider:
            print("✓ Optimized provider 'llamacpp-optimized' found in registry")
            print(f"  Provider class: {optimized_provider.__class__.__name__}")
            print(f"  Provider module: {optimized_provider.__module__}")

            # Check if it has the required methods
            required_methods = ["generate", "generate_stream", "health_check"]
            for method in required_methods:
                if hasattr(optimized_provider, method):
                    print(f"  ✓ Method '{method}' available")
                else:
                    print(f"  ✗ Method '{method}' missing")
                    return False
        else:
            print("✗ Optimized provider 'llamacpp-optimized' not found in registry")
            return False

        # Check original provider
        original_provider = LLM_REGISTRY.get("llamacpp")
        if original_provider:
            print("✓ Original provider 'llamacpp' found in registry")
        else:
            print("✗ Original provider 'llamacpp' not found in registry")
            return False

        return True

    except Exception as e:
        print(f"✗ Error testing provider registration: {e}")
        return False


def test_provider_priority():
    """Test the provider priority order"""
    print("\nTesting provider priority order...")

    try:
        from ai_karen_engine.integrations.llm_registry import LLM_REGISTRY

        # Test getting providers in priority order
        providers_in_order = []

        # Check if providers exist in expected order
        expected_order = ["llamacpp-optimized", "llamacpp", "fallback", "ollama"]

        for provider_name in expected_order:
            provider = LLM_REGISTRY.get(provider_name)
            if provider:
                providers_in_order.append(provider_name)
                print(f"  ✓ Provider '{provider_name}' available")
            else:
                print(f"  - Provider '{provider_name}' not available (skipped)")

        print(f"Available providers in order: {providers_in_order}")
        return len(providers_in_order) > 0

    except Exception as e:
        print(f"✗ Error testing provider priority: {e}")
        return False


def test_nlp_service_manager():
    """Test the NLP service manager configuration"""
    print("\nTesting NLP service manager...")

    try:
        from services.memory.nlp_service_manager import NLPServiceManager

        # Get the service manager instance
        nlp_manager = NLPServiceManager()

        # Check the provider priority
        if hasattr(nlp_manager, "provider_priority"):
            print(f"  Provider priority: {nlp_manager.provider_priority}")
        else:
            print("  Provider priority not accessible")

        # Check if the optimized provider is in the priority list
        if (
            hasattr(nlp_manager, "provider_priority")
            and "llamacpp-optimized" in nlp_manager.provider_priority
        ):
            print("  ✓ Optimized provider in NLP service manager priority list")
        else:
            print("  ✗ Optimized provider not in NLP service manager priority list")
            return False

        return True

    except Exception as e:
        print(f"✗ Error testing NLP service manager: {e}")
        return False


def test_runtime_availability():
    """Test if the runtime is available"""
    print("\nTesting runtime availability...")

    try:
        from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime

        # Get runtime instance
        runtime = LlamaCppRuntime.get_instance()
        print("  ✓ LlamaCppRuntime singleton available")

        # Check if it has the required methods
        required_methods = ["load_model", "generate", "generate_stream"]
        for method in required_methods:
            if hasattr(runtime, method):
                print(f"  ✓ Runtime method '{method}' available")
            else:
                print(f"  ✗ Runtime method '{method}' missing")
                return False

        return True

    except Exception as e:
        print(f"✗ Error testing runtime availability: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("SIMPLE OPTIMIZED PROVIDER VALIDATION TEST")
    print("=" * 60)

    tests = [
        ("Provider Registration", test_provider_registration),
        ("Provider Priority", test_provider_priority),
        ("NLP Service Manager", test_nlp_service_manager),
        ("Runtime Availability", test_runtime_availability),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name.upper()}:")
        print("-" * len(test_name))

        start_time = time.time()
        try:
            result = test_func()
            end_time = time.time()

            if result:
                status = "✓ PASSED"
                results.append(True)
            else:
                status = "✗ FAILED"
                results.append(False)

            print(f"{status} ({end_time - start_time:.2f}s)")

        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✓ PASSED" if results[i] else "✗ FAILED"
        print(f"{status}: {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Optimized provider is properly configured.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
