#!/usr/bin/env python3
"""
Test script for intelligent suggestion generation
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
from ai_karen_engine.core.services.base import ServiceConfig
from ai_karen_engine.models.shared_types import FlowInput, FlowType

async def test_intelligent_suggestions():
    """Test the intelligent suggestion generation functionality"""
    
    print("🧠 Testing Intelligent Suggestion Generation...")
    
    # Create orchestrator
    config = ServiceConfig(name="ai_orchestrator", enabled=True)
    orchestrator = AIOrchestrator(config)
    await orchestrator.initialize()
    
    # Test cases
    test_cases = [
        {
            "name": "Technical Conversation",
            "message": "I need help with programming",
            "history": [
                {"content": "Hello", "role": "user"},
                {"content": "Hi there!", "role": "assistant"},
                {"content": "Can you help me with code?", "role": "user"}
            ],
            "expected_type": "technical"
        },
        {
            "name": "Creative Conversation", 
            "message": "I want to write a story",
            "history": [
                {"content": "Hello", "role": "user"},
                {"content": "Hi there!", "role": "assistant"}
            ],
            "expected_type": "creative"
        },
        {
            "name": "Long Conversation",
            "message": "What about databases?",
            "history": [
                {"content": f"Question {i}", "role": "user"} 
                for i in range(12)  # Long conversation
            ],
            "expected_type": "pattern_based"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        
        # Create flow input
        flow_input = FlowInput(
            prompt=test_case["message"],
            conversation_history=test_case["history"],
            user_settings={"personalityTone": "friendly", "personalityVerbosity": "balanced"},
            user_id="test_user",
            session_id="test_session",
            context_from_memory=[]
        )
        
        # Process the conversation
        result = await orchestrator.conversation_processing_flow(flow_input)
        
        # Check if suggestion was generated
        if result.proactive_suggestion:
            print(f"✅ Generated suggestion: {result.proactive_suggestion}")
        else:
            print("❌ No suggestion generated")
        
        # Verify response was generated
        if result.response:
            print(f"✅ Response generated: {result.response[:100]}...")
        else:
            print("❌ No response generated")
    
    print("\n🎉 Intelligent suggestion testing completed!")

if __name__ == "__main__":
    asyncio.run(test_intelligent_suggestions())