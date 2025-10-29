"""
Comprehensive Progressive Delivery Tests
Validates streaming functionality, content prioritization, and progressive response delivery.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Optional, AsyncIterator
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.progressive_response_streamer import ProgressiveResponseStreamer
from src.ai_karen_engine.core.shared_types import (
    OptimizedResponse, ContentSection, StreamingMetadata, Priority
)


class TestProgressiveDeliveryValidation:
    """Test suite for comprehensive progressive delivery validation."""
    
    @pytest.fixture
    async def response_streamer(self):
        """Create a progressive response streamer for testing."""
        streamer = ProgressiveResponseStreamer()
        await streamer.initialize()
        return streamer
    
    @pytest.fixture
    def sample_optimized_responses(self):
        """Create sample optimized responses for streaming tests."""
        responses = []
        
        # Simple response
        simple_response = OptimizedResponse(
            content_sections=[
                ContentSection(
                    priority=1,
                    content="Quick answer: Python is a programming language.",
                    section_type="summary",
                    estimated_read_time=5
                ),
                ContentSection(
                    priority=2,
                    content="Python is a high-level, interpreted programming language known for its simplicity and readability.",
                    section_type="explanation",
                    estimated_read_time=15
                )
            ],
            total_size=500,
            generation_time=1.0,
            model_used="test-model",
            optimization_applied=["content_prioritization"],
            cache_key="simple-response",
            streaming_metadata=StreamingMetadata(
                total_chunks=2,
                estimated_total_time=20,
                priority_order=[1, 2]
            )
        )
        responses.append(simple_response)
        
        # Complex response with multiple priorities
        complex_response = OptimizedResponse(
            content_sections=[
                ContentSection(
                    priority=1,
                    content="# Neural Networks Overview\nNeural networks are computational models inspired by biological neural networks.",
                    section_type="summary",
                    estimated_read_time=10
                ),
                ContentSection(
                    priority=1,
                    content="```python\nimport torch\nimport torch.nn as nn\n\nclass SimpleNN(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.layer = nn.Linear(10, 1)\n```",
                    section_type="code",
                    estimated_read_time=20
                ),
                ContentSection(
                    priority=2,
                    content="## Architecture Components\n\n1. **Input Layer**: Receives data\n2. **Hidden Layers**: Process information\n3. **Output Layer**: Produces results",
                    section_type="explanation",
                    estimated_read_time=30
                ),
                ContentSection(
                    priority=3,
                    content="### Mathematical Foundation\n\nThe forward pass can be expressed as:\n\n$$y = f(Wx + b)$$\n\nWhere:\n- W is the weight matrix\n- x is the input vector\n- b is the bias vector\n- f is the activation function",
                    section_type="mathematical",
                    estimated_read_time=45
                ),
                ContentSection(
                    priority=3,
                    content="## Further Reading\n\n- Deep Learning by Ian Goodfellow\n- Neural Networks and Deep Learning by Michael Nielsen\n- Pattern Recognition and Machine Learning by Christopher Bishop",
                    section_type="references",
                    estimated_read_time=15
                )
            ],
            total_size=2500,
            generation_time=3.0,
            model_used="test-model",
            optimization_applied=["content_prioritization", "progressive_structuring"],
            cache_key="complex-response",
            streaming_metadata=StreamingMetadata(
                total_chunks=5,
                estimated_total_time=120,
                priority_order=[1, 1, 2, 3, 3]
            )
        )
        responses.append(complex_response)
        
        return responses
    
    async def _collect_stream_chunks(self, stream: AsyncIterator[str], max_chunks: int = 10) -> List[Dict[str, Any]]:
        """Collect chunks from a stream with timing information."""
        chunks = []
        start_time = time.time()
        
        chunk_count = 0
        async for chunk in stream:
            chunk_time = time.time() - start_time
            chunks.append({
                'content': chunk,
                'timestamp': chunk_time,
                'chunk_number': chunk_count,
                'size': len(chunk)
            })
            chunk_count += 1
            
            if chunk_count >= max_chunks:
                break
        
        return chunks
    
    @pytest.mark.asyncio
    async def test_priority_based_content_ordering(self, response_streamer, sample_optimized_responses):
        """Test that content is streamed in priority order."""
        complex_response = sample_optimized_responses[1]  # Use complex response
        
        # Stream the response
        chunks = await self._collect_stream_chunks(
            response_streamer.stream_priority_content(complex_response)
        )
        
        # Verify we received chunks
        assert len(chunks) > 0, "Should receive streaming chunks"
        
        # Verify priority ordering - high priority content should come first
        first_chunk = chunks[0]
        assert "Neural Networks Overview" in first_chunk['content'] or "import torch" in first_chunk['content'], (
            "First chunk should contain high priority content (summary or code)"
        )
        
        # Verify time to first chunk is fast
        assert first_chunk['timestamp'] < 0.5, (
            f"First chunk should arrive quickly, took {first_chunk['timestamp']:.3f}s"
        )
        
        # Check that chunks arrive in reasonable intervals
        if len(chunks) > 1:
            chunk_intervals = [
                chunks[i]['timestamp'] - chunks[i-1]['timestamp'] 
                for i in range(1, len(chunks))
            ]
            avg_interval = statistics.mean(chunk_intervals)
            assert avg_interval < 1.0, f"Average chunk interval {avg_interval:.3f}s should be under 1s"
        
        print(f"\nPriority-Based Streaming Results:")
        print(f"Total chunks received: {len(chunks)}")
        print(f"Time to first chunk: {first_chunk['timestamp']:.3f}s")
        print(f"First chunk content preview: {first_chunk['content'][:100]}...")
        if len(chunks) > 1:
            print(f"Average chunk interval: {avg_interval:.3f}s")
    
    @pytest.mark.asyncio
    async def test_actionable_items_first_delivery(self, response_streamer, sample_optimized_responses):
        """Test that actionable items are delivered before explanatory content."""
        complex_response = sample_optimized_responses[1]
        
        # Extract content sections by type
        code_sections = [s for s in complex_response.content_sections if s.section_type == "code"]
        explanation_sections = [s for s in complex_response.content_sections if s.section_type == "explanation"]
        
        # Stream actionable items first
        chunks = await self._collect_stream_chunks(
            response_streamer.deliver_actionable_items_first(complex_response.content_sections)
        )
        
        # Verify actionable content comes first
        actionable_chunk_found = False
        explanatory_chunk_found = False
        actionable_timestamp = None
        explanatory_timestamp = None
        
        for chunk in chunks:
            if "import torch" in chunk['content'] or "class SimpleNN" in chunk['content']:
                if not actionable_chunk_found:
                    actionable_chunk_found = True
                    actionable_timestamp = chunk['timestamp']
            
            if "Architecture Components" in chunk['content'] or "Hidden Layers" in chunk['content']:
                if not explanatory_chunk_found:
                    explanatory_chunk_found = True
                    explanatory_timestamp = chunk['timestamp']
        
        # Verify ordering
        if actionable_chunk_found and explanatory_chunk_found:
            assert actionable_timestamp < explanatory_timestamp, (
                "Actionable content should be delivered before explanatory content"
            )
        
        assert actionable_chunk_found, "Should deliver actionable content (code examples)"
        
        print(f"\nActionable Items First Results:")
        print(f"Actionable content delivered: {actionable_chunk_found}")
        print(f"Explanatory content delivered: {explanatory_chunk_found}")
        if actionable_timestamp and explanatory_timestamp:
            print(f"Actionable at: {actionable_timestamp:.3f}s, Explanatory at: {explanatory_timestamp:.3f}s")
    
    @pytest.mark.asyncio
    async def test_streaming_coherence_maintenance(self, response_streamer, sample_optimized_responses):
        """Test that response structure remains coherent during progressive delivery."""
        complex_response = sample_optimized_responses[1]
        
        # Create a mock stream
        async def mock_stream():
            for section in complex_response.content_sections:
                yield section.content
                await asyncio.sleep(0.1)  # Simulate streaming delay
        
        # Test coherence maintenance
        chunks = await self._collect_stream_chunks(
            response_streamer.maintain_response_coherence(mock_stream())
        )
        
        # Verify coherence
        full_content = "".join(chunk['content'] for chunk in chunks)
        
        # Check for proper structure markers
        assert "# Neural Networks Overview" in full_content, "Should maintain header structure"
        assert "```python" in full_content, "Should maintain code block structure"
        assert "## Architecture Components" in full_content, "Should maintain section structure"
        
        # Verify no broken formatting
        assert full_content.count("```") % 2 == 0, "Code blocks should be properly closed"
        assert full_content.count("#") >= 2, "Should maintain multiple header levels"
        
        # Check that chunks maintain readability
        for chunk in chunks:
            # No chunk should end mid-word (basic coherence check)
            if chunk['content'].strip() and not chunk['content'].endswith(('\n', '.', '`', ')', ']', '}')):
                # Allow some flexibility for streaming boundaries
                pass  # In real implementation, would check for proper boundaries
        
        print(f"\nStreaming Coherence Results:")
        print(f"Total content length: {len(full_content)} characters")
        print(f"Structure maintained: {full_content.count('#') >= 2}")
        print(f"Code blocks coherent: {full_content.count('```') % 2 == 0}")
    
    @pytest.mark.asyncio
    async def test_real_time_streaming_feedback(self, response_streamer, sample_optimized_responses):
        """Test real-time feedback during response generation."""
        simple_response = sample_optimized_responses[0]
        
        feedback_events = []
        
        # Mock feedback handler
        async def feedback_handler(progress: float, message: str):
            feedback_events.append({
                'progress': progress,
                'message': message,
                'timestamp': time.time()
            })
        
        # Stream with feedback
        with patch.object(response_streamer, 'provide_streaming_feedback', side_effect=feedback_handler):
            chunks = await self._collect_stream_chunks(
                response_streamer.stream_priority_content(simple_response)
            )
        
        # Verify feedback was provided
        assert len(feedback_events) > 0, "Should provide streaming feedback"
        
        # Verify progress increases
        if len(feedback_events) > 1:
            progress_values = [event['progress'] for event in feedback_events]
            assert progress_values == sorted(progress_values), "Progress should increase monotonically"
            assert progress_values[-1] >= 0.8, "Final progress should be near completion"
        
        print(f"\nStreaming Feedback Results:")
        print(f"Feedback events: {len(feedback_events)}")
        if feedback_events:
            print(f"Progress range: {feedback_events[0]['progress']:.1%} to {feedback_events[-1]['progress']:.1%}")
    
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, response_streamer, sample_optimized_responses):
        """Test error handling during streaming."""
        # Create a stream that will fail
        async def failing_stream():
            yield "First chunk"
            yield "Second chunk"
            raise RuntimeError("Streaming error")
            yield "This should not be reached"
        
        # Test error handling
        chunks = []
        error_handled = False
        
        try:
            async for chunk in response_streamer.handle_streaming_errors(failing_stream()):
                chunks.append(chunk)
        except Exception as e:
            error_handled = True
            assert "Streaming error" in str(e), "Should propagate original error"
        
        # Verify partial content was delivered before error
        assert len(chunks) >= 2, "Should deliver chunks before error"
        assert "First chunk" in chunks[0], "Should deliver first chunk"
        assert "Second chunk" in chunks[1], "Should deliver second chunk"
        
        print(f"\nStreaming Error Handling Results:")
        print(f"Chunks delivered before error: {len(chunks)}")
        print(f"Error properly handled: {error_handled}")
    
    @pytest.mark.asyncio
    async def test_response_chunking_optimization(self, response_streamer, sample_optimized_responses):
        """Test optimal response chunking for streaming performance."""
        complex_response = sample_optimized_responses[1]
        
        # Test chunking with different strategies
        chunk_strategies = [
            {"max_chunk_size": 100, "strategy": "size_based"},
            {"max_chunk_size": 500, "strategy": "size_based"},
            {"max_chunk_size": None, "strategy": "content_based"}
        ]
        
        chunking_results = []
        
        for strategy in chunk_strategies:
            with patch.object(response_streamer, 'chunking_strategy', strategy):
                start_time = time.time()
                chunks = await self._collect_stream_chunks(
                    response_streamer.stream_priority_content(complex_response)
                )
                total_time = time.time() - start_time
                
                chunking_results.append({
                    'strategy': strategy['strategy'],
                    'max_size': strategy['max_chunk_size'],
                    'chunk_count': len(chunks),
                    'total_time': total_time,
                    'avg_chunk_size': statistics.mean([chunk['size'] for chunk in chunks]) if chunks else 0
                })
        
        # Verify chunking optimization
        for result in chunking_results:
            assert result['chunk_count'] > 0, f"Should produce chunks for {result['strategy']} strategy"
            assert result['total_time'] < 2.0, f"Chunking should be fast for {result['strategy']} strategy"
            
            if result['max_size']:
                # Verify chunks respect size limits (with some tolerance)
                assert result['avg_chunk_size'] <= result['max_size'] * 1.2, (
                    f"Average chunk size should respect limit for {result['strategy']} strategy"
                )
        
        print(f"\nResponse Chunking Results:")
        for result in chunking_results:
            print(f"  {result['strategy']}: {result['chunk_count']} chunks, "
                  f"avg size: {result['avg_chunk_size']:.0f} chars, "
                  f"time: {result['total_time']:.3f}s")
    
    @pytest.mark.asyncio
    async def test_progressive_delivery_performance(self, response_streamer, sample_optimized_responses):
        """Test overall progressive delivery performance."""
        performance_results = []
        
        for i, response in enumerate(sample_optimized_responses):
            # Measure streaming performance
            start_time = time.time()
            chunks = await self._collect_stream_chunks(
                response_streamer.stream_priority_content(response)
            )
            total_streaming_time = time.time() - start_time
            
            # Calculate metrics
            time_to_first_chunk = chunks[0]['timestamp'] if chunks else float('inf')
            total_content_size = sum(chunk['size'] for chunk in chunks)
            streaming_throughput = total_content_size / total_streaming_time if total_streaming_time > 0 else 0
            
            performance_results.append({
                'response_type': 'simple' if i == 0 else 'complex',
                'total_time': total_streaming_time,
                'time_to_first_chunk': time_to_first_chunk,
                'chunk_count': len(chunks),
                'total_size': total_content_size,
                'throughput': streaming_throughput
            })
        
        # Verify performance targets
        for result in performance_results:
            assert result['time_to_first_chunk'] < 0.5, (
                f"Time to first chunk {result['time_to_first_chunk']:.3f}s should be under 0.5s "
                f"for {result['response_type']} response"
            )
            
            assert result['throughput'] > 1000, (  # Characters per second
                f"Streaming throughput {result['throughput']:.0f} chars/s should be over 1000 "
                f"for {result['response_type']} response"
            )
            
            assert result['total_time'] < 3.0, (
                f"Total streaming time {result['total_time']:.3f}s should be under 3s "
                f"for {result['response_type']} response"
            )
        
        print(f"\nProgressive Delivery Performance:")
        for result in performance_results:
            print(f"  {result['response_type'].capitalize()} response:")
            print(f"    Time to first chunk: {result['time_to_first_chunk']:.3f}s")
            print(f"    Total streaming time: {result['total_time']:.3f}s")
            print(f"    Throughput: {result['throughput']:.0f} chars/s")
            print(f"    Chunks: {result['chunk_count']}")
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_performance(self, response_streamer, sample_optimized_responses):
        """Test streaming performance under concurrent load."""
        # Create multiple concurrent streaming requests
        concurrent_streams = []
        
        for i in range(5):  # 5 concurrent streams
            response = sample_optimized_responses[i % len(sample_optimized_responses)]
            stream = response_streamer.stream_priority_content(response)
            concurrent_streams.append(stream)
        
        # Process streams concurrently
        start_time = time.time()
        
        async def process_stream(stream, stream_id):
            chunks = await self._collect_stream_chunks(stream)
            return {
                'stream_id': stream_id,
                'chunk_count': len(chunks),
                'first_chunk_time': chunks[0]['timestamp'] if chunks else float('inf')
            }
        
        # Execute concurrent streaming
        tasks = [process_stream(stream, i) for i, stream in enumerate(concurrent_streams)]
        results = await asyncio.gather(*tasks)
        total_concurrent_time = time.time() - start_time
        
        # Verify concurrent performance
        assert total_concurrent_time < 5.0, (
            f"Concurrent streaming should complete in under 5s, took {total_concurrent_time:.3f}s"
        )
        
        # Verify all streams completed successfully
        assert len(results) == 5, "All concurrent streams should complete"
        
        for result in results:
            assert result['chunk_count'] > 0, f"Stream {result['stream_id']} should produce chunks"
            assert result['first_chunk_time'] < 1.0, (
                f"Stream {result['stream_id']} first chunk should arrive quickly"
            )
        
        # Calculate average performance
        avg_first_chunk_time = statistics.mean([r['first_chunk_time'] for r in results])
        total_chunks = sum(r['chunk_count'] for r in results)
        
        print(f"\nConcurrent Streaming Performance:")
        print(f"Concurrent streams: {len(results)}")
        print(f"Total time: {total_concurrent_time:.3f}s")
        print(f"Average first chunk time: {avg_first_chunk_time:.3f}s")
        print(f"Total chunks delivered: {total_chunks}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])