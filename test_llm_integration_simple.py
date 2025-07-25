#!/usr/bin/env python3
"""
Simple test for LLM integration functionality.
Tests the LLM utilities directly.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_llm_utils():
    """Test the LLM utilities directly."""
    print("Testing LLM Utils...")
    
    try:
        from ai_karen_engine.integrations.llm_utils import get_llm_manager
        
        # Get LLM manager
        llm_manager = get_llm_manager()
        
        # Test provider listing
        providers = llm_manager.list_available_providers()
        print(f"Available providers: {providers}")
        
        # Test health check
        health = llm_manager.health_check_all()
        print(f"Health check results: {health}")
        
        # Test text generation with fallback
        try:
            response = llm_manager.generate_text(
                prompt="Hello, how are you?",
                provider="ollama",
                model="llama3.2:latest",
                temperature=0.7,
                max_tokens=100
            )
            print(f"LLM Response: {response}")
        except Exception as e:
            print(f"LLM generation failed (expected if Ollama not running): {e}")
        
        print("✅ LLM Utils test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_utils())