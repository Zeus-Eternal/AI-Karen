"""
Progressive Response Streaming Example

This example demonstrates the progressive response streaming system with:
- Priority-based content ordering
- Actionable items delivered first
- Real-time feedback during streaming
- Error handling and recovery
- Response chunking optimization
"""

import asyncio
import logging
from datetime import datetime
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the streaming system
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.services.progressive_response_streamer import (
    ProgressiveResponseStreamer,
    StreamingFeedback,
    ChunkType
)
from ai_karen_engine.services.content_optimization_engine import (
    ContentSection,
    Priority,
    ContentType,
    FormatType,
    ExpertiseLevel
)


async def feedback_handler(feedback: StreamingFeedback):
    """Handle real-time feedback during streaming"""
    timestamp = feedback.timestamp.strftime("%H:%M:%S")
    print(f"[{timestamp}] {feedback.feedback_type.upper()}: {feedback.message}")
    
    if feedback.requires_acknowledgment:
        print(f"  → Action required: {feedback.action_required}")


async def demonstrate_basic_streaming():
    """Demonstrate basic progressive streaming with priority ordering"""
    print("\n" + "="*60)
    print("BASIC PROGRESSIVE STREAMING DEMONSTRATION")
    print("="*60)
    
    # Create streamer with feedback
    streamer = ProgressiveResponseStreamer(
        buffer_size=1024,
        chunk_size=256,
        feedback_callback=feedback_handler
    )
    
    # Create sample content sections with different priorities
    content_sections = [
        ContentSection(
            content="🚨 URGENT: Run `pip install --upgrade security-patch` immediately!",
            content_type=ContentType.CODE,
            priority=Priority.CRITICAL,
            relevance_score=1.0,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.CODE_BLOCK,
            is_actionable=True,
            estimated_read_time=3.0
        ),
        ContentSection(
            content="⚠️ Important: Backup your data before proceeding with the upgrade.",
            content_type=ContentType.TEXT,
            priority=Priority.HIGH,
            relevance_score=0.9,
            expertise_level=ExpertiseLevel.BEGINNER,
            format_type=FormatType.PLAIN_TEXT,
            is_actionable=True,
            estimated_read_time=5.0
        ),
        ContentSection(
            content="""This security patch addresses several vulnerabilities:
- CVE-2024-0001: Buffer overflow in authentication module
- CVE-2024-0002: SQL injection in user management
- CVE-2024-0003: Cross-site scripting in web interface

The patch has been tested extensively and is recommended for all users.""",
            content_type=ContentType.LIST,
            priority=Priority.MEDIUM,
            relevance_score=0.7,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.BULLET_POINTS,
            is_actionable=False,
            estimated_read_time=15.0
        ),
        ContentSection(
            content="""Technical Details:
The security patch modifies the following components:
- Authentication module (auth.py)
- Database layer (db_manager.py)  
- Web interface templates (*.html)

For advanced users, you can review the changes in the changelog:
https://github.com/example/project/blob/main/CHANGELOG.md

Configuration changes may be required for custom installations.""",
            content_type=ContentType.TECHNICAL,
            priority=Priority.LOW,
            relevance_score=0.4,
            expertise_level=ExpertiseLevel.ADVANCED,
            format_type=FormatType.MARKDOWN,
            is_actionable=False,
            estimated_read_time=20.0
        )
    ]
    
    print("\nStreaming content with priority-based ordering...")
    print("-" * 50)
    
    chunk_count = 0
    async for chunk in streamer.stream_priority_content(content_sections):
        chunk_count += 1
        
        if chunk.chunk_type == ChunkType.METADATA:
            print(f"\n📊 METADATA (Chunk {chunk_count}):")
            print(f"  Stream ID: {chunk.metadata.get('stream_id', 'N/A')}")
            print(f"  Sequence: {chunk.sequence_number}")
            
        elif chunk.chunk_type == ChunkType.CONTENT:
            priority_emoji = {
                Priority.CRITICAL: "🔴",
                Priority.HIGH: "🟠", 
                Priority.MEDIUM: "🟡",
                Priority.LOW: "🟢"
            }.get(chunk.priority, "⚪")
            
            actionable_marker = "⚡ ACTIONABLE" if chunk.is_actionable else "📖 INFO"
            
            print(f"\n{priority_emoji} CONTENT (Chunk {chunk_count}) - {actionable_marker}:")
            print(f"  Priority: {chunk.priority.name}")
            print(f"  Type: {chunk.metadata.get('content_type', 'unknown')}")
            print(f"  Content: {chunk.content[:100]}{'...' if len(chunk.content) > 100 else ''}")
            
        elif chunk.chunk_type == ChunkType.COMPLETION:
            print(f"\n✅ COMPLETION (Chunk {chunk_count}):")
            print(f"  Status: {chunk.metadata.get('status', 'unknown')}")
            print(f"  Message: {chunk.content}")
    
    print(f"\nStreaming completed! Total chunks: {chunk_count}")


