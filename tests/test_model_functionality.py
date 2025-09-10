#!/usr/bin/env python3
"""
Test Model Functionality

This script tests if the models are working correctly after fixes.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_model_functionality():
    """Test model functionality."""
    print("🧪 Testing model functionality...")
    
    try:
        # Test 1: Check if models are loaded
        from ai_karen_engine.llm_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        models = orchestrator.registry.list_models()
        print(f"   Found {len(models)} registered models:")
        for model in models:
            print(f"     - {model['model_id']}: {model['status']}")
        
        # Test 2: Try generating a response
        if models:
            print("\n   Testing response generation...")
            try:
                response = orchestrator.route("Hello, how are you?", skill="conversation")
                print(f"   Response: {response[:100]}...")
                
                if len(response) > 10 and not response.startswith("I"):
                    print("   ✅ Model generating proper responses!")
                else:
                    print("   ⚠️ Model responses may still need improvement")
                    
            except Exception as e:
                print(f"   ❌ Response generation failed: {e}")
        else:
            print("   ❌ No models available for testing")
    
    except Exception as e:
        print(f"   ❌ Model testing failed: {e}")
    
    # Test 3: Check chat orchestrator
    try:
        from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest
        from ai_karen_engine.chat.memory_processor import MemoryProcessor
        
        print("\n   Testing chat orchestrator...")
        
        # Create minimal orchestrator for testing
        orchestrator = ChatOrchestrator(memory_processor=None)
        
        request = ChatRequest(
            message="What is Python?",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=False
        )
        
        response = await orchestrator.process_message(request)
        
        if response and hasattr(response, 'response') and response.response:
            print(f"   Chat response: {response.response[:100]}...")
            print("   ✅ Chat orchestrator working!")
        else:
            print("   ⚠️ Chat orchestrator returned empty response")
            
    except Exception as e:
        print(f"   ❌ Chat orchestrator test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_model_functionality())
