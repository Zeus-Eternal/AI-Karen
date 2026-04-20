"""
Stream Authority Module

This module provides centralized control over all streaming requests, ensuring:
- Single entry point for all streaming requests
- Centralized control over stream lifecycle
- Pipeline validation and monitoring
- Guaranteed terminal events
- Timeout enforcement and fallback handling
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

from ..config.config_manager import get_config_manager
from ..core.logging.logger import get_structured_logger
from ..core.metrics_manager import get_metrics_manager
from ..chat.stream_processor import AsyncStreamProcessor, StreamChunk, StreamStatus
from ..core.chat_runtime_control_plane import (
    get_chat_runtime_control_plane,
    ChatRuntimeControlPlane,
)

logger = logging.getLogger(__name__)


class StreamAuthorityStatus(Enum):
    """Stream authority status"""

    ACTIVE = "active"
    THROTTLED = "throttled"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"


@dataclass
class StreamAuthorityConfig:
    """Stream authority configuration"""

    # Timeout settings
    first_token_timeout: int = 15  # seconds
    chunk_timeout: int = 30  # seconds
    stream_timeout: int = 300  # seconds (5 minutes)

    # Rate limiting
    max_concurrent_streams: int = 100
    max_streams_per_user: int = 10
    streams_per_minute: int = 30

    # Fallback settings
    enable_fallback: bool = True
    fallback_timeout: int = 10  # seconds
    max_fallback_attempts: int = 2

    # Circuit breaker settings
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_max_requests: int = 3


@dataclass
class StreamAuthoritySession:
    """Stream authority session tracking"""

    session_id: str
    user_id: str
    response_id: str
    status: StreamAuthorityStatus
    created_at: datetime
    last_activity: datetime
    first_token_sent: bool = False
    last_chunk_time: Optional[datetime] = None
    timeout_count: int = 0
    error_count: int = 0
    fallback_attempts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamAuthority:
    """
    Centralized stream authority that controls all streaming requests.

    This class ensures:
    - Single entry point for all streaming requests
    - Guaranteed terminal events for all streams
    - Timeout enforcement and fallback handling
    - Complete observability and monitoring
    """

    def __init__(self, config: Optional[StreamAuthorityConfig] = None):
        self.config = config or StreamAuthorityConfig()

        # Core components
        self.stream_processor: Optional[AsyncStreamProcessor] = None
        self.control_plane: Optional[ChatRuntimeControlPlane] = None

        # Session management
        self._sessions: Dict[str, StreamAuthoritySession] = {}
        self._session_lock = asyncio.Lock()

        # Rate limiting
        self._user_streams: Dict[str, List[datetime]] = {}
        self._rate_lock = asyncio.Lock()

        # Circuit breaker state
        self._circuit_state = "closed"  # closed, open, half_open
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None

        # Configuration and logging
        self.config_manager = get_config_manager()
        self.structured_logger = get_structured_logger()
        self.metrics_manager = get_metrics_manager()

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("StreamAuthority initialized")

    async def initialize(self):
        """Initialize the stream authority"""
        if self._running:
            return

        self._running = True

        # Initialize dependencies
        self.stream_processor = AsyncStreamProcessor()
        await self.stream_processor.initialize()

        self.control_plane = get_chat_runtime_control_plane()

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("StreamAuthority initialized successfully")

    async def authorize_stream_request(
        self,
        user_id: str,
        messages: List[Dict[str, Any]],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        stream: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Authorize and process streaming requests with guaranteed terminal events.

        Args:
            user_id: User identifier
            messages: Conversation messages
            model: Model to use
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            stream: Whether to stream response
            metadata: Additional metadata

        Yields:
            Streaming response chunks with guaranteed terminal events
        """
        session_id = str(uuid.uuid4())
        response_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())

        try:
            # Pre-authorization checks
            await self._pre_authorize_session(user_id, session_id)

            # Create authority session
            session = StreamAuthoritySession(
                session_id=session_id,
                user_id=user_id,
                response_id=response_id,
                status=StreamAuthorityStatus.ACTIVE,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                metadata=metadata or {},
            )

            async with self._session_lock:
                self._sessions[session_id] = session

            # Record metrics
            self.metrics_manager.register_counter(
                "stream_authority_requests_total", ["status"]
            ).labels(status="authorized").inc()

            self.structured_logger.log_event(
                event="stream_authorized",
                user_id=user_id,
                details={
                    "session_id": session_id,
                    "response_id": response_id,
                    "correlation_id": correlation_id,
                    "model": model,
                },
            )

            # Start stream processing with timeout enforcement
            async def generate_stream_with_timeout():
                try:
                    # First token timeout enforcement
                    first_token_task = asyncio.create_task(
                        self._process_stream_with_timeouts(
                            session_id,
                            user_id,
                            messages,
                            model,
                            temperature,
                            max_tokens,
                            response_id,
                            correlation_id,
                        )
                    )

                    # Wait for first token or timeout
                    try:
                        async for chunk in first_token_task:
                            yield chunk

                            # Update session state
                            await self._update_session_activity(session_id, chunk)

                            # Check for first token
                            if not session.first_token_sent and chunk.get("content"):
                                session.first_token_sent = True
                                await self._update_session_status(
                                    session_id, StreamAuthorityStatus.ACTIVE
                                )

                    except asyncio.TimeoutError:
                        await self._handle_first_token_timeout(
                            session_id, user_id, correlation_id
                        )
                        # Fallback will be handled by the timeout logic
                        raise

                except Exception as e:
                    await self._handle_stream_error(
                        session_id, user_id, str(e), correlation_id
                    )
                    raise

            return generate_stream_with_timeout()

        except Exception as e:
            await self._handle_authorization_error(
                session_id, user_id, str(e), correlation_id
            )
            raise

    async def _pre_authorize_session(self, user_id: str, session_id: str):
        """Pre-authorization checks before creating session"""
        # Check circuit breaker state
        if self._circuit_state == "open":
            raise Exception("Stream authority in circuit breaker state")

        # Check user rate limits
        await self._check_user_rate_limits(user_id)

        # Check concurrent stream limits
        await self._check_concurrent_streams(user_id)

    async def _check_user_rate_limits(self, user_id: str):
        """Check user rate limits"""
        async with self._rate_lock:
            now = datetime.utcnow()

            # Clean old entries
            cutoff = now - timedelta(minutes=1)
            if user_id in self._user_streams:
                self._user_streams[user_id] = [
                    timestamp
                    for timestamp in self._user_streams[user_id]
                    if timestamp > cutoff
                ]
            else:
                self._user_streams[user_id] = []

            # Check per-minute limit
            if len(self._user_streams[user_id]) >= self.config.streams_per_minute:
                raise Exception(f"User rate limit exceeded for {user_id}")

            # Check concurrent limit
            user_active_streams = sum(
                1
                for session in self._sessions.values()
                if session.user_id == user_id
                and session.status
                in [StreamAuthorityStatus.ACTIVE, StreamAuthorityStatus.DEGRADED]
            )

            if user_active_streams >= self.config.max_streams_per_user:
                raise Exception(f"Maximum concurrent streams reached for {user_id}")

    async def _check_concurrent_streams(self, user_id: str):
        """Check global concurrent stream limits"""
        active_streams = sum(
            1
            for session in self._sessions.values()
            if session.status
            in [StreamAuthorityStatus.ACTIVE, StreamAuthorityStatus.DEGRADED]
        )

        if active_streams >= self.config.max_concurrent_streams:
            raise Exception("Maximum concurrent streams reached")

    async def _process_stream_with_timeouts(
        self,
        session_id: str,
        user_id: str,
        messages: List[Dict[str, Any]],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_id: str,
        correlation_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process stream with timeout enforcement"""
        session = await self._get_session(session_id)
        if not session:
            raise Exception(f"Session {session_id} not found")

        try:
            # Set up timeout monitors
            stream_timeout_task = asyncio.create_task(
                asyncio.sleep(self.config.stream_timeout)
            )

            chunk_timeout_task = asyncio.create_task(
                asyncio.sleep(self.config.chunk_timeout)
            )

            # Process stream through enhanced stream processor
            if self.stream_processor:
                async for chunk in self.stream_processor.process_streaming_response(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    session_id=session_id,
                    user_id=user_id,
                    response_id=response_id,
                ):
                    # Reset chunk timeout on each chunk
                    chunk_timeout_task.cancel()
                    chunk_timeout_task = asyncio.create_task(
                        asyncio.sleep(self.config.chunk_timeout)
                    )

                    # Yield chunk
                    yield (
                        chunk.to_dict()
                        if hasattr(chunk, "to_dict")
                        else {
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                            "finished": chunk.finished,
                            "event_type": chunk.event_type,
                        }
                    )

                    # Check if stream should timeout
                    if stream_timeout_task.done():
                        raise asyncio.TimeoutError("Stream timeout exceeded")

                    if chunk_timeout_task.done():
                        raise asyncio.TimeoutError("Chunk timeout exceeded")

            # Stream completed successfully
            stream_timeout_task.cancel()
            chunk_timeout_task.cancel()

            # Ensure terminal event is emitted
            yield {
                "content": "",
                "metadata": {"event": "complete", "session_id": session_id},
                "finished": True,
                "event_type": "complete",
            }

            await self._update_session_status(session_id, StreamAuthorityStatus.ACTIVE)

        except asyncio.TimeoutError as e:
            await self._handle_timeout(session_id, user_id, str(e), correlation_id)
            # Fallback will be handled by the timeout logic
            raise
        except Exception as e:
            await self._handle_stream_error(session_id, user_id, str(e), correlation_id)
            raise

    async def _handle_first_token_timeout(
        self, session_id: str, user_id: str, correlation_id: str
    ):
        """Handle first token timeout"""
        session = await self._get_session(session_id)
        if session:
            session.timeout_count += 1
            session.status = StreamAuthorityStatus.DEGRADED

            self.structured_logger.log_event(
                event="stream_first_token_timeout",
                user_id=user_id,
                details={
                    "session_id": session_id,
                    "timeout_count": session.timeout_count,
                },
            )

            self.metrics_manager.register_counter(
                "stream_timeouts_total", ["type"]
            ).labels(type="first_token").inc()

            # Trigger fallback if enabled
            if (
                self.config.enable_fallback
                and session.timeout_count < self.config.max_fallback_attempts
            ):
                await self._trigger_fallback_response(
                    session_id, user_id, "first_token_timeout", correlation_id
                )

    async def _handle_timeout(
        self, session_id: str, user_id: str, error: str, correlation_id: str
    ):
        """Handle stream timeout"""
        session = await self._get_session(session_id)
        if session:
            session.timeout_count += 1
            session.status = StreamAuthorityStatus.DEGRADED

            self.structured_logger.log_event(
                event="stream_timeout",
                user_id=user_id,
                details={
                    "session_id": session_id,
                    "timeout_count": session.timeout_count,
                    "error": error,
                },
            )

            self.metrics_manager.register_counter(
                "stream_timeouts_total", ["type"]
            ).labels(type="stream").inc()

            # Trigger fallback if enabled
            if (
                self.config.enable_fallback
                and session.timeout_count < self.config.max_fallback_attempts
            ):
                await self._trigger_fallback_response(
                    session_id, user_id, "stream_timeout", correlation_id
                )

    async def _handle_stream_error(
        self, session_id: str, user_id: str, error: str, correlation_id: str
    ):
        """Handle stream processing error"""
        session = await self._get_session(session_id)
        if session:
            session.error_count += 1
            session.status = StreamAuthorityStatus.ERROR

            self.structured_logger.log_event(
                event="stream_error",
                user_id=user_id,
                details={
                    "session_id": session_id,
                    "error_count": session.error_count,
                    "error": error,
                },
            )

            self.metrics_manager.register_counter(
                "stream_errors_total", ["error_type"]
            ).labels(error_type="processing").inc()

            # Update circuit breaker state
            self._update_circuit_breaker_state(True)

    async def _handle_authorization_error(
        self, session_id: str, user_id: str, error: str, correlation_id: str
    ):
        """Handle authorization error"""
        self.structured_logger.log_event(
            event="stream_authorization_failed",
            user_id=user_id,
            details={
                "error": error,
                "correlation_id": correlation_id,
            },
        )

        self.metrics_manager.register_counter("stream_authorization_errors_total").inc()

    async def _trigger_fallback_response(
        self, session_id: str, user_id: str, reason: str, correlation_id: str
    ):
        """Trigger fallback response"""
        session = await self._get_session(session_id)
        if not session:
            return

        session.fallback_attempts += 1
        session.status = StreamAuthorityStatus.DEGRADED

        self.structured_logger.log_event(
            event="stream_fallback_triggered",
            user_id=user_id,
            details={
                "session_id": session_id,
                "fallback_attempts": session.fallback_attempts,
                "reason": reason,
            },
        )

        self.metrics_manager.register_counter(
            "stream_fallbacks_total", ["reason"]
        ).labels(reason=reason).inc()

        # Generate fallback response
        fallback_response = {
            "content": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
            "metadata": {
                "event": "fallback",
                "session_id": session_id,
                "reason": reason,
                "fallback_attempts": session.fallback_attempts,
                "formatted": False,
            },
            "finished": True,
            "event_type": "fallback",
        }

        # Emit fallback response
        yield fallback_response

        # Update session status
        await self._update_session_status(session_id, StreamAuthorityStatus.DEGRADED)

    async def _update_session_activity(self, session_id: str, chunk: Dict[str, Any]):
        """Update session activity based on chunk"""
        async with self._session_lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_activity = datetime.utcnow()
                session.last_chunk_time = datetime.utcnow()

                if chunk.get("content"):
                    session.first_token_sent = True

    async def _update_session_status(
        self, session_id: str, status: StreamAuthorityStatus
    ):
        """Update session status"""
        async with self._session_lock:
            if session_id in self._sessions:
                self._sessions[session_id].status = status
                self._sessions[session_id].last_activity = datetime.utcnow()

    async def _get_session(self, session_id: str) -> Optional[StreamAuthoritySession]:
        """Get session"""
        async with self._session_lock:
            return self._sessions.get(session_id)

    async def _update_circuit_breaker_state(self, failure: bool):
        """Update circuit breaker state based on failures"""
        now = datetime.utcnow()

        if failure:
            self._failure_count += 1
            self._last_failure_time = now

            if self._failure_count >= self.config.failure_threshold:
                self._circuit_state = "open"
                self.structured_logger.log_event(
                    event="stream_circuit_breaker_opened",
                    details={"failure_count": self._failure_count},
                )

                self.metrics_manager.register_counter(
                    "stream_circuit_breaker_openings_total"
                ).inc()
        else:
            self._failure_count = 0

            if self._circuit_state == "open":
                self._circuit_state = "half_open"
                self.structured_logger.log_event(
                    event="stream_circuit_breaker_half_open",
                    details={},
                )

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
                        if age > 3600 or session.status == StreamAuthorityStatus.ERROR:
                            expired_sessions.append(session_id)

                    # Remove expired sessions
                    for session_id in expired_sessions:
                        del self._sessions[session_id]

                    if expired_sessions:
                        self.structured_logger.log_event(
                            event="stream_sessions_cleaned",
                            details={
                                "expired_count": len(expired_sessions),
                                "remaining_sessions": len(self._sessions),
                            },
                        )

                # Clean up old rate limit entries
                async with self._rate_lock:
                    cutoff = now - timedelta(minutes=5)
                    for user_id in list(self._user_streams.keys()):
                        self._user_streams[user_id] = [
                            timestamp
                            for timestamp in self._user_streams[user_id]
                            if timestamp > cutoff
                        ]

                        if not self._user_streams[user_id]:
                            del self._user_streams[user_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _monitoring_loop(self):
        """Background monitoring loop for circuit breaker and health checks"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds

                # Check circuit breaker recovery
                if self._circuit_state == "open":
                    if self._last_failure_time:
                        recovery_time = (
                            datetime.utcnow() - self._last_failure_time
                        ).total_seconds()
                        if recovery_time >= self.config.recovery_timeout:
                            self._circuit_state = "half_open"
                            self.structured_logger.log_event(
                                event="stream_circuit_breaker_ready",
                                details={},
                            )

                # Perform health checks
                if self.stream_processor:
                    is_healthy = await self.stream_processor.health_check()
                    if not is_healthy:
                        self._update_circuit_breaker_state(True)

                # Record metrics
                await self._record_health_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _record_health_metrics(self):
        """Record health metrics"""
        try:
            active_sessions = sum(
                1
                for session in self._sessions.values()
                if session.status == StreamAuthorityStatus.ACTIVE
            )

            degraded_sessions = sum(
                1
                for session in self._sessions.values()
                if session.status == StreamAuthorityStatus.DEGRADED
            )

            self.metrics_manager.register_gauge("stream_authority_active_sessions").set(
                active_sessions
            )
            self.metrics_manager.register_gauge(
                "stream_authority_degraded_sessions"
            ).set(degraded_sessions)
            self.metrics_manager.register_gauge("stream_authority_circuit_state").set(
                1 if self._circuit_state == "open" else 0
            )

        except Exception as e:
            logger.error(f"Error recording health metrics: {e}")

    async def shutdown(self):
        """Shutdown the stream authority gracefully"""
        self._running = False

        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Shutdown stream processor
        if self.stream_processor:
            await self.stream_processor.shutdown()

        logger.info("StreamAuthority shutdown completed")

    async def health_check(self) -> bool:
        """Health check for the stream authority"""
        try:
            if not self._running:
                return False

            if not self.stream_processor:
                return False

            if not await self.stream_processor.health_check():
                return False

            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get stream authority metrics"""
        async with self._session_lock:
            active_sessions = sum(
                1
                for session in self._sessions.values()
                if session.status == StreamAuthorityStatus.ACTIVE
            )

            degraded_sessions = sum(
                1
                for session in self._sessions.values()
                if session.status == StreamAuthorityStatus.DEGRADED
            )

            error_sessions = sum(
                1
                for session in self._sessions.values()
                if session.status == StreamAuthorityStatus.ERROR
            )

        return {
            "active_sessions": active_sessions,
            "degraded_sessions": degraded_sessions,
            "error_sessions": error_sessions,
            "total_sessions": len(self._sessions),
            "circuit_state": self._circuit_state,
            "failure_count": self._failure_count,
            "running": self._running,
            "stream_processor_healthy": await self.stream_processor.health_check()
            if self.stream_processor
            else False,
        }


# Global stream authority instance
_stream_authority: Optional[StreamAuthority] = None


async def get_stream_authority() -> StreamAuthority:
    """Get global stream authority instance"""
    global _stream_authority
    if _stream_authority is None:
        _stream_authority = StreamAuthority()
        await _stream_authority.initialize()
    return _stream_authority
