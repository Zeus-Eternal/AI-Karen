"""
Stream Processing Node

Implements centralized streaming authority with interruption rules and degraded mode support.
Ensures consistent streaming behavior across all execution paths.
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from ..contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)


class StreamStatus(str, Enum):
    """Streaming status"""

    ACTIVE = "active"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class StreamAuthorityConfig:
    """Configuration for streaming authority"""

    enable_interruption: bool = True
    enable_degraded_mode_rules: bool = True
    max_concurrent_streams: int = 10
    stream_timeout_ms: int = 30000
    enable_backpressure: bool = True


@dataclass
class StreamChunk:
    """Standardized stream chunk"""

    content: str
    chunk_type: str = "text"  # text, tool_result, metadata
    timestamp: str = None
    sequence: int = 0
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            from datetime import datetime, timezone

            self.timestamp = datetime.now(timezone.utc).isoformat()


class StreamAuthority:
    """Centralized streaming authority"""

    def __init__(self, config: Optional[StreamAuthorityConfig] = None):
        self.config = config or StreamAuthorityConfig()
        self.active_streams: Dict[str, StreamStatus] = {}
        self.stream_counters: Dict[str, int] = {}

    async def check_stream_authority(
        self, state: LangGraphOrchestrationState, stream_id: str
    ) -> bool:
        """Check if streaming is allowed"""

        # Check degraded mode rules
        if self.config.enable_degraded_mode_rules:
            degraded_level = state.get("runtime_level", "FULL")
            if degraded_level in ["EMERGENCY", "SAFE"]:
                logger.warning(f"Streaming disabled in {degraded_level} mode")
                return False

        # Check concurrent stream limit
        if len(self.active_streams) >= self.config.max_concurrent_streams:
            logger.warning(
                f"Max concurrent streams ({self.config.max_concurrent_streams}) reached"
            )
            return False

        # Check if stream already exists
        if stream_id in self.active_streams:
            if self.active_streams[stream_id] == StreamStatus.ACTIVE:
                logger.warning(f"Stream {stream_id} already active")
                return False

        # Authority check passed
        self.active_streams[stream_id] = StreamStatus.ACTIVE
        self.stream_counters[stream_id] = 0
        return True

    async def handle_interruption(
        self, stream_id: str, interruption_reason: str
    ) -> bool:
        """Handle stream interruption"""

        if not self.config.enable_interruption:
            return False

        if stream_id in self.active_streams:
            self.active_streams[stream_id] = StreamStatus.INTERRUPTED
            logger.info(f"Stream {stream_id} interrupted: {interruption_reason}")
            return True

        return False

    async def complete_stream(self, stream_id: str):
        """Mark stream as completed"""

        if stream_id in self.active_streams:
            self.active_streams[stream_id] = StreamStatus.COMPLETED
            logger.info(f"Stream {stream_id} completed")

    async def error_stream(self, stream_id: str, error_message: str):
        """Mark stream as errored"""

        if stream_id in self.active_streams:
            self.active_streams[stream_id] = StreamStatus.ERROR
            logger.error(f"Stream {stream_id} error: {error_message}")

    def get_stream_status(self, stream_id: str) -> Optional[StreamStatus]:
        """Get current stream status"""
        return self.active_streams.get(stream_id)

    def get_active_streams(self) -> Dict[str, StreamStatus]:
        """Get all active streams"""
        return {
            k: v for k, v in self.active_streams.items() if v == StreamStatus.ACTIVE
        }


class StreamProcessor:
    """Handles stream processing with interruption rules"""

    def __init__(self, authority: StreamAuthority):
        self.authority = authority

    async def process_stream_chunks(
        self, state: LangGraphOrchestrationState, chunks: AsyncGenerator[str, None]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Process stream chunks with interruption rules"""

        stream_id = state.get("stream_id", f"stream_{id(state)}")

        # Check streaming authority
        if not await self.authority.check_stream_authority(state, stream_id):
            yield StreamChunk(
                content="Streaming not available at this time",
                chunk_type="metadata",
                metadata={"reason": "authority_check_failed"},
            )
            return

        try:
            async for chunk in chunks:
                # Check for interruption
                if await self._should_interrupt(state, stream_id):
                    yield StreamChunk(
                        content="Stream interrupted",
                        chunk_type="metadata",
                        metadata={"reason": "interruption_detected"},
                    )
                    await self.authority.handle_interruption(
                        stream_id, "user_interruption"
                    )
                    return

                # Create standardized chunk
                stream_chunk = StreamChunk(
                    content=chunk,
                    chunk_type="text",
                    metadata={
                        "stream_id": stream_id,
                        "sequence": self.authority.stream_counters[stream_id],
                    },
                )

                self.authority.stream_counters[stream_id] += 1
                yield stream_chunk

        except Exception as e:
            await self.authority.error_stream(stream_id, str(e))
            yield StreamChunk(
                content=f"Stream error: {str(e)}",
                chunk_type="metadata",
                metadata={"error": str(e)},
            )
        finally:
            await self.authority.complete_stream(stream_id)

    async def _should_interrupt(
        self, state: LangGraphOrchestrationState, stream_id: str
    ) -> bool:
        """Check if stream should be interrupted"""

        # Check for user interruption signal
        if state.get("interrupt_requested", False):
            return True

        # Check for degraded mode changes
        degraded_level = state.get("runtime_level", "FULL")
        if degraded_level in ["EMERGENCY", "SAFE"]:
            return True

        # Check for critical errors
        if state.get("errors") and any(
            "critical" in error.lower() for error in state.get("errors", [])
        ):
            return True

        return False


