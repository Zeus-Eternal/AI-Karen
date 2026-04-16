#!/usr/bin/env python3
"""
Debug script to test llama.cpp provider directly
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from ai_karen_engine.integrations.llm_registry import get_registry


def test_llama_direct():
    registry = get_registry()

    # Test getting the provider directly
    print("Getting llama.cpp provider...")
    provider = registry.get_provider("llamacpp")

    if not provider:
        print("ERROR: Could not get llama.cpp provider")
        return

    print("Provider obtained successfully")
    print(f"Provider info: {provider.get_provider_info()}")

    # Test with a very simple prompt
    print("\nTesting with simple prompt...")
    try:
        response = provider.generate_text("Hello")
        print(f"Simple response: '{response}'")
    except Exception as e:
        print(f"Simple prompt failed: {e}")

    # Test with different parameters
    print("\nTesting with parameters...")
    try:
        response = provider.generate_text(
            "Hello, how are you?", max_tokens=50, temperature=0.7
        )
        print(f"Parameterized response: '{response}'")
    except Exception as e:
        print(f"Parameterized prompt failed: {e}")

    # Test with messages format
    print("\nTesting with messages format...")
    try:
        messages = [
            {
                "role": "user",
                "content": "Hello! Can you tell me a fun fact about space?",
            }
        ]
        response = provider.generate_text(messages, max_tokens=100, temperature=0.8)
        print(f"Messages response: '{response}'")
    except Exception as e:
        print(f"Messages format failed: {e}")


def test_model_loading():
    registry = get_registry()
    provider = registry.get_provider("llamacpp")

    # Check what models are available
    print("Available models:")
    models = provider.get_models() if provider else []
    for model in models:
        print(f"  - {model}")

    # Try to load a different model
    if len(models) > 1 and provider:
        print(f"\nTrying to load {models[1]}...")
        try:
            success = provider.load_model_by_id(models[1])
            print(f"Load result: {success}")
            if success:
                response = provider.generate_text("Hello")
                print(f"New model response: '{response}'")
        except Exception as e:
            print(f"Failed to load alternative model: {e}")


if __name__ == "__main__":
    test_llama_direct()
    test_model_loading()
