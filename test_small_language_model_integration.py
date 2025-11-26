#!/usr/bin/env python3
"""
Simple integration test for SmallLanguageModelService and LLM Orchestrator.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ai_karen_engine.services.small_language_model_service import SmallLanguageModelService, SmallLanguageModelConfig
    from ai_karen_engine.llm_orchestrator import LLMOrchestrator
    from ai_karen_engine.services.factory import ServicesConfig
    print("✓ Successfully imported SmallLanguageModelService and LLMOrchestrator")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)

async def test_small_language_model_service():
    """Test SmallLanguageModelService basic functionality."""
    print("\n--- Testing SmallLanguageModelService ---")
    
    try:
        # Create a config
        config = SmallLanguageModelConfig(
            model_name="tinyllama-1.1b-chat",
            max_tokens=100,
            temperature=0.7,
            enable_fallback=True,
            cache_size=100,
            cache_ttl=1800
        )
        print("✓ Created SmallLanguageModelConfig")
        
        # Create the service
        service = SmallLanguageModelService(config=config)
        print("✓ Created SmallLanguageModelService")
        
        # Test health status
        health = service.get_health_status()
        print(f"✓ Got health status: {health.is_healthy}")
        
        # Test scaffolding with fallback
        result = await service.generate_scaffold("Test input for scaffolding")
        print(f"✓ Generated scaffold: {len(result.content)} characters")
        
        # Test outline generation with fallback
        outline = await service.generate_outline("Test input for outline generation")
        print(f"✓ Generated outline with {len(outline.outline)} points")
        
        # Test summarization with fallback
        summary = await service.summarize_context("Test input for summarization")
        print(f"✓ Generated summary: {len(summary.summary)} characters")
        
        return True
    except Exception as e:
        print(f"✗ SmallLanguageModelService test failed: {e}")
        return False

async def test_llm_orchestrator_integration():
    """Test LLM Orchestrator with SmallLanguageModelService integration."""
    print("\n--- Testing LLM Orchestrator Integration ---")
    
    try:
        # Create a config with Small Language Model enabled
        services_config = ServicesConfig(enable_small_language_model=True)
        print("✓ Created ServicesConfig with Small Language Model enabled")
        
        # Create the orchestrator
        orchestrator = LLMOrchestrator()
        print("✓ Created LLMOrchestrator")
        
        # Check if Small Language Model is registered as a provider
        # Get list of registered models
        models = orchestrator.registry.list_models()
        small_language_model_provider = None
        for model in models:
            if "small" in model.get("model_id", "").lower() or "tiny" in model.get("model_id", "").lower():
                small_language_model_provider = model
                break
        
        if small_language_model_provider:
            print(f"✓ Found Small Language Model provider: {small_language_model_provider.get('model_id', '')}")
        else:
            print("✗ Small Language Model provider not found in orchestrator")
            return False
        
        # Test generating text with the TinyLlama provider
        try:
            # Route a request to the small language model
            response = orchestrator.route(
                prompt="Test prompt",
                skill="generic"
            )
            # Handle both string and LLMRouteResult responses
            if isinstance(response, str):
                content = response
            elif hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response) if response else ""
            print(f"✓ Generated response using TinyLlama provider: {len(content) if content else 0} characters")
        except Exception as e:
            print(f"✗ Failed to generate response with TinyLlama provider: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ LLM Orchestrator integration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Starting SmallLanguageModelService integration tests...")
    
    success = True
    
    # Test SmallLanguageModelService
    success &= await test_small_language_model_service()
    
    # Test LLM Orchestrator integration
    success &= await test_llm_orchestrator_integration()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)