#!/usr/bin/env python3
"""
Test script for ChatOrchestrator implementation.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    RetryConfig
)


async def test_chat_orchestrator():
    """Test the ChatOrchestrator implementation."""
    print("Testing ChatOrchestrator...")
    
    # Create orchestrator with custom retry config
    retry_config = RetryConfig(max_attempts=2, initial_delay=0.1)
    orchestrator = ChatOrchestrator(
        retry_config=retry_config,
        timeout_seconds=10.0
    )
    
    # Test traditional processing
    print("\n1. Testing traditional processing...")
    request = ChatRequest(
        message="Hello, how are you today?",
        user_id="test_user_123",
        conversation_id="test_conv_456",
        stream=False,
        include_context=True
    )
    
    try:
        response = await orchestrator.process_message(request)
        print(f"✓ Response received: {response.response[:100]}...")
        print(f"✓ Processing time: {response.processing_time:.3f}s")
        print(f"✓ Correlation ID: {response.correlation_id}")
        print(f"✓ Used fallback: {response.used_fallback}")
        print(f"✓ Context used: {response.context_used}")
    except Exception as e:
        print(f"✗ Traditional processing failed: {e}")
        return False
    
    # Test streaming processing
    print("\n2. Testing streaming processing...")
    stream_request = ChatRequest(
        message="Tell me about artificial intelligence and machine learning.",
        user_id="test_user_123",
        conversation_id="test_conv_456",
        stream=True,
        include_context=True
    )
    
    try:
        stream_response = await orchestrator.process_message(stream_request)
        chunks = []
        
        async for chunk in stream_response:
            chunks.append(chunk)
            print(f"  Chunk [{chunk.type}]: {chunk.content[:50]}...")
            
            if chunk.type == "complete":
                print(f"✓ Streaming completed with {len(chunks)} chunks")
                break
            elif chunk.type == "error":
                print(f"✗ Streaming error: {chunk.content}")
                return False
                
    except Exception as e:
        print(f"✗ Streaming processing failed: {e}")
        return False
    
    # Test processing stats
    print("\n3. Testing processing stats...")
    stats = orchestrator.get_processing_stats()
    print(f"✓ Total requests: {stats['total_requests']}")
    print(f"✓ Success rate: {stats['success_rate']:.2%}")
    print(f"✓ Average processing time: {stats['avg_processing_time']:.3f}s")
    
    # Test with entity-rich message
    print("\n4. Testing entity extraction...")
    entity_request = ChatRequest(
        message="I work at Google in San Francisco and my name is John Smith. I love Python programming.",
        user_id="test_user_123",
        conversation_id="test_conv_456",
        stream=False,
        include_context=True
    )
    
    try:
        entity_response = await orchestrator.process_message(entity_request)
        print(f"✓ Entity response: {entity_response.response[:100]}...")
        print(f"✓ Entities detected: {entity_response.metadata.get('parsed_entities', 0)}")
    except Exception as e:
        print(f"✗ Entity processing failed: {e}")
        return False
    
    print("\n✓ All tests passed!")
    return True


async def test_error_handling():
    """Test error handling and retry logic."""
    print("\nTesting error handling...")
    
    orchestrator = ChatOrchestrator(
        retry_config=RetryConfig(max_attempts=2, initial_delay=0.1),
        timeout_seconds=1.0  # Very short timeout to test timeout handling
    )
    
    # Test with empty message
    print("\n1. Testing empty message handling...")
    empty_request = ChatRequest(
        message="",
        user_id="test_user",
        conversation_id="test_conv",
        stream=False
    )
    
    try:
        response = await orchestrator.process_message(empty_request)
        print(f"✓ Empty message handled: {response.response[:50]}...")
    except Exception as e:
        print(f"✗ Empty message test failed: {e}")
        return False
    
    print("\n✓ Error handling tests passed!")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ChatOrchestrator Integration Test")
    print("=" * 60)
    
    try:
        # Test basic functionality
        success1 = await test_chat_orchestrator()
        
        # Test error handling
        success2 = await test_error_handling()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED!")
            print("ChatOrchestrator is working correctly with NLP integration.")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ SOME TESTS FAILED!")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)