async def demonstrate_actionable_first_delivery():
    """Demonstrate actionable items delivered first"""
    print("\n" + "="*60)
    print("ACTIONABLE-FIRST DELIVERY DEMONSTRATION")
    print("="*60)
    
    streamer = ProgressiveResponseStreamer()
    
    # Mix of actionable and explanatory content
    mixed_content = [
        ContentSection(
            content="Here's some background information about the process...",
            content_type=ContentType.TEXT,
            priority=Priority.HIGH,
            relevance_score=0.8,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.PLAIN_TEXT,
            is_actionable=False
        ),
        ContentSection(
            content="Step 1: Open your terminal and navigate to the project directory",
            content_type=ContentType.TEXT,
            priority=Priority.HIGH,
            relevance_score=0.9,
            expertise_level=ExpertiseLevel.BEGINNER,
            format_type=FormatType.PLAIN_TEXT,
            is_actionable=True
        ),
        ContentSection(
            content="The theoretical foundation of this approach is based on...",
            content_type=ContentType.TECHNICAL,
            priority=Priority.MEDIUM,
            relevance_score=0.6,
            expertise_level=ExpertiseLevel.ADVANCED,
            format_type=FormatType.MARKDOWN,
            is_actionable=False
        ),
        ContentSection(
            content="Step 2: Run the following command:\n```bash\nnpm install\nnpm run build\n```",
            content_type=ContentType.CODE,
            priority=Priority.HIGH,
            relevance_score=0.95,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.CODE_BLOCK,
            is_actionable=True
        )
    ]
    
    print("\nDelivering actionable items first...")
    print("-" * 40)
    
    item_count = 0
    async for content in streamer.deliver_actionable_items_first(mixed_content):
        item_count += 1
        
        # Determine if this is actionable based on formatting
        is_actionable = ("Action Required" in content or 
                        "Action Items" in content or 
                        "```" in content)
        
        marker = "⚡ ACTIONABLE" if is_actionable else "📖 EXPLANATORY"
        
        print(f"\n{marker} (Item {item_count}):")
        print(content.strip())
    
    print(f"\nDelivery completed! Total items: {item_count}")


async def demonstrate_coherence_maintenance():
    """Demonstrate coherent structure maintenance"""
    print("\n" + "="*60)
    print("COHERENCE MAINTENANCE DEMONSTRATION")
    print("="*60)
    
    streamer = ProgressiveResponseStreamer()
    
    # Simulate fragmented content stream
    async def fragmented_stream():
        fragments = [
            "This is the first part",
            "of a longer explanation",
            "that needs to be\n\n",
            "properly structured",
            "with coherent transitions.",
            "## New Section\n",
            "Here's a new section",
            "with additional details"
        ]
        
        for fragment in fragments:
            yield fragment
            await asyncio.sleep(0.1)  # Simulate streaming delay
    
    print("\nMaintaining coherence in fragmented stream...")
    print("-" * 45)
    
    item_count = 0
    async for coherent_item in streamer.maintain_response_coherence(fragmented_stream()):
        item_count += 1
        print(f"\nCoherent Item {item_count}:")
        print(repr(coherent_item))  # Show with escape characters
    
    print(f"\nCoherence processing completed! Total items: {item_count}")


