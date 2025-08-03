"""
Tests for Stream Processor functionality.

This module tests the streaming response processor including
chunked delivery, Server-Sent Events, stream interruption handling,
and performance monitoring.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, AsyncGenerator

# Import the modules to test
from src.ai_karen_engine.chat.stream_processor import (
    StreamProcessor,
    StreamChunk,
    ChunkType,
    StreamType,
    StreamStatus,
    StreamSession,
    StreamBuffer,
    StreamMetrics
)
from src.ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest, ChatResponse


class MockChatOrchestrator:
    """Mock ChatOrchestrator for testing."""
    
    def __init__(self):
        self.process_calls = []
        self.streaming_response = "This is a test response for streaming."
        self.traditional_response = "Traditional response."
    
    async def process_message(self, request: ChatRequest):
        """Mock process_message method."""
        self.process_calls.append(request)
        
        if request.stream:
            # Return async generator for streaming
            async def stream_generator():
                words = self.streaming_response.split()
                for word in words:
                    yield type('ChatStreamChunk', (), {
                        'type': 'content',
                        'content': word + ' ',
                        'metadata': {},
                        'timestamp': datetime.utcnow()
                    })()
                
                yield type('ChatStreamChunk', (), {
                    'type': 'complete',
                    'content': '',
                    'metadata': {'processing_time': 0.5},
                    'timestamp': datetime.utcnow()
                })()
            
            return stream_generator()
        else:
            # Return traditional response
            return ChatResponse(
                response=self.traditional_response,
                correlation_id=request.metadata.get('correlation_id', ''),
                processing_time=0.5,
                used_fallback=False,
                context_used=True,
                metadata={}
            )


class MockRequest:
    """Mock HTTP request for testing."""
    
    def __init__(self, client_host="127.0.0.1", user_agent="test-agent"):
        self.client = type('Client', (), {'host': client_host})()
        self.headers = {"user-agent": user_agent}


@pytest.fixture
def mock_chat_orchestrator():
    """Create mock chat orchestrator."""
    return MockChatOrchestrator()


@pytest.fixture
def stream_processor(mock_chat_orchestrator):
    """Create stream processor for testing."""
    return StreamProcessor(
        chat_orchestrator=mock_chat_orchestrator,
        default_chunk_size=10,  # Small chunks for testing
        default_chunk_delay=0.01,  # Fast for testing
        heartbeat_interval=1.0,  # Short interval for testing
        stream_timeout=5.0  # Short timeout for testing
    )


@pytest.fixture
def mock_request():
    """Create mock HTTP request."""
    return MockRequest()


class TestStreamChunk:
    """Test StreamChunk functionality."""
    
    def test_stream_chunk_creation(self):
        """Test creating stream chunk."""
        chunk = StreamChunk(
            type=ChunkType.CONTENT,
            content="Hello world",
            metadata={"test": "value"},
            sequence_number=1
        )
        
        assert chunk.type == ChunkType.CONTENT
        assert chunk.content == "Hello world"
        assert chunk.metadata["test"] == "value"
        assert chunk.sequence_number == 1
        assert chunk.chunk_id is not None
        assert chunk.timestamp is not None
    
    def test_stream_chunk_serialization(self):
        """Test stream chunk serialization."""
        chunk = StreamChunk(
            type=ChunkType.METADATA,
            content="",
            metadata={"session_id": "test123"},
            sequence_number=0
        )
        
        # Test that chunk can be serialized
        chunk_dict = {
            "type": chunk.type.value,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "chunk_id": chunk.chunk_id,
            "sequence_number": chunk.sequence_number,
            "timestamp": chunk.timestamp.isoformat()
        }
        
        json_str = json.dumps(chunk_dict)
        assert json_str is not None
        
        # Test deserialization
        parsed = json.loads(json_str)
        assert parsed["type"] == ChunkType.METADATA.value
        assert parsed["metadata"]["session_id"] == "test123"


class TestStreamBuffer:
    """Test StreamBuffer functionality."""
    
    @pytest.fixture
    def stream_buffer(self):
        """Create stream buffer for testing."""
        return StreamBuffer(max_size=100)  # Small buffer for testing
    
    @pytest.mark.asyncio
    async def test_add_chunk(self, stream_buffer):
        """Test adding chunks to buffer."""
        chunk1 = StreamChunk(type=ChunkType.CONTENT, content="Hello", sequence_number=1)
        chunk2 = StreamChunk(type=ChunkType.CONTENT, content=" world", sequence_number=2)
        
        await stream_buffer.add_chunk(chunk1)
        await stream_buffer.add_chunk(chunk2)
        
        assert len(stream_buffer.chunks) == 2
        assert stream_buffer.total_size == len("Hello") + len(" world")
    
    @pytest.mark.asyncio
    async def test_buffer_size_limit(self, stream_buffer):
        """Test buffer size limit."""
        # Add chunks that exceed buffer size
        for i in range(20):
            chunk = StreamChunk(
                type=ChunkType.CONTENT,
                content="x" * 10,  # 10 characters each
                sequence_number=i
            )
            await stream_buffer.add_chunk(chunk)
        
        # Buffer should not exceed max_size
        assert stream_buffer.total_size <= stream_buffer.max_size
    
    @pytest.mark.asyncio
    async def test_get_chunks_from(self, stream_buffer):
        """Test getting chunks from specific sequence number."""
        chunks = []
        for i in range(5):
            chunk = StreamChunk(
                type=ChunkType.CONTENT,
                content=f"chunk{i}",
                sequence_number=i
            )
            chunks.append(chunk)
            await stream_buffer.add_chunk(chunk)
        
        # Get chunks from sequence 2
        result_chunks = await stream_buffer.get_chunks_from(2)
        assert len(result_chunks) == 3  # chunks 2, 3, 4
        assert result_chunks[0].sequence_number == 2
    
    @pytest.mark.asyncio
    async def test_get_latest_chunks(self, stream_buffer):
        """Test getting latest chunks."""
        chunks = []
        for i in range(5):
            chunk = StreamChunk(
                type=ChunkType.CONTENT,
                content=f"chunk{i}",
                sequence_number=i
            )
            chunks.append(chunk)
            await stream_buffer.add_chunk(chunk)
        
        # Get latest 3 chunks
        latest_chunks = await stream_buffer.get_latest_chunks(3)
        assert len(latest_chunks) == 3
        assert latest_chunks[-1].sequence_number == 4  # Last chunk
    
    @pytest.mark.asyncio
    async def test_clear_buffer(self, stream_buffer):
        """Test clearing buffer."""
        chunk = StreamChunk(type=ChunkType.CONTENT, content="test", sequence_number=1)
        await stream_buffer.add_chunk(chunk)
        
        await stream_buffer.clear()
        
        assert len(stream_buffer.chunks) == 0
        assert stream_buffer.total_size == 0


class TestStreamMetrics:
    """Test StreamMetrics functionality."""
    
    @pytest.fixture
    def stream_metrics(self):
        """Create stream metrics for testing."""
        return StreamMetrics()
    
    def test_record_stream_start(self, stream_metrics):
        """Test recording stream start."""
        stream_metrics.record_stream_start()
        assert stream_metrics.total_streams == 1
    
    def test_record_stream_success(self, stream_metrics):
        """Test recording stream success."""
        session = StreamSession(
            session_id="test123",
            stream_type=StreamType.WEBSOCKET,
            chunks_sent=10,
            bytes_sent=1000,
            processing_time=1.5
        )
        session.started_at = datetime.utcnow()
        session.completed_at = datetime.utcnow()
        
        stream_metrics.record_stream_success(session)
        
        assert stream_metrics.successful_streams == 1
        assert stream_metrics.total_chunks_sent == 10
        assert stream_metrics.total_bytes_sent == 1000
        assert stream_metrics.total_processing_time == 1.5
    
    def test_record_stream_failure(self, stream_metrics):
        """Test recording stream failure."""
        session = StreamSession(session_id="test123", stream_type=StreamType.WEBSOCKET)
        
        stream_metrics.record_stream_failure(session)
        
        assert stream_metrics.failed_streams == 1
    
    def test_get_metrics(self, stream_metrics):
        """Test getting metrics."""
        # Record some activity
        stream_metrics.record_stream_start()
        session = StreamSession(
            session_id="test123",
            stream_type=StreamType.WEBSOCKET,
            chunks_sent=5,
            bytes_sent=500
        )
        stream_metrics.record_stream_success(session)
        
        metrics = stream_metrics.get_metrics()
        
        assert "total_streams" in metrics
        assert "successful_streams" in metrics
        assert "success_rate" in metrics
        assert metrics["total_streams"] == 1
        assert metrics["successful_streams"] == 1
        assert metrics["success_rate"] == 1.0


class TestStreamProcessor:
    """Test StreamProcessor functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_stream_creation(self, stream_processor, mock_chat_orchestrator):
        """Test creating WebSocket stream."""
        chat_request = ChatRequest(
            message="Hello world",
            user_id="user1",
            conversation_id="conv1",
            stream=True
        )
        
        sent_chunks = []
        
        async def mock_websocket_send(chunk: StreamChunk):
            sent_chunks.append(chunk)
        
        session_id = await stream_processor.create_websocket_stream(
            chat_request,
            mock_websocket_send
        )
        
        assert session_id is not None
        assert session_id in stream_processor.active_sessions
        
        # Wait for processing to complete
        await asyncio.sleep(0.5)
        
        # Check that chunks were sent
        assert len(sent_chunks) > 0
        
        # Check that chat orchestrator was called
        assert len(mock_chat_orchestrator.process_calls) > 0
    
    @pytest.mark.asyncio
    async def test_sse_stream_creation(self, stream_processor, mock_request):
        """Test creating Server-Sent Events stream."""
        chat_request = ChatRequest(
            message="Hello world",
            user_id="user1",
            conversation_id="conv1",
            stream=True
        )
        
        sse_response = await stream_processor.create_sse_stream(chat_request, mock_request)
        
        assert sse_response is not None
        # Note: Full SSE testing would require more complex mocking of EventSourceResponse
    
    @pytest.mark.asyncio
    async def test_http_stream_creation(self, stream_processor, mock_request):
        """Test creating HTTP stream."""
        chat_request = ChatRequest(
            message="Hello world",
            user_id="user1",
            conversation_id="conv1",
            stream=True
        )
        
        http_response = await stream_processor.create_http_stream(chat_request, mock_request)
        
        assert http_response is not None
        # Note: Full HTTP streaming testing would require more complex mocking
    
    @pytest.mark.asyncio
    async def test_stream_processing_traditional(self, stream_processor, mock_chat_orchestrator):
        """Test stream processing with traditional response."""
        chat_request = ChatRequest(
            message="Hello world",
            user_id="user1",
            conversation_id="conv1",
            stream=False  # Traditional response
        )
        
        # Create a session manually for testing
        session_id = "test_session"
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.HTTP_STREAMING,
            user_id="user1",
            conversation_id="conv1",
            chunk_size=5  # Small chunks for testing
        )
        
        stream_processor.active_sessions[session_id] = session
        stream_processor.session_buffers[session_id] = StreamBuffer()
        
        chunks = []
        async for chunk in stream_processor._process_chat_stream(session_id, chat_request):
            chunks.append(chunk)
        
        # Should have metadata chunk, content chunks, and completion chunk
        assert len(chunks) > 2
        assert chunks[0].type == ChunkType.METADATA
        assert chunks[-1].type == ChunkType.COMPLETE
        
        # Check that content was chunked
        content_chunks = [c for c in chunks if c.type == ChunkType.CONTENT]
        assert len(content_chunks) > 0
    
    @pytest.mark.asyncio
    async def test_stream_pause_resume(self, stream_processor):
        """Test pausing and resuming streams."""
        # Create a session
        session_id = "test_session"
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.WEBSOCKET
        )
        stream_processor.active_sessions[session_id] = session
        
        # Test pause
        success = await stream_processor.pause_stream(session_id)
        assert success
        assert session.status == StreamStatus.PAUSED
        assert session.pause_requested
        
        # Test resume
        success = await stream_processor.resume_stream(session_id)
        assert success
        assert session.status == StreamStatus.STREAMING
        assert not session.pause_requested
    
    @pytest.mark.asyncio
    async def test_stream_cancellation(self, stream_processor):
        """Test cancelling streams."""
        # Create a session
        session_id = "test_session"
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.WEBSOCKET
        )
        stream_processor.active_sessions[session_id] = session
        
        # Test cancel
        success = await stream_processor.cancel_stream(session_id)
        assert success
        assert session.status == StreamStatus.INTERRUPTED
        assert session.cancel_requested
    
    @pytest.mark.asyncio
    async def test_stream_recovery(self, stream_processor):
        """Test stream recovery."""
        # Create a session with buffer
        session_id = "test_session"
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.WEBSOCKET
        )
        stream_processor.active_sessions[session_id] = session
        stream_processor.session_buffers[session_id] = StreamBuffer()
        
        # Add some chunks to buffer
        buffer = stream_processor.session_buffers[session_id]
        for i in range(5):
            chunk = StreamChunk(
                type=ChunkType.CONTENT,
                content=f"chunk{i}",
                sequence_number=i
            )
            await buffer.add_chunk(chunk)
        
        # Test recovery
        success = await stream_processor.recover_stream(session_id, from_sequence_number=2)
        assert success
        assert session.recovery_attempts == 1
        assert session.resume_from_chunk == 2
    
    @pytest.mark.asyncio
    async def test_get_stream_status(self, stream_processor):
        """Test getting stream status."""
        # Create a session
        session_id = "test_session"
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.WEBSOCKET,
            user_id="user1",
            conversation_id="conv1",
            chunks_sent=10,
            bytes_sent=1000
        )
        stream_processor.active_sessions[session_id] = session
        
        status = await stream_processor.get_stream_status(session_id)
        
        assert status is not None
        assert status["session_id"] == session_id
        assert status["status"] == StreamStatus.STARTING.value
        assert status["stream_type"] == StreamType.WEBSOCKET.value
        assert status["chunks_sent"] == 10
        assert status["bytes_sent"] == 1000
        assert status["user_id"] == "user1"
        assert status["conversation_id"] == "conv1"
    
    @pytest.mark.asyncio
    async def test_list_active_streams(self, stream_processor):
        """Test listing active streams."""
        # Create some sessions
        for i in range(3):
            session_id = f"session_{i}"
            session = StreamSession(
                session_id=session_id,
                stream_type=StreamType.WEBSOCKET,
                status=StreamStatus.STREAMING if i < 2 else StreamStatus.COMPLETED
            )
            stream_processor.active_sessions[session_id] = session
        
        active_streams = await stream_processor.list_active_streams()
        
        # Should only return streaming sessions
        assert len(active_streams) == 2
    
    def test_get_performance_metrics(self, stream_processor):
        """Test getting performance metrics."""
        metrics = stream_processor.get_performance_metrics()
        
        assert "total_streams" in metrics
        assert "successful_streams" in metrics
        assert "failed_streams" in metrics
        assert "success_rate" in metrics
        assert "avg_stream_duration" in metrics
    
    def test_get_active_session_count(self, stream_processor):
        """Test getting active session count."""
        # Create some sessions
        for i in range(3):
            session_id = f"session_{i}"
            session = StreamSession(
                session_id=session_id,
                stream_type=StreamType.WEBSOCKET,
                status=StreamStatus.STREAMING if i < 2 else StreamStatus.COMPLETED
            )
            stream_processor.active_sessions[session_id] = session
        
        count = stream_processor.get_active_session_count()
        assert count == 2  # Only streaming sessions
    
    @pytest.mark.asyncio
    async def test_cleanup(self, stream_processor):
        """Test stream processor cleanup."""
        # Create some sessions
        for i in range(3):
            session_id = f"session_{i}"
            session = StreamSession(
                session_id=session_id,
                stream_type=StreamType.WEBSOCKET
            )
            stream_processor.active_sessions[session_id] = session
            stream_processor.session_buffers[session_id] = StreamBuffer()
        
        # Cleanup
        await stream_processor.cleanup()
        
        # Check that sessions were cleaned up
        assert len(stream_processor.active_sessions) == 0
        assert len(stream_processor.session_buffers) == 0


class TestStreamSession:
    """Test StreamSession functionality."""
    
    def test_stream_session_creation(self):
        """Test creating stream session."""
        session = StreamSession(
            session_id="test123",
            stream_type=StreamType.SERVER_SENT_EVENTS,
            user_id="user1",
            conversation_id="conv1"
        )
        
        assert session.session_id == "test123"
        assert session.stream_type == StreamType.SERVER_SENT_EVENTS
        assert session.status == StreamStatus.STARTING
        assert session.user_id == "user1"
        assert session.conversation_id == "conv1"
        assert session.started_at is not None
        assert session.chunks_sent == 0
        assert session.bytes_sent == 0
    
    def test_stream_session_defaults(self):
        """Test stream session default values."""
        session = StreamSession(
            session_id="test123",
            stream_type=StreamType.WEBSOCKET
        )
        
        assert session.chunk_size == 1024
        assert session.chunk_delay == 0.05
        assert session.heartbeat_interval == 30.0
        assert session.timeout == 300.0
        assert session.max_interruptions == 3
        assert session.max_recovery_attempts == 3


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])