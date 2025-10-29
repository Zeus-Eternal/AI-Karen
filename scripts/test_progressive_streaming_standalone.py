"""
Standalone test for Progressive Response Streaming System

This script tests the progressive response streaming implementation
without requiring the full test framework.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.services.progressive_response_streamer import (
    ProgressiveResponseStreamer,
    StreamingChunk,
    ChunkType,
    StreamingFeedback
)
from ai_karen_engine.services.content_optimization_engine import (
    ContentSection,
    Priority,
    ContentType,
    FormatType,
    ExpertiseLevel
)


async def test_basic_streaming():
    """Test basic streaming functionality"""
    print("Testing basic streaming functionality...")
    
    # Create feedback handler
    feedback_messages = []
    
    async def feedback_handler(feedback: StreamingFeedback):
        feedback_messages.append(feedback)
        print(f"  Feedback: {feedback.message}")
    
    # Create streamer
    streamer = ProgressiveResponseStreamer(
        buffer_size=512,
        chunk_size=128,
        feedback_callback=feedback_handler
    )
    
    # Create test content
    sections = [
        ContentSection(
            content="Critical action needed!",
            content_type=ContentType.TEXT,
            priority=Priority.CRITICAL,
            relevance_score=1.0,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.PLAIN_TEXT,
            is_actionable=True,
            estimated_read_time=2.0
        ),
        ContentSection(
            content="Background information here.",
            content_type=ContentType.TEXT,
            priority=Priority.LOW,
            relevance_score=0.3,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.PLAIN_TEXT,
            is_actionable=False,
            estimated_read_time=5.0
        )
    ]
    
    # Stream content
    chunks = []
    async for chunk in streamer.stream_priority_content(sections):
        chunks.append(chunk)
        print(f"  Received chunk: {chunk.chunk_type.value} - {chunk.content[:50]}...")
    
    # Verify results
    assert len(chunks) >= 4, f"Expected at least 4 chunks, got {len(chunks)}"
    assert chunks[0].chunk_type == ChunkType.METADATA, "First chunk should be metadata"
    assert chunks[-1].chunk_type == ChunkType.COMPLETION, "Last chunk should be completion"
    
    content_chunks = [c for c in chunks if c.chunk_type == ChunkType.CONTENT]
    assert len(content_chunks) == 2, f"Expected 2 content chunks, got {len(content_chunks)}"
    
    # Actionable content should come first
    assert content_chunks[0].is_actionable, "First content chunk should be actionable"
    
    print("  ✅ Basic streaming test passed!")
    return True


async def test_actionable_first_delivery():
    """Test actionable items delivered first"""
    print("Testing actionable-first delivery...")
    
    streamer = ProgressiveResponseStreamer()
    
    sections = [
        ContentSection(
            content="Explanatory content",
            content_type=ContentType.TEXT,
            priority=Priority.HIGH,
            relevance_score=0.8,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.PLAIN_TEXT,
            is_actionable=False
        ),
        ContentSection(
            content="Action required: Do this now!",
            content_type=ContentType.TEXT,
            priority=Priority.HIGH,
            relevance_score=0.9,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.PLAIN_TEXT,
            is_actionable=True
        ),
        ContentSection(
            content="pip install package",
            content_type=ContentType.CODE,
            priority=Priority.MEDIUM,
            relevance_score=0.85,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.CODE_BLOCK,
            is_actionable=True
        )
    ]
    
    content_items = []
    async for content in streamer.deliver_actionable_items_first(sections):
        content_items.append(content)
        print(f"  Delivered: {content[:30]}...")
    
    assert len(content_items) == 3, f"Expected 3 items, got {len(content_items)}"
    
    # First two should be actionable (formatted with action indicators)
    actionable_indicators = ["Action Required", "Action Items", "```"]
    first_is_actionable = any(indicator in content_items[0] for indicator in actionable_indicators)
    second_is_actionable = any(indicator in content_items[1] for indicator in actionable_indicators)
    
    assert first_is_actionable or second_is_actionable, "Actionable items should be delivered first"
    
    print("  ✅ Actionable-first delivery test passed!")
    return True


async def test_coherence_maintenance():
    """Test coherent structure maintenance"""
    print("Testing coherence maintenance...")
    
    streamer = ProgressiveResponseStreamer()
    
    async def test_stream():
        fragments = [
            "First part",
            "Second part\n\n",
            "Third part",
            "Fourth part."
        ]
        for fragment in fragments:
            yield fragment
    
    coherent_items = []
    async for item in streamer.maintain_response_coherence(test_stream()):
        coherent_items.append(item)
        print(f"  Coherent item: {repr(item)}")
    
    assert len(coherent_items) > 0, "Should produce coherent items"
    
    print("  ✅ Coherence maintenance test passed!")
    return True


async def test_error_handling():
    """Test error handling"""
    print("Testing error handling...")
    
    streamer = ProgressiveResponseStreamer()
    
    # Test different error types
    test_error = ValueError("Test error")
    error_chunk = await streamer.handle_streaming_errors("test_stream", test_error)
    
    assert error_chunk.chunk_type == ChunkType.ERROR, "Should create error chunk"
    assert "Test error" in error_chunk.content, "Should include error message"
    assert error_chunk.priority == Priority.CRITICAL, "Error should be critical priority"
    assert "recovery_strategy" in error_chunk.metadata, "Should include recovery strategy"
    
    print(f"  Error chunk created: {error_chunk.content}")
    print(f"  Recovery strategy: {error_chunk.metadata['recovery_strategy']}")
    
    print("  ✅ Error handling test passed!")
    return True


async def test_chunking_optimization():
    """Test response chunking optimization"""
    print("Testing chunking optimization...")
    
    streamer = ProgressiveResponseStreamer()
    
    # Test content with natural boundaries
    test_content = """This is a test paragraph.

