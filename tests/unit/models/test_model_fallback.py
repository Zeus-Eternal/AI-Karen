#!/usr/bin/env python3
"""
Test script to verify model fallback functionality
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.ai_karen_engine.llm_orchestrator import get_orchestrator
from src.ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_model_fallback():
    """Test that the system properly falls back when models fail"""
    
    print("🧪 Testing Model Fallback System")
    print("=" * 50)
    
    # Test 1: Check LLM orchestrator model status
    print("\n1. Checking LLM Orchestrator Model Status:")
    try:
        orchestrator = get_orchestrator()
        model_status = orchestrator.get_model_status()
        print(f"   Registered models: {len(model_status)}")
        for model_id, status in model_status.items():
            print(f"   - {model_id}: {status}")
        
        # Reset any circuit breakers
        orchestrator.reset_circuit_breakers()
        print("   ✅ Circuit breakers reset")
        
    except Exception as e:
        print(f"   ❌ Error checking orchestrator: {e}")
    
    # Test 2: Test chat orchestrator with fallback
    print("\n2. Testing Chat Orchestrator Fallback:")
    try:
        chat_orchestrator = ChatOrchestrator()
        
        request = ChatRequest(
            message="Hello, can you help me test the system?",
            user_id="test_user",
            conversation_id="test_conversation",
            stream=False
        )
        
        print("   Sending test message...")
        response = await chat_orchestrator.process_message(request)
        
        if hasattr(response, 'response'):
            print(f"   ✅ Got response: {response.response[:100]}...")
            print(f"   Used fallback: {response.used_fallback}")
            print(f"   Processing time: {response.processing_time:.2f}s")
        else:
            print(f"   ❌ Unexpected response type: {type(response)}")
            
    except Exception as e:
        print(f"   ❌ Chat orchestrator error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test direct LLM orchestrator routing
    print("\n3. Testing Direct LLM Orchestrator Routing:")
    try:
        orchestrator = get_orchestrator()
        
        print("   Trying route() method...")
        response = orchestrator.route("Hello, this is a test message", skill="conversation")
        print(f"   ✅ Route response: {response[:100]}...")
        
    except Exception as e:
        print(f"   ⚠️  Route method failed (expected if no models loaded): {e}")
        
        # Try enhanced route
        try:
            print("   Trying enhanced_route() method...")
            response = await orchestrator.enhanced_route("Hello, this is a test message", skill="conversation")
            print(f"   ✅ Enhanced route response: {response[:100]}...")
        except Exception as e2:
            print(f"   ⚠️  Enhanced route also failed: {e2}")
    
    print("\n" + "=" * 50)
    print("🏁 Test Complete")

if __name__ == "__main__":
    asyncio.run(test_model_fallback())