"""
Progressive Response Streaming System

This module implements progressive response streaming with priority-based content ordering,
real-time feedback, and streaming error handling for optimal user experience.

Key Features:
- Priority-based content ordering and delivery
- Actionable items delivered first
- Coherent structure maintenance during streaming
- Real-time feedback system for users
- Streaming error handling and recovery
- Response chunking and buffering optimization
"""

import asyncio
import json
import logging
from typing import AsyncIterator, List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time
import uuid

from ...internal.content_optimization_engine import ContentSection, Priority, ContentType, FormatType

logger = logging.getLogger(__name__)


class StreamingState(Enum):
    """States of the streaming process"""
    INITIALIZING = "initializing"
    STREAMING = "streaming"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ChunkType(Enum):
    """Types of streaming chunks"""
    CONTENT = "content"
    METADATA = "metadata"
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETION = "completion"
    FEEDBACK_REQUEST = "feedback_request"


@dataclass
class StreamingChunk:
    """Individual chunk in the streaming response"""
    id: str
    chunk_type: ChunkType
    content: str
    priority: Priority
    sequence_number: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_actionable: bool = False
    requires_user_input: bool = False


@dataclass
class StreamingMetadata:
    """Metadata for streaming response"""
    total_sections: int
    estimated_duration: float
    content_types: List[ContentType]
    priority_distribution: Dict[Priority, int]
    streaming_strategy: str
    buffer_size: int
    chunk_size: int


@dataclass
class StreamingProgress:
    """Progress information for streaming response"""
    current_section: int
    total_sections: int
    bytes_streamed: int
    estimated_bytes_total: int
    elapsed_time: float
    estimated_remaining_time: float
    completion_percentage: float
    current_priority: Priority


@dataclass
class StreamingFeedback:
    """Real-time feedback during streaming"""
    message: str
    feedback_type: str  # "info", "warning", "error", "success"
    timestamp: datetime
    requires_acknowledgment: bool = False
    action_required: Optional[str] = None


