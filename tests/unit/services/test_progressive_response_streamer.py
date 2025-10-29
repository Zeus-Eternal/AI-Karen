"""
Unit tests for Progressive Response Streamer

Tests the progressive response streaming system including:
- Priority-based content ordering
- Actionable items delivery
- Coherent structure maintenance
- Real-time feedback system
- Streaming error handling and recovery
- Response chunking and buffering optimization
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import List, AsyncIterator

from src.ai_karen_engine.services.progressive_response_streamer import (
    ProgressiveResponseStreamer,
    StreamingChunk,
    StreamingState,
    ChunkType,
    StreamingProgress,
    StreamingFeedback,
    StreamingMetadata
)
from src.ai_karen_engine.services.content_optimization_engine import (
    ContentSection,
    Priority,
    ContentType,
    FormatType,
    ExpertiseLevel
)


class TestProgressiveResponseStreamer:
    """Test cases for ProgressiveResponseStreamer"""
    
    @pytest.fixture
    def streamer(self):
        """Create a ProgressiveResponseStreamer instance for testing"""
        return ProgressiveResponseStreamer(
            buffer_size=1024,
            chunk_size=256,
            max_concurrent_streams=5
        )
    
    @pytest.fixture
    def sample_content_sections(self):
        """Create sample content sections for testing"""
        return [
            ContentSection(
                content="Execute this command: `pip install package`",
                content_type=ContentType.CODE,
                priority=Priority.CRITICAL,
                relevance_score=0.95,
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                format_type=FormatType.CODE_BLOCK,
                is_actionable=True,
                estimated_read_time=5.0
            ),
            ContentSection(
                content="This is background information about the package.",
                content_type=ContentType.TEXT,
                priority=Priority.MEDIUM,
                relevance_score=0.7,
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                format_type=FormatType.PLAIN_TEXT,
                is_actionable=False,
                estimated_read_time=10.0
            ),
            ContentSection(
                content="Important: Check your Python version first",
                content_type=ContentType.TEXT,
                priority=Priority.HIGH,
                relevance_score=0.9,
                expertise_level=ExpertiseLevel.BEGINNER,
                format_type=FormatType.PLAIN_TEXT,
                is_actionable=True,
                estimated_read_time=3.0
            ),
            ContentSection(
                content="Additional technical details and configuration options.",
                content_type=ContentType.TECHNICAL,
                priority=Priority.LOW,
                relevance_score=0.5,
                expertise_level=ExpertiseLevel.ADVANCED,
                format_type=FormatType.MARKDOWN,
                is_actionable=False,
                estimated_read_time=15.0
            )
        ]
    
    @pytest.mark.asyncio
    async def test_stream_priority_content_basic(self, streamer, sample_content_sections):
        """Test basic priority-based content streaming"""
        chunks = []
        async for chunk in streamer.stream_priority_content(sample_content_sections):
            chunks.append(chunk)
        
        # Should have metadata, content chunks, and completion
        assert len(chunks) >= 6  # metadata + 4 content + completion
        
        # First chunk should be metadata
        assert chunks[0].chunk_type == ChunkType.METADATA
        
        # Last chunk should be completion
        assert chunks[-1].chunk_type == ChunkType.COMPLETION
        
        # Content chunks should be in priority order
        content_chunks = [c for c in chunks if c.chunk_type == ChunkType.CONTENT]
        assert len(content_chunks) == 4
        
        # Actionable items should come first among same priority
        actionable_chunks = [c for c in content_chunks if c.is_actionable]
        assert len(actionable_chunks) == 2
    
    @pytest.mark.asyncio
    async def test_deliver_actionable_items_first(self, streamer, sample_content_sections):
        """Test that actionable items are delivered before explanatory content"""
        content_items = []
        async for content in streamer.deliver_actionable_items_first(sample_content_sections):
            content_items.append(content)
        
        assert len(content_items) == 4
        
        # First two items should be actionable (formatted differently)
        assert "Action Required" in content_items[0] or "Action Items" in content_items[0] or "```" in content_items[0]
        assert "Action Required" in content_items[1] or "Action Items" in content_items[1] or "```" in content_items[1]
    
    @pytest.mark.asyncio
    async def test_maintain_response_coherence(self, streamer):
        """Test coherent structure maintenance during streaming"""
        async def sample_stream():
            yield "First paragraph"
            yield "Second paragraph\n\n"
            yield "Third paragraph"
            yield "Fourth paragraph."
        
        coherent_items = []
        async for item in streamer.maintain_response_coherence(sample_stream()):
            coherent_items.append(item)
        
        assert len(coherent_items) > 0
        # Should maintain structure and add proper breaks
    
    @pytest.mark.asyncio
    async def test_streaming_feedback(self, streamer):
        """Test real-time feedback system"""
        feedback_received = []
        
        async def feedback_callback(feedback: StreamingFeedback):
            feedback_received.append(feedback)
        
        streamer.feedback_callback = feedback_callback
        
        progress = StreamingProgress(
            current_section=2,
            total_sections=5,
            bytes_streamed=1024,
            estimated_bytes_total=5120,
            elapsed_time=10.0,
            estimated_remaining_time=30.0,
            completion_percentage=40.0,
            current_priority=Priority.HIGH
        )
        
        await streamer.provide_streaming_feedback("test_stream", progress)
        
        assert len(feedback_received) == 1
        assert "Processing section 2/5" in feedback_received[0].message
        assert feedback_received[0].feedback_type == "info"
    
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, streamer):
        """Test streaming error handling and recovery"""
        test_error = ValueError("Test streaming error")
        
        error_chunk = await streamer.handle_streaming_errors("test_stream", test_error)
        
        assert error_chunk.chunk_type == ChunkType.ERROR
        assert "Test streaming error" in error_chunk.content
        assert error_chunk.priority == Priority.CRITICAL
        assert error_chunk.metadata["can_retry"] is True
        assert "recovery_strategy" in error_chunk.metadata
    
    @pytest.mark.asyncio
    async def test_response_chunking_optimization(self, streamer):
        """Test response chunking and buffering optimization"""
        long_content = "This is a long piece of content. " * 50  # Create long content
        
        chunks = await streamer.optimize_response_chunking(long_content, target_chunk_size=100)
        
        assert len(chunks) > 1  # Should be split into multiple chunks
        
        # Each chunk should be reasonably sized
        for chunk in chunks:
            assert len(chunk) <= 150  # Allow some flexibility for natural boundaries
        
        # Chunks should maintain readability
        for chunk in chunks:
            assert chunk.strip()  # No empty chunks
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_limits(self, streamer):
        """Test concurrent streaming limits"""
        # Create multiple concurrent streams
        tasks = []
        for i in range(10):  # More than max_concurrent_streams
            task = asyncio.create_task(
                self._consume_stream(streamer, [
                    ContentSection(
                        content=f"Content {i}",
                        content_type=ContentType.TEXT,
                        priority=Priority.MEDIUM,
                        relevance_score=0.5,
                        expertise_level=ExpertiseLevel.INTERMEDIATE,
                        format_type=FormatType.PLAIN_TEXT
                    )
                ])
            )
            tasks.append(task)
        
        # Should handle concurrent streams without error
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_stream_cancellation(self, streamer):
        """Test stream cancellation functionality"""
        # Start a stream
        stream_id = "test_cancel_stream"
        
        # Simulate active stream
        await streamer._initialize_stream(stream_id, [])
        
        # Cancel the stream
        result = await streamer.cancel_stream(stream_id)
        
        assert result is True
        assert streamer._active_streams[stream_id]["state"] == StreamingState.CANCELLED
    
    @pytest.mark.asyncio
    async def test_stream_pause_resume(self, streamer):
        """Test stream pause and resume functionality"""
        stream_id = "test_pause_resume"
        
        # Initialize stream
        await streamer._initialize_stream(stream_id, [])
        
        # Pause stream
        pause_result = await streamer.pause_stream(stream_id)
        assert pause_result is True
        assert streamer._active_streams[stream_id]["state"] == StreamingState.PAUSED
        
        # Resume stream
        resume_result = await streamer.resume_stream(stream_id)
        assert resume_result is True
        assert streamer._active_streams[stream_id]["state"] == StreamingState.STREAMING
    
    @pytest.mark.asyncio
    async def test_streaming_metadata_creation(self, streamer, sample_content_sections):
        """Test streaming metadata creation"""
        metadata = streamer._create_streaming_metadata(sample_content_sections)
        
        assert isinstance(metadata, StreamingMetadata)
        assert metadata.total_sections == 4
        assert metadata.estimated_duration > 0
        assert len(metadata.content_types) > 0
        assert metadata.streaming_strategy == "priority_based"
        assert metadata.buffer_size == streamer.buffer_size
        assert metadata.chunk_size == streamer.chunk_size
    
    @pytest.mark.asyncio
    async def test_natural_boundary_detection(self, streamer):
        """Test natural boundary detection for chunking"""
        # Test various boundary indicators
        test_cases = [
            ("Content with\n\nparagraph break", True),
            ("Code block end\n```\n", True),
            ("Section header\n## Title", True),
            ("Regular content", False),
            ("Content with---separator", True)
        ]
        
        for content, expected in test_cases:
            result = await streamer._is_natural_break_point(content)
            assert result == expected, f"Failed for content: {content}"
    
    @pytest.mark.asyncio
    async def test_error_recovery_strategies(self, streamer):
        """Test different error recovery strategies"""
        test_errors = [
            (asyncio.TimeoutError(), "retry_with_timeout"),
            (ConnectionError(), "reconnect_and_retry"),
            (MemoryError(), "reduce_chunk_size"),
            (ValueError(), "fallback_to_simple_delivery")
        ]
        
        for error, expected_strategy in test_errors:
            strategy = await streamer._determine_recovery_strategy(error)
            assert strategy == expected_strategy
    
    @pytest.mark.asyncio
    async def test_chunk_boundary_optimization(self, streamer):
        """Test chunk boundary optimization"""
        test_chunks = [
            "This is a complete sentence.",
            "This is incomplete",
            "Another complete sentence!",
            "Incomplete again"
        ]
        
        optimized = await streamer._optimize_chunk_boundaries(test_chunks)
        
        # Should have same number of chunks
        assert len(optimized) == len(test_chunks)
        
        # Complete sentences should remain unchanged
        assert optimized[0] == test_chunks[0]
        assert optimized[2] == test_chunks[2]
    
    def test_active_streams_management(self, streamer):
        """Test active streams management"""
        # Initially no active streams
        active = streamer.get_active_streams()
        assert len(active) == 0
        
        # Add some mock streams
        streamer._active_streams["stream1"] = {"state": StreamingState.STREAMING}
        streamer._active_streams["stream2"] = {"state": StreamingState.PAUSED}
        
        active = streamer.get_active_streams()
        assert len(active) == 2
        assert "stream1" in active
        assert "stream2" in active
    
    @pytest.mark.asyncio
    async def test_sequence_number_generation(self, streamer):
        """Test sequence number generation"""
        # Should start at 1 and increment
        seq1 = streamer._get_next_sequence()
        seq2 = streamer._get_next_sequence()
        seq3 = streamer._get_next_sequence()
        
        assert seq1 == 1
        assert seq2 == 2
        assert seq3 == 3
    
    @pytest.mark.asyncio
    async def test_content_formatting(self, streamer):
        """Test content formatting for different types"""
        code_section = ContentSection(
            content="print('hello')",
            content_type=ContentType.CODE,
            priority=Priority.HIGH,
            relevance_score=0.8,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.CODE_BLOCK,
            is_actionable=True
        )
        
        list_section = ContentSection(
            content="- Item 1\n- Item 2",
            content_type=ContentType.LIST,
            priority=Priority.HIGH,
            relevance_score=0.8,
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            format_type=FormatType.BULLET_POINTS,
            is_actionable=True
        )
        
        # Test actionable formatting
        code_formatted = await streamer._format_actionable_content(code_section)
        assert "```" in code_formatted
        
        list_formatted = await streamer._format_actionable_content(list_section)
        assert "Action Items" in list_formatted
    
    # Helper methods
    
    async def _consume_stream(self, streamer: ProgressiveResponseStreamer, 
                            sections: List[ContentSection]) -> List[StreamingChunk]:
        """Helper to consume a stream and return all chunks"""
        chunks = []
        async for chunk in streamer.stream_priority_content(sections):
            chunks.append(chunk)
        return chunks


class TestStreamingIntegration:
    """Integration tests for streaming system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_streaming_flow(self):
        """Test complete end-to-end streaming flow"""
        feedback_messages = []
        
        async def feedback_callback(feedback: StreamingFeedback):
            feedback_messages.append(feedback)
        
        streamer = ProgressiveResponseStreamer(
            buffer_size=512,
            chunk_size=128,
            feedback_callback=feedback_callback
        )
        
        # Create test content
        sections = [
            ContentSection(
                content="Critical action: Run this command now!",
                content_type=ContentType.TEXT,
                priority=Priority.CRITICAL,
                relevance_score=1.0,
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                format_type=FormatType.PLAIN_TEXT,
                is_actionable=True,
                estimated_read_time=2.0
            ),
            ContentSection(
                content="Background information for context.",
                content_type=ContentType.TEXT,
                priority=Priority.LOW,
                relevance_score=0.3,
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                format_type=FormatType.PLAIN_TEXT,
                is_actionable=False,
                estimated_read_time=8.0
            )
        ]
        
        # Stream content
        chunks = []
        async for chunk in streamer.stream_priority_content(sections):
            chunks.append(chunk)
        
        # Verify complete flow
        assert len(chunks) >= 4  # metadata + 2 content + completion
        assert chunks[0].chunk_type == ChunkType.METADATA
        assert chunks[-1].chunk_type == ChunkType.COMPLETION
        
        # Verify feedback was provided
        assert len(feedback_messages) > 0
        
        # Verify actionable content came first
        content_chunks = [c for c in chunks if c.chunk_type == ChunkType.CONTENT]
        assert content_chunks[0].is_actionable is True
    
    @pytest.mark.asyncio
    async def test_streaming_with_errors_and_recovery(self):
        """Test streaming with simulated errors and recovery"""
        streamer = ProgressiveResponseStreamer()
        
        # Simulate error during streaming
        with patch.object(streamer, '_stream_sections') as mock_stream:
            async def error_stream(*args):
                yield StreamingChunk(
                    id="test_chunk",
                    chunk_type=ChunkType.CONTENT,
                    content="Some content",
                    priority=Priority.MEDIUM,
                    sequence_number=1,
                    timestamp=datetime.now()
                )
                raise ConnectionError("Simulated connection error")
            
            mock_stream.return_value = error_stream()
            
            chunks = []
            async for chunk in streamer.stream_priority_content([]):
                chunks.append(chunk)
            
            # Should have received error chunk
            error_chunks = [c for c in chunks if c.chunk_type == ChunkType.ERROR]
            assert len(error_chunks) > 0
    
    @pytest.mark.asyncio
    async def test_large_content_streaming_performance(self):
        """Test streaming performance with large content"""
        streamer = ProgressiveResponseStreamer(
            buffer_size=2048,
            chunk_size=512
        )
        
        # Create large content sections
        large_sections = []
        for i in range(20):
            large_sections.append(
                ContentSection(
                    content="Large content section " * 100,  # Large content
                    content_type=ContentType.TEXT,
                    priority=Priority.MEDIUM,
                    relevance_score=0.5,
                    expertise_level=ExpertiseLevel.INTERMEDIATE,
                    format_type=FormatType.PLAIN_TEXT,
                    estimated_read_time=5.0
                )
            )
        
        start_time = asyncio.get_event_loop().time()
        
        chunks = []
        async for chunk in streamer.stream_priority_content(large_sections):
            chunks.append(chunk)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (less than 5 seconds for test)
        assert processing_time < 5.0
        
        # Should have processed all sections
        content_chunks = [c for c in chunks if c.chunk_type == ChunkType.CONTENT]
        assert len(content_chunks) == 20


if __name__ == "__main__":
    pytest.main([__file__])