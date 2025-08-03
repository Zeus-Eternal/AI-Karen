"""
Streaming Response Processor for Real-Time Chat

This module implements AI response streaming with chunked delivery,
Server-Sent Events fallback for streaming, stream interruption handling
and recovery, and streaming performance monitoring and optimization.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator, Union, Callable, Awaitable
from enum import Enum

try:
    from fastapi import Request, Response
    from fastapi.responses import StreamingResponse
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    # Stubs for testing
    class Request:
        def __init__(self): pass
    
    class Response:
        def __init__(self, content="", status_code=200): pass
    
    class StreamingResponse:
        def __init__(self, content, media_type="text/plain"): pass
    
    class EventSourceResponse:
        def __init__(self, content): pass

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest, ChatStreamChunk

logger = logging.getLogger(__name__)


class StreamType(str, Enum):
    """Types of streaming responses."""
    WEBSOCKET = "websocket"
    SERVER_SENT_EVENTS = "server_sent_events"
    HTTP_STREAMING = "http_streaming"


class StreamStatus(str, Enum):
    """Status of streaming response."""
    STARTING = "starting"
    STREAMING = "streaming"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"


class ChunkType(str, Enum):
    """Types of stream chunks."""
    METADATA = "metadata"
    CONTENT = "content"
    DELTA = "delta"
    COMPLETE = "complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    PROGRESS = "progress"


@dataclass
class StreamChunk:
    """Individual chunk in a streaming response."""
    type: ChunkType
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sequence_number: int = 0
    total_chunks: Optional[int] = None
    correlation_id: Optional[str] = None


@dataclass
class StreamSession:
    """Information about an active streaming session."""
    session_id: str
    stream_type: StreamType
    status: StreamStatus = StreamStatus.STARTING
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_chunk_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Stream configuration
    chunk_size: int = 1024
    chunk_delay: float = 0.05
    heartbeat_interval: float = 30.0
    timeout: float = 300.0
    
    # Progress tracking
    chunks_sent: int = 0
    bytes_sent: int = 0
    total_content_length: Optional[int] = None
    
    # Error handling
    interruption_count: int = 0
    max_interruptions: int = 3
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    
    # Performance metrics
    processing_time: float = 0.0
    network_time: float = 0.0
    queue_time: float = 0.0
    
    # Client information
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Stream control
    pause_requested: bool = False
    cancel_requested: bool = False
    resume_from_chunk: Optional[int] = None


class StreamBuffer:
    """Buffer for managing streaming content."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.chunks: List[StreamChunk] = []
        self.total_size = 0
        self._lock = asyncio.Lock()
    
    async def add_chunk(self, chunk: StreamChunk):
        """Add a chunk to the buffer."""
        async with self._lock:
            self.chunks.append(chunk)
            self.total_size += len(chunk.content)
            
            # Remove old chunks if buffer is full
            while self.total_size > self.max_size and self.chunks:
                old_chunk = self.chunks.pop(0)
                self.total_size -= len(old_chunk.content)
    
    async def get_chunks_from(self, sequence_number: int) -> List[StreamChunk]:
        """Get chunks starting from a specific sequence number."""
        async with self._lock:
            return [
                chunk for chunk in self.chunks
                if chunk.sequence_number >= sequence_number
            ]
    
    async def get_latest_chunks(self, count: int) -> List[StreamChunk]:
        """Get the latest N chunks."""
        async with self._lock:
            return self.chunks[-count:] if count <= len(self.chunks) else self.chunks
    
    async def clear(self):
        """Clear the buffer."""
        async with self._lock:
            self.chunks.clear()
            self.total_size = 0


