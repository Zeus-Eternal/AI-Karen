#!/usr/bin/env python3
"""
Test script for AI Orchestrator LLM integration.
Tests the updated _process_conversation_with_memory method.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
from ai_karen_engine.core.services.base import ServiceConfig
from ai_karen_engine.models.shared_types import FlowInput, FlowType


async def test_llm_integration():
    """Test the LLM integration in AI orchestrator."""
    print("Testing AI Orchestrator LLM Integration...")
    
    # Create AI orchestrator
    config = ServiceConfig(name="test_orchestrator")
    orchestrator = AIOrchestrator(config)
    
    try:
        # Initialize the orchestrator
        await orchestrator.initialize()
        await orchestrator.start()
        
        # Create test input
        test_input = FlowInput(
            prompt="Hello, how are you today?",
            user_id="test_user",
            session_id="test_session",
            conversation_history=[],
            user_settings={
                "personality_tone": "friendly",
                "llm_provider": "ollama",
                "llm_model": "llama3.2:latest",
                "temperature": 0.7
            }
        )
        
        # Test context building
        context = await orchestrator.context_manager.build_context(
            user_id=test_input.user_id,
            session_id=test_input.session_id,
            prompt=test_input.prompt,
            conversation_history=test_input.conversation_history,
            user_settings=test_input.user_settings
        )
        
        print(f"Built context: {context}")
        
        # Test the updated _process_conversation_with_memory method
        print("\nTesting LLM-powered conversation processing...")
        response = await orchestrator._process_conversation_with_memory(test_input, context)
        
        print(f"LLM Response: {response}")
        
        # Test fallback behavior
        print("\nTesting fallback behavior...")
        test_input_fallback = FlowInput(
            prompt="This is a test message",
            user_id="test_user",
            session_id="test_session",
            user_settings={
                "llm_provider": "nonexistent_provider"  # This should trigger fallback
            }
        )
        
        context_fallback = await orchestrator.context_manager.build_context(
            user_id=test_input_fallback.user_id,
            session_id=test_input_fallback.session_id,
            prompt=test_input_fallback.prompt,
            user_settings=test_input_fallback.user_settings
        )
        
        fallback_response = await orchestrator._process_conversation_with_memory(test_input_fallback, context_fallback)
        print(f"Fallback Response: {fallback_response}")
        
        # Test system prompt building
        print("\nTesting system prompt building...")
        system_prompt = await orchestrator._build_system_prompt(test_input, context)
        print(f"System Prompt: {system_prompt}")
        
        # Test user prompt with context
        print("\nTesting user prompt with context...")
        user_prompt = await orchestrator._build_user_prompt_with_context(test_input, context)
        print(f"User Prompt with Context: {user_prompt}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(test_llm_integration())