class StreamIntegration:
    """Integrates streaming with LangGraph orchestration"""

    def __init__(self, config: Optional[StreamAuthorityConfig] = None):
        self.authority = StreamAuthority(config)
        self.processor = StreamProcessor(self.authority)

    async def process_response_stream(
        self,
        state: LangGraphOrchestrationState,
        response_stream: AsyncGenerator[str, None],
    ) -> AsyncGenerator[StreamChunk, None]:
        """Process response stream with centralized authority"""

        logger.info("Processing response stream with centralized authority")

        # Apply streaming constraints
        state = self._apply_streaming_constraints(state)

        # Process chunks
        async for chunk in self.processor.process_stream_chunks(state, response_stream):
            yield chunk

    def _apply_streaming_constraints(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """Apply streaming constraints based on runtime state"""

        # Check degraded mode
        degraded_level = state.get("runtime_level", "FULL")
        if degraded_level in ["EMERGENCY", "SAFE"]:
            state["streaming_enabled"] = False
            state["stream_chunk_size"] = 100  # Smaller chunks in degraded mode
        else:
            state["streaming_enabled"] = True
            state["stream_chunk_size"] = 500  # Normal chunk size

        # Apply backpressure
        if self.authority.config.enable_backpressure:
            active_streams = len(self.authority.get_active_streams())
            if active_streams > 5:  # High load
                state["stream_delay_ms"] = 100  # Add delay
            else:
                state["stream_delay_ms"] = 0

        return state


async def stream_process_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """
    Stream processing node for LangGraph orchestration

    Handles centralized streaming authority with interruption rules
    """
    logger.info("Stream processing node")

    try:
        # Initialize stream integration
        stream_integration = StreamIntegration()

        # Apply streaming constraints
        state = stream_integration._apply_streaming_constraints(state)

        # Store stream authority status in state
        state["stream_authority"] = {
            "active_streams": len(stream_integration.authority.get_active_streams()),
            "max_concurrent_streams": stream_integration.authority.config.max_concurrent_streams,
            "streaming_enabled": state.get("streaming_enabled", False),
        }

        logger.info("Stream processing completed")

    except Exception as e:
        logger.error(f"Stream processing error: {e}")
        state.setdefault("errors", []).append(f"Stream processing error: {str(e)}")

    return state


# Helper function for streaming integration
async def create_stream_chunk(
    content: str, chunk_type: str = "text", metadata: Optional[Dict[str, Any]] = None
) -> StreamChunk:
    """Create a standardized stream chunk"""
    return StreamChunk(content=content, chunk_type=chunk_type, metadata=metadata or {})