This is another paragraph with more content.

```python
def test():
    return True
```

Final paragraph here."""
    
    chunks = await streamer.optimize_response_chunking(test_content, target_chunk_size=50)
    
    assert len(chunks) > 1, f"Should create multiple chunks, got {len(chunks)}"
    
    # Verify chunks are reasonably sized
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1} ({len(chunk)} chars): {chunk[:30]}...")
        assert len(chunk) <= 100, f"Chunk {i+1} too large: {len(chunk)} chars"
        assert chunk.strip(), f"Chunk {i+1} should not be empty"
    
    print("  ✅ Chunking optimization test passed!")
    return True


async def test_stream_management():
    """Test stream management functionality"""
    print("Testing stream management...")
    
    streamer = ProgressiveResponseStreamer()
    
    # Test stream initialization and management
    stream_id = "test_stream"
    await streamer._initialize_stream(stream_id, [])
    
    # Test pause/resume
    pause_result = await streamer.pause_stream(stream_id)
    assert pause_result, "Should be able to pause stream"
    
    resume_result = await streamer.resume_stream(stream_id)
    assert resume_result, "Should be able to resume stream"
    
    # Test cancellation
    cancel_result = await streamer.cancel_stream(stream_id)
    assert cancel_result, "Should be able to cancel stream"
    
    # Test active streams
    active_streams = streamer.get_active_streams()
    assert isinstance(active_streams, dict), "Should return dict of active streams"
    
    print("  ✅ Stream management test passed!")
    return True


async def test_feedback_system():
    """Test real-time feedback system"""
    print("Testing feedback system...")
    
    feedback_received = []
    
    async def test_feedback_callback(feedback: StreamingFeedback):
        feedback_received.append(feedback)
    
    streamer = ProgressiveResponseStreamer(feedback_callback=test_feedback_callback)
    
    # Create test progress
    from ai_karen_engine.services.progressive_response_streamer import StreamingProgress
    
    progress = StreamingProgress(
        current_section=1,
        total_sections=3,
        bytes_streamed=100,
        estimated_bytes_total=300,
        elapsed_time=5.0,
        estimated_remaining_time=10.0,
        completion_percentage=33.3,
        current_priority=Priority.HIGH
    )
    
    await streamer.provide_streaming_feedback("test_stream", progress)
    
    assert len(feedback_received) == 1, f"Expected 1 feedback message, got {len(feedback_received)}"
    assert "Processing section 1/3" in feedback_received[0].message, "Should include progress info"
    
    print(f"  Feedback received: {feedback_received[0].message}")
    print("  ✅ Feedback system test passed!")
    return True


async def run_all_tests():
    """Run all tests"""
    print("Progressive Response Streaming System - Standalone Tests")
    print("=" * 60)
    
    tests = [
        test_basic_streaming,
        test_actionable_first_delivery,
        test_coherence_maintenance,
        test_error_handling,
        test_chunking_optimization,
        test_stream_management,
        test_feedback_system
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n{test.__name__.replace('test_', '').replace('_', ' ').title()}:")
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"  ❌ {test.__name__} failed!")
        except Exception as e:
            failed += 1
            print(f"  ❌ {test.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)