async def demonstrate_error_handling():
    """Demonstrate streaming error handling and recovery"""
    print("\n" + "="*60)
    print("ERROR HANDLING DEMONSTRATION")
    print("="*60)
    
    error_feedback = []
    
    async def error_feedback_handler(feedback: StreamingFeedback):
        error_feedback.append(feedback)
        await feedback_handler(feedback)
    
    streamer = ProgressiveResponseStreamer(feedback_callback=error_feedback_handler)
    
    # Test different types of errors
    test_errors = [
        asyncio.TimeoutError("Connection timeout"),
        ConnectionError("Network connection lost"),
        MemoryError("Insufficient memory"),
        ValueError("Invalid data format")
    ]
    
    print("\nTesting error handling and recovery strategies...")
    print("-" * 50)
    
    for i, error in enumerate(test_errors, 1):
        print(f"\n{i}. Testing {type(error).__name__}:")
        
        error_chunk = await streamer.handle_streaming_errors(f"test_stream_{i}", error)
        
        print(f"   Error Chunk ID: {error_chunk.id}")
        print(f"   Recovery Strategy: {error_chunk.metadata.get('recovery_strategy')}")
        print(f"   Can Retry: {error_chunk.metadata.get('can_retry')}")
        print(f"   Content: {error_chunk.content}")
    
    print(f"\nError handling completed! Feedback messages: {len(error_feedback)}")


async def demonstrate_chunking_optimization():
    """Demonstrate response chunking optimization"""
    print("\n" + "="*60)
    print("CHUNKING OPTIMIZATION DEMONSTRATION")
    print("="*60)
    
    streamer = ProgressiveResponseStreamer()
    
    # Create content with various structures
    test_content = """
This is a long piece of content that needs to be chunked intelligently. It contains multiple sentences and paragraphs that should be split at natural boundaries.

Here's a code example that should stay together:
```python
def example_function():
    print("This code block should not be split")
    return "success"
```

This is another paragraph with technical information. It discusses various aspects of the system including performance, reliability, and maintainability.

## Section Header

This section contains additional details about the implementation. The chunking algorithm should respect section boundaries and maintain readability.

- List item one
- List item two  
- List item three

Final paragraph with concluding thoughts and recommendations for next steps.
"""
    
    print("\nOptimizing content chunking...")
    print("-" * 35)
    
    # Test different chunk sizes
    chunk_sizes = [100, 200, 500]
    
    for size in chunk_sizes:
        print(f"\nChunk size: {size} characters")
        print("-" * 25)
        
        chunks = await streamer.optimize_response_chunking(test_content, target_chunk_size=size)
        
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i} ({len(chunk)} chars): {chunk[:50]}{'...' if len(chunk) > 50 else ''}")
        
        print(f"  Total chunks: {len(chunks)}")


async def demonstrate_concurrent_streaming():
    """Demonstrate concurrent streaming capabilities"""
    print("\n" + "="*60)
    print("CONCURRENT STREAMING DEMONSTRATION")
    print("="*60)
    
    streamer = ProgressiveResponseStreamer(max_concurrent_streams=3)
    
    # Create multiple content sets for concurrent streaming
    content_sets = []
    for i in range(5):
        content_sets.append([
            ContentSection(
                content=f"Content set {i+1}: This is important information that needs to be streamed.",
                content_type=ContentType.TEXT,
                priority=Priority.MEDIUM,
                relevance_score=0.7,
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                format_type=FormatType.PLAIN_TEXT,
                estimated_read_time=2.0
            )
        ])
    
    print(f"\nStarting {len(content_sets)} concurrent streams (max: {streamer.max_concurrent_streams})...")
    print("-" * 60)
    
    async def stream_content(stream_id: int, content: List[ContentSection]):
        """Stream content and collect results"""
        chunks = []
        try:
            async for chunk in streamer.stream_priority_content(content, f"stream_{stream_id}"):
                chunks.append(chunk)
            return f"Stream {stream_id}: {len(chunks)} chunks"
        except Exception as e:
            return f"Stream {stream_id}: Error - {str(e)}"
    
    # Start concurrent streams
    tasks = [
        stream_content(i+1, content_sets[i]) 
        for i in range(len(content_sets))
    ]
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = asyncio.get_event_loop().time()
    
    print("\nConcurrent streaming results:")
    for result in results:
        print(f"  {result}")
    
    print(f"\nTotal processing time: {end_time - start_time:.2f} seconds")
    print(f"Active streams: {len(streamer.get_active_streams())}")


async def main():
    """Run all demonstrations"""
    print("Progressive Response Streaming System Demonstration")
    print("=" * 60)
    
    try:
        await demonstrate_basic_streaming()
        await demonstrate_actionable_first_delivery()
        await demonstrate_coherence_maintenance()
        await demonstrate_error_handling()
        await demonstrate_chunking_optimization()
        await demonstrate_concurrent_streaming()
        
        print("\n" + "="*60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())