class ProgressiveResponseStreamer:
    """
    Progressive response streaming system with priority-based content ordering
    and real-time user feedback.
    """
    
    def __init__(self, 
                 buffer_size: int = 8192,
                 chunk_size: int = 1024,
                 max_concurrent_streams: int = 10,
                 feedback_callback: Optional[Callable] = None):
        """
        Initialize the progressive response streamer.
        
        Args:
            buffer_size: Size of the streaming buffer in bytes
            chunk_size: Size of individual chunks in bytes
            max_concurrent_streams: Maximum number of concurrent streams
            feedback_callback: Optional callback for real-time feedback
        """
        self.buffer_size = buffer_size
        self.chunk_size = chunk_size
        self.max_concurrent_streams = max_concurrent_streams
        self.feedback_callback = feedback_callback
        
        self._active_streams: Dict[str, Dict[str, Any]] = {}
        self._stream_semaphore = asyncio.Semaphore(max_concurrent_streams)
        self._sequence_counter = 0
        
        logger.info(f"ProgressiveResponseStreamer initialized with buffer_size={buffer_size}, chunk_size={chunk_size}")
    
    async def stream_priority_content(self, 
                                    response_sections: List[ContentSection],
                                    stream_id: Optional[str] = None) -> AsyncIterator[StreamingChunk]:
        """
        Stream response content with priority-based ordering.
        
        Args:
            response_sections: List of content sections to stream
            stream_id: Optional stream identifier
            
        Yields:
            StreamingChunk: Individual chunks of the response
        """
        if not stream_id:
            stream_id = str(uuid.uuid4())
        
        async with self._stream_semaphore:
            try:
                # Initialize streaming state
                await self._initialize_stream(stream_id, response_sections)
                
                # Sort sections by priority and actionability
                prioritized_sections = await self._prioritize_sections(response_sections)
                
                # Create streaming metadata
                metadata = self._create_streaming_metadata(prioritized_sections)
                
                # Yield metadata chunk first
                metadata_dict = {
                    "total_sections": metadata.total_sections,
                    "estimated_duration": metadata.estimated_duration,
                    "content_types": [ct.value for ct in metadata.content_types],
                    "priority_distribution": {p.name: count for p, count in metadata.priority_distribution.items()},
                    "streaming_strategy": metadata.streaming_strategy,
                    "buffer_size": metadata.buffer_size,
                    "chunk_size": metadata.chunk_size
                }
                
                yield StreamingChunk(
                    id=f"{stream_id}_metadata",
                    chunk_type=ChunkType.METADATA,
                    content=json.dumps(metadata_dict),
                    priority=Priority.CRITICAL,
                    sequence_number=self._get_next_sequence(),
                    timestamp=datetime.now(),
                    metadata={"stream_id": stream_id}
                )
                
                # Stream sections in priority order
                async for chunk in self._stream_sections(stream_id, prioritized_sections):
                    yield chunk
                    
                # Yield completion chunk
                yield StreamingChunk(
                    id=f"{stream_id}_completion",
                    chunk_type=ChunkType.COMPLETION,
                    content="Stream completed successfully",
                    priority=Priority.CRITICAL,
                    sequence_number=self._get_next_sequence(),
                    timestamp=datetime.now(),
                    metadata={"stream_id": stream_id, "status": "completed"}
                )
                
            except Exception as e:
                logger.error(f"Error in stream_priority_content for stream {stream_id}: {e}")
                yield await self._create_error_chunk(stream_id, str(e))
            finally:
                await self._cleanup_stream(stream_id)
    
    async def deliver_actionable_items_first(self, 
                                           content_sections: List[ContentSection]) -> AsyncIterator[str]:
        """
        Deliver actionable items before explanatory content.
        
        Args:
            content_sections: List of content sections to process
            
        Yields:
            str: Content strings with actionable items first
        """
        try:
            # Separate actionable and non-actionable content
            actionable_sections = [s for s in content_sections if s.is_actionable]
            explanatory_sections = [s for s in content_sections if not s.is_actionable]
            
            # Sort actionable sections by priority
            actionable_sections.sort(key=lambda x: x.priority.value)
            
            # Deliver actionable content first
            for section in actionable_sections:
                formatted_content = await self._format_actionable_content(section)
                yield formatted_content
                
                # Provide feedback about actionable item delivery
                if self.feedback_callback:
                    feedback = StreamingFeedback(
                        message=f"Delivered actionable item: {section.content_type.value}",
                        feedback_type="info",
                        timestamp=datetime.now()
                    )
                    await self.feedback_callback(feedback)
            
            # Then deliver explanatory content
            explanatory_sections.sort(key=lambda x: x.priority.value)
            for section in explanatory_sections:
                formatted_content = await self._format_explanatory_content(section)
                yield formatted_content
                
        except Exception as e:
            logger.error(f"Error in deliver_actionable_items_first: {e}")
            yield f"Error processing content: {str(e)}"
    
    async def maintain_response_coherence(self, 
                                        stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """
        Maintain coherent structure during progressive delivery.
        
        Args:
            stream: Input stream of content
            
        Yields:
            str: Coherently structured content
        """
        try:
            buffer = []
            section_markers = []
            
            async for content in stream:
                buffer.append(content)
                
                # Check for natural break points
                if await self._is_natural_break_point(content):
                    # Process buffered content for coherence
                    coherent_content = await self._ensure_coherence(buffer)
                    
                    for item in coherent_content:
                        yield item
                    
                    buffer.clear()
                    section_markers.append(len(buffer))
            
            # Process any remaining buffered content
            if buffer:
                coherent_content = await self._ensure_coherence(buffer)
                for item in coherent_content:
                    yield item
                    
        except Exception as e:
            logger.error(f"Error in maintain_response_coherence: {e}")
            yield f"Error maintaining coherence: {str(e)}"
    
    async def provide_streaming_feedback(self, 
                                       stream_id: str, 
                                       progress: StreamingProgress) -> None:
        """
        Provide real-time feedback to users during response generation.
        
        Args:
            stream_id: Identifier for the stream
            progress: Current progress information
        """
        try:
            # Create feedback message based on progress
            feedback_message = await self._create_progress_message(progress)
            
            feedback = StreamingFeedback(
                message=feedback_message,
                feedback_type="info",
                timestamp=datetime.now(),
                requires_acknowledgment=False
            )
            
            # Update stream state
            if stream_id in self._active_streams:
                self._active_streams[stream_id]["progress"] = progress
                self._active_streams[stream_id]["last_feedback"] = feedback
            
            # Call feedback callback if provided
            if self.feedback_callback:
                await self.feedback_callback(feedback)
                
            logger.debug(f"Provided feedback for stream {stream_id}: {feedback_message}")
            
        except Exception as e:
            logger.error(f"Error providing streaming feedback for stream {stream_id}: {e}")
    
    async def handle_streaming_errors(self, 
                                    stream_id: str, 
                                    error: Exception) -> StreamingChunk:
        """
        Handle streaming errors and provide recovery mechanisms.
        
        Args:
            stream_id: Identifier for the stream
            error: The error that occurred
            
        Returns:
            StreamingChunk: Error chunk with recovery information
        """
        try:
            logger.error(f"Handling streaming error for stream {stream_id}: {error}")
            
            # Update stream state to error
            if stream_id in self._active_streams:
                self._active_streams[stream_id]["state"] = StreamingState.ERROR
                self._active_streams[stream_id]["error"] = str(error)
            
            # Determine recovery strategy
            recovery_strategy = await self._determine_recovery_strategy(error)
            
            # Create error chunk with recovery information
            error_chunk = StreamingChunk(
                id=f"{stream_id}_error",
                chunk_type=ChunkType.ERROR,
                content=f"Streaming error occurred: {str(error)}",
                priority=Priority.CRITICAL,
                sequence_number=self._get_next_sequence(),
                timestamp=datetime.now(),
                metadata={
                    "stream_id": stream_id,
                    "error_type": type(error).__name__,
                    "recovery_strategy": recovery_strategy,
                    "can_retry": True
                }
            )
            
            # Provide error feedback
            if self.feedback_callback:
                feedback = StreamingFeedback(
                    message=f"Streaming error: {str(error)}. Recovery strategy: {recovery_strategy}",
                    feedback_type="error",
                    timestamp=datetime.now(),
                    requires_acknowledgment=True,
                    action_required="retry_or_fallback"
                )
                await self.feedback_callback(feedback)
            
            return error_chunk
            
        except Exception as e:
            logger.error(f"Error in handle_streaming_errors: {e}")
            return await self._create_error_chunk(stream_id, f"Critical error: {str(e)}")
    
    async def optimize_response_chunking(self, 
                                       content: str, 
                                       target_chunk_size: Optional[int] = None) -> List[str]:
        """
        Implement response chunking and buffering for optimal streaming performance.
        
        Args:
            content: Content to chunk
            target_chunk_size: Target size for chunks (uses default if None)
            
        Returns:
            List[str]: Optimally chunked content
        """
        try:
            chunk_size = target_chunk_size or self.chunk_size
            
            # Smart chunking based on content structure
            chunks = []
            
            # Split by natural boundaries (sentences, paragraphs, code blocks)
            natural_chunks = await self._split_by_natural_boundaries(content)
            
            current_chunk = ""
            for natural_chunk in natural_chunks:
                # If adding this chunk would exceed size, finalize current chunk
                if len(current_chunk) + len(natural_chunk) > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = natural_chunk
                else:
                    current_chunk += natural_chunk
            
            # Add final chunk if not empty
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Optimize chunk boundaries
            optimized_chunks = await self._optimize_chunk_boundaries(chunks)
            
            logger.debug(f"Optimized content into {len(optimized_chunks)} chunks")
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"Error in optimize_response_chunking: {e}")
            return [content]  # Fallback to single chunk
    
    # Private helper methods
    
    async def _initialize_stream(self, stream_id: str, sections: List[ContentSection]) -> None:
        """Initialize streaming state for a new stream."""
        self._active_streams[stream_id] = {
            "state": StreamingState.INITIALIZING,
            "sections": sections,
            "start_time": time.time(),
            "progress": None,
            "error": None,
            "last_feedback": None
        }
        
        logger.debug(f"Initialized stream {stream_id} with {len(sections)} sections")
    
    async def _prioritize_sections(self, sections: List[ContentSection]) -> List[ContentSection]:
        """Sort sections by priority and actionability."""
        def priority_key(section: ContentSection) -> tuple:
            # Actionable items get higher priority
            actionable_boost = 0 if section.is_actionable else 10
            return (section.priority.value + actionable_boost, -section.relevance_score)
        
        return sorted(sections, key=priority_key)
    
    def _create_streaming_metadata(self, sections: List[ContentSection]) -> StreamingMetadata:
        """Create metadata for the streaming response."""
        content_types = list(set(s.content_type for s in sections))
        priority_dist = {}
        for priority in Priority:
            priority_dist[priority] = len([s for s in sections if s.priority == priority])
        
        estimated_duration = sum(s.estimated_read_time for s in sections) * 1.2  # Add buffer
        
        return StreamingMetadata(
            total_sections=len(sections),
            estimated_duration=estimated_duration,
            content_types=content_types,
            priority_distribution=priority_dist,
            streaming_strategy="priority_based",
            buffer_size=self.buffer_size,
            chunk_size=self.chunk_size
        )
    
    async def _stream_sections(self, 
                             stream_id: str, 
                             sections: List[ContentSection]) -> AsyncIterator[StreamingChunk]:
        """Stream individual sections as chunks."""
        total_sections = len(sections)
        
        for i, section in enumerate(sections):
            try:
                # Update progress
                progress = StreamingProgress(
                    current_section=i + 1,
                    total_sections=total_sections,
                    bytes_streamed=0,  # Would be calculated in real implementation
                    estimated_bytes_total=0,  # Would be calculated in real implementation
                    elapsed_time=time.time() - self._active_streams[stream_id]["start_time"],
                    estimated_remaining_time=0,  # Would be calculated
                    completion_percentage=(i / total_sections) * 100,
                    current_priority=section.priority
                )
                
                # Provide progress feedback
                await self.provide_streaming_feedback(stream_id, progress)
                
                # Create content chunk
                chunk = StreamingChunk(
                    id=f"{stream_id}_section_{i}",
                    chunk_type=ChunkType.CONTENT,
                    content=section.content,
                    priority=section.priority,
                    sequence_number=self._get_next_sequence(),
                    timestamp=datetime.now(),
                    metadata={
                        "stream_id": stream_id,
                        "section_index": i,
                        "content_type": section.content_type.value,
                        "format_type": section.format_type.value,
                        "is_actionable": section.is_actionable
                    },
                    is_actionable=section.is_actionable
                )
                
                yield chunk
                
                # Small delay to simulate realistic streaming
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error streaming section {i} for stream {stream_id}: {e}")
                yield await self._create_error_chunk(stream_id, f"Error in section {i}: {str(e)}")
    
    async def _format_actionable_content(self, section: ContentSection) -> str:
        """Format actionable content for immediate delivery."""
        if section.content_type == ContentType.CODE:
            return f"```\n{section.content}\n```\n\n"
        elif section.content_type == ContentType.LIST:
            return f"**Action Items:**\n{section.content}\n\n"
        else:
            return f"**🎯 Action Required:** {section.content}\n\n"
    
    async def _format_explanatory_content(self, section: ContentSection) -> str:
        """Format explanatory content."""
        if section.content_type == ContentType.TECHNICAL:
            return f"**Technical Details:**\n{section.content}\n\n"
        else:
            return f"{section.content}\n\n"
    
    async def _is_natural_break_point(self, content: str) -> bool:
        """Check if content represents a natural break point."""
        break_indicators = [
            "\n\n",  # Paragraph break
            "```\n",  # End of code block
            "---",    # Horizontal rule
            "## ",    # Section header
        ]
        return any(indicator in content for indicator in break_indicators)
    
    async def _ensure_coherence(self, buffer: List[str]) -> List[str]:
        """Ensure coherent structure in buffered content."""
        if not buffer:
            return []
        
        # Simple coherence check - ensure proper transitions
        coherent_content = []
        for i, content in enumerate(buffer):
            if i > 0 and not content.startswith((" ", "\t", "-", "*")):
                # Add transition if needed
                if not buffer[i-1].endswith(("\n", ".", ":", ";")):
                    coherent_content[-1] += "\n"
            
            coherent_content.append(content)
        
        return coherent_content
    
    async def _create_progress_message(self, progress: StreamingProgress) -> str:
        """Create a progress message for user feedback."""
        return (f"Processing section {progress.current_section}/{progress.total_sections} "
                f"({progress.completion_percentage:.1f}% complete)")
    
    async def _determine_recovery_strategy(self, error: Exception) -> str:
        """Determine the best recovery strategy for an error."""
        if isinstance(error, asyncio.TimeoutError):
            return "retry_with_timeout"
        elif isinstance(error, ConnectionError):
            return "reconnect_and_retry"
        elif isinstance(error, MemoryError):
            return "reduce_chunk_size"
        else:
            return "fallback_to_simple_delivery"
    
    async def _create_error_chunk(self, stream_id: str, error_message: str) -> StreamingChunk:
        """Create an error chunk."""
        return StreamingChunk(
            id=f"{stream_id}_error_{int(time.time())}",
            chunk_type=ChunkType.ERROR,
            content=error_message,
            priority=Priority.CRITICAL,
            sequence_number=self._get_next_sequence(),
            timestamp=datetime.now(),
            metadata={"stream_id": stream_id, "error": True}
        )
    
    async def _cleanup_stream(self, stream_id: str) -> None:
        """Clean up stream resources."""
        if stream_id in self._active_streams:
            self._active_streams[stream_id]["state"] = StreamingState.COMPLETED
            # Keep stream info for a short time for debugging
            await asyncio.sleep(60)  # Keep for 1 minute
            if stream_id in self._active_streams:
                del self._active_streams[stream_id]
    
    async def _split_by_natural_boundaries(self, content: str) -> List[str]:
        """Split content by natural boundaries."""
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                # Split long paragraphs by sentences
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                chunks.extend(sentences)
            else:
                chunks.append(paragraph)
        
        return [chunk + '\n\n' for chunk in chunks if chunk.strip()]
    
    async def _optimize_chunk_boundaries(self, chunks: List[str]) -> List[str]:
        """Optimize chunk boundaries for better readability."""
        optimized = []
        
        for chunk in chunks:
            # Ensure chunks don't end mid-sentence
            if chunk and not chunk.rstrip().endswith(('.', '!', '?', ':', ';', '\n')):
                # Try to find a better break point
                words = chunk.split()
                if len(words) > 1:
                    # Move last few words to next chunk if possible
                    better_end = ' '.join(words[:-2]) + '.'
                    optimized.append(better_end)
                else:
                    optimized.append(chunk)
            else:
                optimized.append(chunk)
        
        return optimized
    
    def _get_next_sequence(self) -> int:
        """Get next sequence number."""
        self._sequence_counter += 1
        return self._sequence_counter
    
    # Public utility methods
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active streams."""
        return self._active_streams.copy()
    
    async def cancel_stream(self, stream_id: str) -> bool:
        """Cancel an active stream."""
        if stream_id in self._active_streams:
            self._active_streams[stream_id]["state"] = StreamingState.CANCELLED
            logger.info(f"Cancelled stream {stream_id}")
            return True
        return False
    
    async def pause_stream(self, stream_id: str) -> bool:
        """Pause an active stream."""
        if stream_id in self._active_streams:
            self._active_streams[stream_id]["state"] = StreamingState.PAUSED
            logger.info(f"Paused stream {stream_id}")
            return True
        return False
    
    async def resume_stream(self, stream_id: str) -> bool:
        """Resume a paused stream."""
        if (stream_id in self._active_streams and 
            self._active_streams[stream_id]["state"] == StreamingState.PAUSED):
            self._active_streams[stream_id]["state"] = StreamingState.STREAMING
            logger.info(f"Resumed stream {stream_id}")
            return True
        return False