class StreamMetrics:
    """Metrics collection for streaming performance."""
    
    def __init__(self):
        self.total_streams = 0
        self.successful_streams = 0
        self.failed_streams = 0
        self.interrupted_streams = 0
        self.recovered_streams = 0
        
        self.total_chunks_sent = 0
        self.total_bytes_sent = 0
        self.total_processing_time = 0.0
        self.total_network_time = 0.0
        
        self.stream_durations: List[float] = []
        self.chunk_sizes: List[int] = []
        self.recovery_times: List[float] = []
        
        # Performance tracking
        self.avg_chunk_size = 0.0
        self.avg_stream_duration = 0.0
        self.avg_processing_time = 0.0
        self.success_rate = 0.0
        self.recovery_rate = 0.0
    
    def record_stream_start(self):
        """Record the start of a new stream."""
        self.total_streams += 1
    
    def record_stream_success(self, session: StreamSession):
        """Record a successful stream completion."""
        self.successful_streams += 1
        self.total_chunks_sent += session.chunks_sent
        self.total_bytes_sent += session.bytes_sent
        self.total_processing_time += session.processing_time
        self.total_network_time += session.network_time
        
        if session.completed_at and session.started_at:
            duration = (session.completed_at - session.started_at).total_seconds()
            self.stream_durations.append(duration)
        
        self._update_averages()
    
    def record_stream_failure(self, session: StreamSession):
        """Record a failed stream."""
        self.failed_streams += 1
        self._update_averages()
    
    def record_stream_interruption(self, session: StreamSession):
        """Record a stream interruption."""
        self.interrupted_streams += 1
    
    def record_stream_recovery(self, session: StreamSession, recovery_time: float):
        """Record a successful stream recovery."""
        self.recovered_streams += 1
        self.recovery_times.append(recovery_time)
        self._update_averages()
    
    def record_chunk_sent(self, chunk_size: int):
        """Record a chunk being sent."""
        self.chunk_sizes.append(chunk_size)
        if len(self.chunk_sizes) > 1000:  # Keep only recent chunks
            self.chunk_sizes = self.chunk_sizes[-1000:]
    
    def _update_averages(self):
        """Update calculated averages."""
        if self.chunk_sizes:
            self.avg_chunk_size = sum(self.chunk_sizes) / len(self.chunk_sizes)
        
        if self.stream_durations:
            self.avg_stream_duration = sum(self.stream_durations) / len(self.stream_durations)
        
        if self.total_streams > 0:
            self.success_rate = self.successful_streams / self.total_streams
            self.avg_processing_time = self.total_processing_time / self.total_streams
        
        if self.interrupted_streams > 0:
            self.recovery_rate = self.recovered_streams / self.interrupted_streams
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            "total_streams": self.total_streams,
            "successful_streams": self.successful_streams,
            "failed_streams": self.failed_streams,
            "interrupted_streams": self.interrupted_streams,
            "recovered_streams": self.recovered_streams,
            "success_rate": self.success_rate,
            "recovery_rate": self.recovery_rate,
            "total_chunks_sent": self.total_chunks_sent,
            "total_bytes_sent": self.total_bytes_sent,
            "avg_chunk_size": self.avg_chunk_size,
            "avg_stream_duration": self.avg_stream_duration,
            "avg_processing_time": self.avg_processing_time,
            "recent_stream_durations": self.stream_durations[-10:],
            "recent_recovery_times": self.recovery_times[-10:]
        }


