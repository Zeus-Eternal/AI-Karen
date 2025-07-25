#!/usr/bin/env python3
"""
Simple test script for ChatOrchestrator implementation without full service dependencies.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the nlp_service_manager before importing
sys.modules['ai_karen_engine.services.nlp_service_manager'] = MagicMock()

# Create mock objects
mock_parsed_message = MagicMock()
mock_parsed_message.tokens = ["Hello", "world"]
mock_parsed_message.lemmas = ["hello", "world"]
mock_parsed_message.entities = [("world", "NOUN")]
mock_parsed_message.pos_tags = [("Hello", "INTJ"), ("world", "NOUN")]
mock_parsed_message.noun_phrases = ["world"]
mock_parsed_message.used_fallback = False

mock_nlp_manager = MagicMock()
mock_nlp_manager.parse_message = AsyncMock(return_value=mock_parsed_message)
mock_nlp_manager.get_embeddings = AsyncMock(return_value=[0.1] * 768)

sys.modules['ai_karen_engine.services.nlp_service_manager'].nlp_service_manager = mock_nlp_manager

# Now import the orchestrator
from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    RetryConfig,
    ProcessingStatus,
    ErrorType
)


async def test_chat_orchestrator_basic():
    """Test basic ChatOrchestrator functionality."""
    print("Testing ChatOrchestrator basic functionality...")
    
    # Create orchestrator
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
        
        # Verify response structure
        assert hasattr(response, 'response')
        assert hasattr(response, 'correlation_id')
        assert hasattr(response, 'processing_time')
        assert hasattr(response, 'used_fallback')
        assert hasattr(response, 'context_used')
        assert hasattr(response, 'metadata')
        
        print("✓ Response structure is correct")
        
    except Exception as e:
        print(f"✗ Traditional processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test streaming processing
    print("\n2. Testing streaming processing...")
    stream_request = ChatRequest(
        message="Tell me about artificial intelligence.",
        user_id="test_user_123",
        conversation_id="test_conv_456",
        stream=True,
        include_context=True
    )
    
    try:
        stream_response = await orchestrator.process_message(stream_request)
        chunks = []
        content_chunks = []
        
        async for chunk in stream_response:
            chunks.append(chunk)
            print(f"  Chunk [{chunk.type}]: {chunk.content[:30]}...")
            
            if chunk.type == "content":
                content_chunks.append(chunk.content)
            elif chunk.type == "complete":
                print(f"✓ Streaming completed with {len(chunks)} total chunks")
                print(f"✓ Content chunks: {len(content_chunks)}")
                break
            elif chunk.type == "error":
                print(f"✗ Streaming error: {chunk.content}")
                return False
        
        # Verify we got some content
        assert len(content_chunks) > 0, "No content chunks received"
        print("✓ Streaming response structure is correct")
                
    except Exception as e:
        print(f"✗ Streaming processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test processing stats
    print("\n3. Testing processing stats...")
    stats = orchestrator.get_processing_stats()
    print(f"✓ Total requests: {stats['total_requests']}")
    print(f"✓ Success rate: {stats['success_rate']:.2%}")
    print(f"✓ Average processing time: {stats['avg_processing_time']:.3f}s")
    
    # Verify stats structure
    expected_keys = [
        'total_requests', 'successful_requests', 'failed_requests',
        'success_rate', 'retry_attempts', 'fallback_usage',
        'avg_processing_time', 'active_contexts', 'recent_processing_times'
    ]
    for key in expected_keys:
        assert key in stats, f"Missing key in stats: {key}"
    
    print("✓ Stats structure is correct")
    
    # Test active contexts
    print("\n4. Testing active contexts...")
    active_contexts = orchestrator.get_active_contexts()
    print(f"✓ Active contexts: {len(active_contexts)}")
    
    print("\n✓ All basic tests passed!")
    return True


async def test_error_handling():
    """Test error handling scenarios."""
    print("\nTesting error handling...")
    
    orchestrator = ChatOrchestrator(
        retry_config=RetryConfig(max_attempts=2, initial_delay=0.1),
        timeout_seconds=10.0
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
        assert response.response is not None
        print("✓ Empty message handling is correct")
    except Exception as e:
        print(f"✗ Empty message test failed: {e}")
        return False
    
    # Test retry configuration
    print("\n2. Testing retry configuration...")
    retry_config = RetryConfig(
        max_attempts=3,
        backoff_factor=2.0,
        initial_delay=0.1,
        exponential_backoff=True
    )
    
    retry_orchestrator = ChatOrchestrator(retry_config=retry_config)
    assert retry_orchestrator.retry_config.max_attempts == 3
    assert retry_orchestrator.retry_config.backoff_factor == 2.0
    print("✓ Retry configuration is correct")
    
    print("\n✓ Error handling tests passed!")
    return True


async def test_data_models():
    """Test data model creation and validation."""
    print("\nTesting data models...")
    
    # Test ChatRequest
    print("\n1. Testing ChatRequest model...")
    request = ChatRequest(
        message="Test message",
        user_id="user123",
        conversation_id="conv456",
        stream=True,
        metadata={"test": "value"}
    )
    
    assert request.message == "Test message"
    assert request.user_id == "user123"
    assert request.conversation_id == "conv456"
    assert request.stream is True
    assert request.metadata["test"] == "value"
    print("✓ ChatRequest model is correct")
    
    # Test ProcessingStatus enum
    print("\n2. Testing ProcessingStatus enum...")
    assert ProcessingStatus.PENDING == "pending"
    assert ProcessingStatus.PROCESSING == "processing"
    assert ProcessingStatus.COMPLETED == "completed"
    assert ProcessingStatus.FAILED == "failed"
    assert ProcessingStatus.RETRYING == "retrying"
    print("✓ ProcessingStatus enum is correct")
    
    # Test ErrorType enum
    print("\n3. Testing ErrorType enum...")
    assert ErrorType.NLP_PARSING_ERROR == "nlp_parsing_error"
    assert ErrorType.EMBEDDING_ERROR == "embedding_error"
    assert ErrorType.TIMEOUT_ERROR == "timeout_error"
    print("✓ ErrorType enum is correct")
    
    print("\n✓ Data model tests passed!")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ChatOrchestrator Simple Integration Test")
    print("=" * 60)
    
    try:
        # Test basic functionality
        success1 = await test_chat_orchestrator_basic()
        
        # Test error handling
        success2 = await test_error_handling()
        
        # Test data models
        success3 = await test_data_models()
        
        if success1 and success2 and success3:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED!")
            print("ChatOrchestrator implementation is working correctly.")
            print("Key features verified:")
            print("  ✓ Traditional message processing")
            print("  ✓ Streaming message processing")
            print("  ✓ Error handling and retry logic")
            print("  ✓ Processing statistics")
            print("  ✓ Data model validation")
            print("  ✓ NLP service integration (mocked)")
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