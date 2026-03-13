"""
Async Stream Processor with Non-Blocking Operations

This module provides efficient streaming response processing with:
- Fully async/await patterns for all I/O operations
- Proper timeout handling and connection pooling
- Thread-safe shared state management
- Backpressure handling and flow control
- Comprehensive error handling and recovery
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import weakref

from ..core.config_manager import get_config_manager
from ..core.logging.logger import get_structured_logger
from ..core.metrics_manager import get_metrics_manager

logger = logging.getLogger(__name__)

class StreamStatus(Enum):
    """Stream processing status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class StreamChunk:
    """Stream chunk data structure"""
    chunk_id: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    finished: bool = False

@dataclass
class StreamSession:
    """Stream session tracking"""
    session_id: str
    user_id: str
    response_id: str
    status: StreamStatus
    created_at: datetime
    updated_at: datetime
    chunks_sent: int = 0
    bytes_sent: int = 0
    error_count: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AsyncStreamProcessor:
    """
    Async stream processor with non-blocking operations and proper resource management
    """
    
    def __init__(self,
                 max_concurrent_streams: int = 100,
                 chunk_timeout: int = 30,
                 max_chunk_size: int = 8192,
                 backpressure_threshold: int = 10):
        self.max_concurrent_streams = max_concurrent_streams
        self.chunk_timeout = chunk_timeout
        self.max_chunk_size = max_chunk_size
        self.backpressure_threshold = backpressure_threshold
        
        # Thread-safe session storage
        self._sessions: Dict[str, StreamSession] = {}
        self._session_lock = asyncio.Lock()
        
        # Connection pooling
        self._connection_pool = None
        self._pool_lock = asyncio.Lock()
        
        # Rate limiting per user
        self._user_rates: Dict[str, List[datetime]] = {}
        self._rate_lock = asyncio.Lock()
        
        # Configuration and logging
        self.config_manager = get_config_manager()
        self.structured_logger = get_structured_logger()
        self.metrics_manager = get_metrics_manager()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("AsyncStreamProcessor initialized")
    
    async def initialize(self):
        """Initialize the stream processor"""
        async with self._session_lock:
            if self._running:
                return
            
            self._running = True
            
            # Initialize connection pool
            await self._init_connection_pool()
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("AsyncStreamProcessor initialized successfully")
    
    async def _init_connection_pool(self):
        """Initialize connection pool for non-blocking I/O"""
        try:
            # This would be implemented based on your specific needs
            # For example, database connection pool, HTTP client pool, etc.
            self._connection_pool = {
                'initialized': True,
                'created_at': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    async def create_stream_session(self,
                                user_id: str,
                                response_id: str,
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new streaming session"""
        session_id = str(uuid.uuid4())
        
        async with self._session_lock:
            # Check concurrent stream limit
            active_streams = sum(
                1 for session in self._sessions.values()
                if session.status in [StreamStatus.ACTIVE, StreamStatus.INITIALIZING]
            )
            
            if active_streams >= self.max_concurrent_streams:
                raise Exception(f"Maximum concurrent streams ({self.max_concurrent_streams}) reached")
            
            # Check user rate limit
            await self._check_user_rate_limit(user_id)
            
            # Create session
            session = StreamSession(
                session_id=session_id,
                user_id=user_id,
                response_id=response_id,
                status=StreamStatus.INITIALIZING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self._sessions[session_id] = session
            
            # Record metrics
            self.metrics_manager.register_counter(
                'stream_sessions_created_total',
                ['user_type']
            ).labels(user_type='user').inc()
            
            self.structured_logger.log_event(
                event="stream_session_created",
                user_id=user_id,
                details={
                    'session_id': session_id,
                    'response_id': response_id,
                    'active_streams': active_streams + 1
                }
            )
            
            return session_id
    
    async def _check_user_rate_limit(self, user_id: str):
        """Check if user exceeds rate limits"""
        async with self._rate_lock:
            now = datetime.utcnow()
            
            # Clean old entries (older than 1 minute)
            cutoff = now - timedelta(minutes=1)
            if user_id in self._user_rates:
                self._user_rates[user_id] = [
                    timestamp for timestamp in self._user_rates[user_id]
                    if timestamp > cutoff
                ]
            else:
                self._user_rates[user_id] = []
            
            # Check rate limit (e.g., max 10 streams per minute)
            if len(self._user_rates[user_id]) >= 10:
                raise Exception(f"User rate limit exceeded for {user_id}")
            
            # Record this stream
            self._user_rates[user_id].append(now)
    
    async def process_streaming_response(self,
                                    messages: List[Dict[str, Any]],
                                    model: Optional[str],
                                    temperature: Optional[float],
                                    max_tokens: Optional[int],
                                    session_id: str,
                                    user_id: str,
                                    response_id: str) -> AsyncGenerator[StreamChunk, None]:
        """
        Process streaming response with non-blocking operations
        """
        try:
            # Update session status
            await self._update_session_status(session_id, StreamStatus.ACTIVE)
            
            # Simulate model response generation (non-blocking)
            response_generator = self._generate_response_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            chunk_id = 0
            bytes_sent = 0
            
            async for chunk_data in response_generator:
                # Check for cancellation
                session = await self._get_session(session_id)
                if not session or session.status == StreamStatus.CANCELLED:
                    break
                
                # Create stream chunk
                chunk = StreamChunk(
                    chunk_id=chunk_id,
                    content=chunk_data,
                    metadata={
                        'model': model,
                        'session_id': session_id,
                        'response_id': response_id
                    }
                )
                
                # Send chunk with timeout
                try:
                    await asyncio.wait_for(
                        self._send_chunk(chunk),
                        timeout=self.chunk_timeout
                    )
                except asyncio.TimeoutError:
                    await self._update_session_status(session_id, StreamStatus.TIMEOUT)
                    break
                
                # Update session
                chunk_id += 1
                bytes_sent += len(chunk_data.encode('utf-8'))
                
                await self._update_session_progress(
                    session_id,
                    chunks_sent=chunk_id,
                    bytes_sent=bytes_sent
                )
                
                # Check backpressure
                if await self._check_backpressure(session_id):
                    await asyncio.sleep(0.1)  # Brief pause to reduce pressure
            
            # Mark session as completed
            await self._update_session_status(session_id, StreamStatus.COMPLETED)
            
            # Record metrics
            processing_time = (datetime.utcnow() - session.created_at).total_seconds()
            self.metrics_manager.register_histogram(
                'stream_session_duration_seconds',
                ['status']
            ).labels(status='completed').observe(processing_time)
            
            self.metrics_manager.register_counter(
                'stream_chunks_sent_total'
            ).inc(chunk_id)
            
        except Exception as e:
            await self._update_session_status(session_id, StreamStatus.ERROR)
            await self._increment_session_errors(session_id)
            
            self.structured_logger.log_error(
                error=str(e),
                user_id=user_id,
                context="stream_processing",
                details={
                    'session_id': session_id,
                    'response_id': response_id
                }
            )
            
            # Record error metrics
            self.metrics_manager.register_counter(
                'stream_session_errors_total',
                ['error_type']
            ).labels(error_type=type(e).__name__).inc()
    
    async def _generate_response_stream(self,
                                    messages: List[Dict[str, Any]],
                                    model: Optional[str],
                                    temperature: Optional[float],
                                    max_tokens: Optional[int]) -> AsyncGenerator[str, None]:
        """Generate response stream using non-blocking operations"""
        # This would integrate with your actual model inference
        # For demonstration, we'll simulate streaming
        
        full_response = "This is a simulated streaming response. " * 20  # Make it longer
        
        words = full_response.split()
        for i, word in enumerate(words):
            # Simulate processing delay (non-blocking)
            await asyncio.sleep(0.05)  # 50ms per word
            
            yield word + " "
            
            # Check for max tokens
            if max_tokens and i >= max_tokens:
                break
    
    async def _send_chunk(self, chunk: StreamChunk):
        """Send chunk using non-blocking I/O"""
        try:
            # This would use your actual transport mechanism
            # For demonstration, we'll just simulate the send
            
            # Simulate network I/O (non-blocking)
            await asyncio.sleep(0.01)  # Simulate network latency
            
            # In real implementation, this would be:
            # await websocket.send_text(chunk.content)
            # await response.write(chunk.content)
            # etc.
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending chunk {chunk.chunk_id}: {e}")
            raise
    
    async def _check_backpressure(self, session_id: str) -> bool:
        """Check if stream is experiencing backpressure"""
        try:
            session = await self._get_session(session_id)
            if not session:
                return False
            
            # Simple backpressure detection based on error rate
            if session.error_count > 5:
                return True
            
            # Check if chunks are being processed too slowly
            time_since_last_activity = (datetime.utcnow() - session.last_activity).total_seconds()
            if time_since_last_activity > 30:  # 30 seconds of inactivity
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking backpressure: {e}")
            return False
    
    async def _update_session_status(self, session_id: str, status: StreamStatus):
        """Update session status thread-safely"""
        async with self._session_lock:
            if session_id in self._sessions:
                self._sessions[session_id].status = status
                self._sessions[session_id].updated_at = datetime.utcnow()
                self._sessions[session_id].last_activity = datetime.utcnow()
    
    async def _update_session_progress(self,
                                   session_id: str,
                                   chunks_sent: Optional[int] = None,
                                   bytes_sent: Optional[int] = None):
        """Update session progress thread-safely"""
        async with self._session_lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                if chunks_sent is not None:
                    session.chunks_sent = chunks_sent
                if bytes_sent is not None:
                    session.bytes_sent = bytes_sent
                session.last_activity = datetime.utcnow()
    
    async def _increment_session_errors(self, session_id: str):
        """Increment session error count thread-safely"""
        async with self._session_lock:
            if session_id in self._sessions:
                self._sessions[session_id].error_count += 1
    
    async def _get_session(self, session_id: str) -> Optional[StreamSession]:
        """Get session thread-safely"""
        async with self._session_lock:
            return self._sessions.get(session_id)
    
    async def cancel_stream(self, session_id: str, user_id: str) -> bool:
        """Cancel a streaming session"""
        try:
            session = await self._get_session(session_id)
            
            if not session or session.user_id != user_id:
                return False
            
            await self._update_session_status(session_id, StreamStatus.CANCELLED)
            
            # Record metrics
            self.metrics_manager.register_counter(
                'stream_sessions_cancelled_total'
            ).inc()
            
            self.structured_logger.log_event(
                event="stream_session_cancelled",
                user_id=user_id,
                details={'session_id': session_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling stream {session_id}: {e}")
            return False
    
    async def get_session_info(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get session information with access control"""
        try:
            session = await self._get_session(session_id)
            
            if not session or session.user_id != user_id:
                return None
            
            return {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'response_id': session.response_id,
                'status': session.status.value,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'chunks_sent': session.chunks_sent,
                'bytes_sent': session.bytes_sent,
                'error_count': session.error_count,
                'last_activity': session.last_activity.isoformat(),
                'metadata': session.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting session info {session_id}: {e}")
            return None
    
    async def _cleanup_loop(self):
        """Background cleanup loop for expired sessions"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                async with self._session_lock:
                    now = datetime.utcnow()
                    expired_sessions = []
                    
                    for session_id, session in self._sessions.items():
                        # Clean up sessions older than 1 hour or in error state
                        age = (now - session.created_at).total_seconds()
                        if age > 3600 or session.status == StreamStatus.ERROR:
                            expired_sessions.append(session_id)
                    
                    # Remove expired sessions
                    for session_id in expired_sessions:
                        del self._sessions[session_id]
                    
                    if expired_sessions:
                        self.structured_logger.log_event(
                            event="stream_sessions_cleaned",
                            details={
                                'expired_count': len(expired_sessions),
                                'remaining_sessions': len(self._sessions)
                            }
                        )
                
                # Clean up old rate limit entries
                async with self._rate_lock:
                    cutoff = now - timedelta(minutes=5)
                    for user_id in list(self._user_rates.keys()):
                        self._user_rates[user_id] = [
                            timestamp for timestamp in self._user_rates[user_id]
                            if timestamp > cutoff
                        ]
                        
                        if not self._user_rates[user_id]:
                            del self._user_rates[user_id]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def shutdown(self):
        """Shutdown the stream processor gracefully"""
        self._running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all active sessions
        async with self._session_lock:
            for session_id, session in self._sessions.items():
                if session.status in [StreamStatus.ACTIVE, StreamStatus.INITIALIZING]:
                    await self._update_session_status(session_id, StreamStatus.CANCELLED)
        
        # Close connection pool
        if self._connection_pool:
            # Close connections based on your implementation
            pass
        
        logger.info("AsyncStreamProcessor shutdown completed")
    
    async def health_check(self) -> bool:
        """Health check for the stream processor"""
        try:
            # Check if running
            if not self._running:
                return False
            
            # Check connection pool
            if not self._connection_pool:
                return False
            
            # Check cleanup task
            if not self._cleanup_task or self._cleanup_task.done():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get stream processor metrics"""
        async with self._session_lock:
            active_sessions = sum(
                1 for session in self._sessions.values()
                if session.status == StreamStatus.ACTIVE
            )
            
            total_sessions = len(self._sessions)
            
            status_counts = {}
            for status in StreamStatus:
                status_counts[status.value] = sum(
                    1 for session in self._sessions.values()
                    if session.status == status
                )
        
        return {
            'active_sessions': active_sessions,
            'total_sessions': total_sessions,
            'status_counts': status_counts,
            'max_concurrent_streams': self.max_concurrent_streams,
            'running': self._running,
            'connection_pool_healthy': bool(self._connection_pool)
        }

# Global processor instance
_stream_processor: Optional[AsyncStreamProcessor] = None

async def get_stream_processor() -> AsyncStreamProcessor:
    """Get global stream processor instance"""
    global _stream_processor
    if _stream_processor is None:
        _stream_processor = AsyncStreamProcessor()
        await _stream_processor.initialize()
    return _stream_processor