class StreamProcessor:
    """
    Streaming Response Processor for Real-Time Chat.
    
    Features:
    - AI response streaming with chunked delivery
    - Server-Sent Events fallback for streaming
    - Stream interruption handling and recovery
    - Streaming performance monitoring and optimization
    """
    
    def __init__(
        self,
        chat_orchestrator: ChatOrchestrator,
        default_chunk_size: int = 1024,
        default_chunk_delay: float = 0.05,
        heartbeat_interval: float = 30.0,
        stream_timeout: float = 300.0,
        enable_recovery: bool = True
    ):
        self.chat_orchestrator = chat_orchestrator
        self.default_chunk_size = default_chunk_size
        self.default_chunk_delay = default_chunk_delay
        self.heartbeat_interval = heartbeat_interval
        self.stream_timeout = stream_timeout
        self.enable_recovery = enable_recovery
        
        # Active streaming sessions
        self.active_sessions: Dict[str, StreamSession] = {}
        self.session_buffers: Dict[str, StreamBuffer] = {}
        
        # Metrics and monitoring
        self.metrics = StreamMetrics()
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        self._start_background_tasks()
        
        logger.info("StreamProcessor initialized")
    
    def _start_background_tasks(self):
        """Start background tasks for stream management."""
        try:
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        except RuntimeError:
            # No event loop running, will start tasks later
            self._heartbeat_task = None
            self._cleanup_task = None
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages to active streams."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                current_time = datetime.utcnow()
                for session_id, session in list(self.active_sessions.items()):
                    if session.status == StreamStatus.STREAMING:
                        # Check if heartbeat is needed
                        if (session.last_chunk_at and 
                            (current_time - session.last_chunk_at).total_seconds() > self.heartbeat_interval):
                            
                            heartbeat_chunk = StreamChunk(
                                type=ChunkType.HEARTBEAT,
                                content="",
                                metadata={"timestamp": current_time.isoformat()},
                                correlation_id=session_id
                            )
                            
                            # Add to buffer
                            if session_id in self.session_buffers:
                                await self.session_buffers[session_id].add_chunk(heartbeat_chunk)
                            
                            logger.debug(f"Sent heartbeat for session {session_id}")
                            
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(60.0)  # Wait longer on error
    
    async def _cleanup_loop(self):
        """Clean up expired streaming sessions."""
        while True:
            try:
                await asyncio.sleep(60.0)  # Check every minute
                
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    # Check for timeout
                    if (current_time - session.started_at).total_seconds() > session.timeout:
                        expired_sessions.append(session_id)
                    
                    # Check for completed sessions that can be cleaned up
                    elif (session.status in [StreamStatus.COMPLETED, StreamStatus.FAILED] and
                          session.completed_at and
                          (current_time - session.completed_at).total_seconds() > 300):  # 5 minutes
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self._cleanup_session(session_id, "Session expired")
                    
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300.0)  # Wait longer on error
    
    async def create_websocket_stream(
        self,
        chat_request: ChatRequest,
        websocket_send_func: Callable[[StreamChunk], Awaitable[None]],
        session_id: Optional[str] = None
    ) -> str:
        """
        Create a WebSocket streaming session.
        
        Args:
            chat_request: Chat request to process
            websocket_send_func: Function to send chunks via WebSocket
            session_id: Optional session ID
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Create session
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.WEBSOCKET,
            user_id=chat_request.user_id,
            conversation_id=chat_request.conversation_id
        )
        
        self.active_sessions[session_id] = session
        self.session_buffers[session_id] = StreamBuffer()
        self.metrics.record_stream_start()
        
        # Start streaming task
        asyncio.create_task(self._process_websocket_stream(session_id, chat_request, websocket_send_func))
        
        return session_id
    
    async def create_sse_stream(
        self,
        chat_request: ChatRequest,
        request: Request
    ) -> EventSourceResponse:
        """
        Create a Server-Sent Events streaming response.
        
        Args:
            chat_request: Chat request to process
            request: HTTP request object
            
        Returns:
            EventSourceResponse for SSE streaming
        """
        session_id = str(uuid.uuid4())
        
        # Create session
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.SERVER_SENT_EVENTS,
            user_id=chat_request.user_id,
            conversation_id=chat_request.conversation_id,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        self.active_sessions[session_id] = session
        self.session_buffers[session_id] = StreamBuffer()
        self.metrics.record_stream_start()
        
        # Create SSE generator
        async def sse_generator():
            try:
                async for chunk in self._process_chat_stream(session_id, chat_request):
                    # Format as SSE event
                    event_data = {
                        "type": chunk.type.value,
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "chunk_id": chunk.chunk_id,
                        "sequence_number": chunk.sequence_number,
                        "timestamp": chunk.timestamp.isoformat()
                    }
                    
                    yield {
                        "event": chunk.type.value,
                        "data": json.dumps(event_data),
                        "id": chunk.chunk_id
                    }
                    
                    # Add delay between chunks
                    if chunk.type == ChunkType.CONTENT:
                        await asyncio.sleep(session.chunk_delay)
                        
            except Exception as e:
                logger.error(f"Error in SSE stream {session_id}: {e}")
                error_chunk = {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                    "id": str(uuid.uuid4())
                }
                yield error_chunk
            finally:
                await self._cleanup_session(session_id, "SSE stream completed")
        
        return EventSourceResponse(sse_generator())
    
    async def create_http_stream(
        self,
        chat_request: ChatRequest,
        request: Request
    ) -> StreamingResponse:
        """
        Create an HTTP streaming response.
        
        Args:
            chat_request: Chat request to process
            request: HTTP request object
            
        Returns:
            StreamingResponse for HTTP streaming
        """
        session_id = str(uuid.uuid4())
        
        # Create session
        session = StreamSession(
            session_id=session_id,
            stream_type=StreamType.HTTP_STREAMING,
            user_id=chat_request.user_id,
            conversation_id=chat_request.conversation_id,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        self.active_sessions[session_id] = session
        self.session_buffers[session_id] = StreamBuffer()
        self.metrics.record_stream_start()
        
        # Create HTTP streaming generator
        async def http_generator():
            try:
                async for chunk in self._process_chat_stream(session_id, chat_request):
                    # Format as JSON lines
                    chunk_data = {
                        "type": chunk.type.value,
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "chunk_id": chunk.chunk_id,
                        "sequence_number": chunk.sequence_number,
                        "timestamp": chunk.timestamp.isoformat()
                    }
                    
                    yield json.dumps(chunk_data) + "\n"
                    
                    # Add delay between chunks
                    if chunk.type == ChunkType.CONTENT:
                        await asyncio.sleep(session.chunk_delay)
                        
            except Exception as e:
                logger.error(f"Error in HTTP stream {session_id}: {e}")
                error_data = {
                    "type": "error",
                    "content": "",
                    "metadata": {"error": str(e)},
                    "chunk_id": str(uuid.uuid4()),
                    "sequence_number": -1,
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield json.dumps(error_data) + "\n"
            finally:
                await self._cleanup_session(session_id, "HTTP stream completed")
        
        return StreamingResponse(
            http_generator(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    async def _process_websocket_stream(
        self,
        session_id: str,
        chat_request: ChatRequest,
        websocket_send_func: Callable[[StreamChunk], Awaitable[None]]
    ):
        """Process WebSocket streaming session."""
        session = self.active_sessions[session_id]
        
        try:
            session.status = StreamStatus.STREAMING
            
            async for chunk in self._process_chat_stream(session_id, chat_request):
                # Send via WebSocket
                await websocket_send_func(chunk)
                
                # Add delay between content chunks
                if chunk.type == ChunkType.CONTENT:
                    await asyncio.sleep(session.chunk_delay)
            
            session.status = StreamStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            self.metrics.record_stream_success(session)
            
        except Exception as e:
            logger.error(f"Error in WebSocket stream {session_id}: {e}")
            session.status = StreamStatus.FAILED
            session.completed_at = datetime.utcnow()
            self.metrics.record_stream_failure(session)
            
            # Send error chunk
            error_chunk = StreamChunk(
                type=ChunkType.ERROR,
                content="",
                metadata={"error": str(e)},
                correlation_id=session_id
            )
            
            try:
                await websocket_send_func(error_chunk)
            except Exception:
                pass  # Connection might be closed
        
        finally:
            await self._cleanup_session(session_id, "WebSocket stream completed")
    
    async def _process_chat_stream(
        self,
        session_id: str,
        chat_request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Process chat request and generate stream chunks."""
        session = self.active_sessions[session_id]
        buffer = self.session_buffers[session_id]
        
        start_time = time.time()
        sequence_number = 0
        
        try:
            # Send initial metadata chunk
            metadata_chunk = StreamChunk(
                type=ChunkType.METADATA,
                content="",
                metadata={
                    "session_id": session_id,
                    "user_id": session.user_id,
                    "conversation_id": session.conversation_id,
                    "stream_type": session.stream_type.value,
                    "started_at": session.started_at.isoformat()
                },
                sequence_number=sequence_number,
                correlation_id=session_id
            )
            
            await buffer.add_chunk(metadata_chunk)
            yield metadata_chunk
            sequence_number += 1
            
            # Process with chat orchestrator
            if chat_request.stream:
                # Handle streaming response
                async for chat_chunk in await self.chat_orchestrator.process_message(chat_request):
                    # Check for interruption
                    if session.cancel_requested:
                        break
                    
                    # Handle pause
                    while session.pause_requested and not session.cancel_requested:
                        await asyncio.sleep(0.1)
                    
                    # Convert chat chunk to stream chunk
                    if chat_chunk.type == "content":
                        chunk = StreamChunk(
                            type=ChunkType.CONTENT,
                            content=chat_chunk.content,
                            metadata=chat_chunk.metadata,
                            sequence_number=sequence_number,
                            correlation_id=session_id
                        )
                    elif chat_chunk.type == "complete":
                        chunk = StreamChunk(
                            type=ChunkType.COMPLETE,
                            content="",
                            metadata=chat_chunk.metadata,
                            sequence_number=sequence_number,
                            correlation_id=session_id
                        )
                    elif chat_chunk.type == "error":
                        chunk = StreamChunk(
                            type=ChunkType.ERROR,
                            content=chat_chunk.content,
                            metadata=chat_chunk.metadata,
                            sequence_number=sequence_number,
                            correlation_id=session_id
                        )
                    else:
                        # Metadata or other chunk types
                        chunk = StreamChunk(
                            type=ChunkType.METADATA,
                            content=chat_chunk.content,
                            metadata=chat_chunk.metadata,
                            sequence_number=sequence_number,
                            correlation_id=session_id
                        )
                    
                    # Update session metrics
                    session.chunks_sent += 1
                    session.bytes_sent += len(chunk.content)
                    session.last_chunk_at = datetime.utcnow()
                    
                    # Record chunk metrics
                    self.metrics.record_chunk_sent(len(chunk.content))
                    
                    # Add to buffer and yield
                    await buffer.add_chunk(chunk)
                    yield chunk
                    sequence_number += 1
                    
                    # Break on completion or error
                    if chunk.type in [ChunkType.COMPLETE, ChunkType.ERROR]:
                        break
            else:
                # Handle traditional response
                response = await self.chat_orchestrator.process_message(chat_request)
                
                # Split response into chunks
                content = response.response
                chunk_size = session.chunk_size
                
                for i in range(0, len(content), chunk_size):
                    # Check for interruption
                    if session.cancel_requested:
                        break
                    
                    # Handle pause
                    while session.pause_requested and not session.cancel_requested:
                        await asyncio.sleep(0.1)
                    
                    chunk_content = content[i:i + chunk_size]
                    is_last_chunk = i + chunk_size >= len(content)
                    
                    chunk = StreamChunk(
                        type=ChunkType.CONTENT,
                        content=chunk_content,
                        metadata={
                            "is_last_chunk": is_last_chunk,
                            "chunk_index": i // chunk_size,
                            "total_length": len(content)
                        },
                        sequence_number=sequence_number,
                        total_chunks=len(content) // chunk_size + (1 if len(content) % chunk_size else 0),
                        correlation_id=session_id
                    )
                    
                    # Update session metrics
                    session.chunks_sent += 1
                    session.bytes_sent += len(chunk.content)
                    session.last_chunk_at = datetime.utcnow()
                    
                    # Record chunk metrics
                    self.metrics.record_chunk_sent(len(chunk.content))
                    
                    # Add to buffer and yield
                    await buffer.add_chunk(chunk)
                    yield chunk
                    sequence_number += 1
                
                # Send completion chunk
                completion_chunk = StreamChunk(
                    type=ChunkType.COMPLETE,
                    content="",
                    metadata={
                        "processing_time": response.processing_time,
                        "used_fallback": response.used_fallback,
                        "context_used": response.context_used,
                        "total_chunks": sequence_number,
                        "total_bytes": session.bytes_sent
                    },
                    sequence_number=sequence_number,
                    correlation_id=session_id
                )
                
                await buffer.add_chunk(completion_chunk)
                yield completion_chunk
            
            # Update session timing
            session.processing_time = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Error processing chat stream {session_id}: {e}")
            
            # Send error chunk
            error_chunk = StreamChunk(
                type=ChunkType.ERROR,
                content="",
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "sequence_number": sequence_number
                },
                sequence_number=sequence_number,
                correlation_id=session_id
            )
            
            await buffer.add_chunk(error_chunk)
            yield error_chunk
            
            raise
    
    async def pause_stream(self, session_id: str) -> bool:
        """Pause a streaming session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.pause_requested = True
        session.status = StreamStatus.PAUSED
        
        logger.info(f"Paused stream session {session_id}")
        return True
    
    async def resume_stream(self, session_id: str) -> bool:
        """Resume a paused streaming session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.pause_requested = False
        session.status = StreamStatus.STREAMING
        
        logger.info(f"Resumed stream session {session_id}")
        return True
    
    async def cancel_stream(self, session_id: str) -> bool:
        """Cancel a streaming session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.cancel_requested = True
        session.status = StreamStatus.INTERRUPTED
        
        logger.info(f"Cancelled stream session {session_id}")
        return True
    
    async def recover_stream(
        self,
        session_id: str,
        from_sequence_number: Optional[int] = None
    ) -> bool:
        """
        Recover an interrupted streaming session.
        
        Args:
            session_id: Session ID to recover
            from_sequence_number: Sequence number to resume from
            
        Returns:
            True if recovery was initiated
        """
        if not self.enable_recovery or session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        if session.recovery_attempts >= session.max_recovery_attempts:
            logger.warning(f"Max recovery attempts reached for session {session_id}")
            return False
        
        session.recovery_attempts += 1
        session.status = StreamStatus.STREAMING
        session.resume_from_chunk = from_sequence_number
        
        recovery_start = time.time()
        
        # Get buffered chunks for recovery
        if session_id in self.session_buffers:
            buffer = self.session_buffers[session_id]
            
            if from_sequence_number is not None:
                recovery_chunks = await buffer.get_chunks_from(from_sequence_number)
            else:
                recovery_chunks = await buffer.get_latest_chunks(10)  # Last 10 chunks
            
            logger.info(f"Recovering session {session_id} with {len(recovery_chunks)} chunks")
            
            # Record recovery metrics
            recovery_time = time.time() - recovery_start
            self.metrics.record_stream_recovery(session, recovery_time)
            
            return True
        
        return False
    
    async def get_stream_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a streaming session."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "stream_type": session.stream_type.value,
            "started_at": session.started_at.isoformat(),
            "last_chunk_at": session.last_chunk_at.isoformat() if session.last_chunk_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "chunks_sent": session.chunks_sent,
            "bytes_sent": session.bytes_sent,
            "processing_time": session.processing_time,
            "interruption_count": session.interruption_count,
            "recovery_attempts": session.recovery_attempts,
            "user_id": session.user_id,
            "conversation_id": session.conversation_id
        }
    
    async def list_active_streams(self) -> List[Dict[str, Any]]:
        """List all active streaming sessions."""
        active_streams = []
        
        for session_id, session in self.active_sessions.items():
            if session.status in [StreamStatus.STREAMING, StreamStatus.PAUSED]:
                stream_info = await self.get_stream_status(session_id)
                if stream_info:
                    active_streams.append(stream_info)
        
        return active_streams
    
    async def _cleanup_session(self, session_id: str, reason: str):
        """Clean up a streaming session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            if session.status not in [StreamStatus.COMPLETED, StreamStatus.FAILED]:
                session.status = StreamStatus.COMPLETED
                session.completed_at = datetime.utcnow()
            
            del self.active_sessions[session_id]
        
        if session_id in self.session_buffers:
            await self.session_buffers[session_id].clear()
            del self.session_buffers[session_id]
        
        logger.debug(f"Cleaned up session {session_id}: {reason}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get streaming performance metrics."""
        return self.metrics.get_metrics()
    
    def get_active_session_count(self) -> int:
        """Get count of active streaming sessions."""
        return len([
            session for session in self.active_sessions.values()
            if session.status in [StreamStatus.STREAMING, StreamStatus.PAUSED]
        ])
    
    async def cleanup(self):
        """Clean up the stream processor."""
        # Cancel background tasks
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        # Clean up all sessions
        for session_id in list(self.active_sessions.keys()):
            await self._cleanup_session(session_id, "Stream processor shutdown")
        
        logger.info("StreamProcessor cleaned up")