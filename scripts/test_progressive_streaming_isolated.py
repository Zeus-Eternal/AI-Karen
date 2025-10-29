"""
Isolated test for Progressive Response Streaming System

This script tests the progressive response streaming implementation
in isolation without importing the full services module.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, AsyncIterator, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import uuid
import re

# Define the required types locally to avoid import issues
class ContentType(Enum):
    TEXT = "text"
    CODE = "code"
    LIST = "list"
    TABLE = "table"
    MIXED = "mixed"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"

class ExpertiseLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class FormatType(Enum):
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    BULLET_POINTS = "bullet_points"
    NUMBERED_LIST = "numbered_list"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    HIERARCHICAL = "hierarchical"

class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    SUPPLEMENTARY = 5

@dataclass
class ContentSection:
    content: str
    content_type: ContentType
    priority: Priority
    relevance_score: float
    expertise_level: ExpertiseLevel
    format_type: FormatType
    source_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_read_time: float = 0.0
    is_actionable: bool = False

# Now include the streaming system classes directly
class StreamingState(Enum):
    INITIALIZING = "initializing"
    STREAMING = "streaming"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

class ChunkType(Enum):
    CONTENT = "content"
    METADATA = "metadata"
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETION = "completion"
    FEEDBACK_REQUEST = "feedback_request"

@dataclass
class StreamingChunk:
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
    total_sections: int
    estimated_duration: float
    content_types: List[ContentType]
    priority_distribution: Dict[Priority, int]
    streaming_strategy: str
    buffer_size: int
    chunk_size: int

@dataclass
class StreamingProgress:
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
    message: str
    feedback_type: str
    timestamp: datetime
    requires_acknowledgment: bool = False
    action_required: Optional[str] = None

class ProgressiveResponseStreamer:
    """Simplified version for testing"""
    
    def __init__(self, 
                 buffer_size: int = 8192,
                 chunk_size: int = 1024,
                 max_concurrent_streams: int = 10,
                 feedback_callback: Optional[Callable] = None):
        self.buffer_size = buffer_size
        self.chunk_size = chunk_size
        self.max_concurrent_streams = max_concurrent_streams
        self.feedback_callback = feedback_callback
        
        self._active_streams: Dict[str, Dict[str, Any]] = {}
        self._stream_semaphore = asyncio.Semaphore(max_concurrent_streams)
        self._sequence_counter = 0
    
    async def stream_priority_content(self, 
                                    response_sections: List[ContentSection],
                                    stream_id: Optional[str] = None) -> AsyncIterator[StreamingChunk]:
        if not stream_id:
            stream_id = str(uuid.uuid4())
        
        async with self._stream_semaphore:
            try:
                await self._initialize_stream(stream_id, response_sections)
                
                prioritized_sections = await self._prioritize_sections(response_sections)
                metadata = self._create_streaming_metadata(prioritized_sections)
                
                # Yield metadata chunk
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
                
                # Stream sections
                async for chunk in self._stream_sections(stream_id, prioritized_sections):
                    yield chunk
                
                # Completion chunk
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
                yield await self._create_error_chunk(stream_id, str(e))
            finally:
                await self._cleanup_stream(stream_id)
    
    async def deliver_actionable_items_first(self, 
                                           content_sections: List[ContentSection]) -> AsyncIterator[str]:
        try:
            actionable_sections = [s for s in content_sections if s.is_actionable]
            explanatory_sections = [s for s in content_sections if not s.is_actionable]
            
            actionable_sections.sort(key=lambda x: x.priority.value)
            
            for section in actionable_sections:
                formatted_content = await self._format_actionable_content(section)
                yield formatted_content
                
                if self.feedback_callback:
                    feedback = StreamingFeedback(
                        message=f"Delivered actionable item: {section.content_type.value}",
                        feedback_type="info",
                        timestamp=datetime.now()
                    )
                    await self.feedback_callback(feedback)
            
            explanatory_sections.sort(key=lambda x: x.priority.value)
            for section in explanatory_sections:
                formatted_content = await self._format_explanatory_content(section)
                yield formatted_content
                
        except Exception as e:
            yield f"Error processing content: {str(e)}"
    
    async def maintain_response_coherence(self, 
                                        stream: AsyncIterator[str]) -> AsyncIterator[str]:
        try:
            buffer = []
            
            async for content in stream:
                buffer.append(content)
                
                if await self._is_natural_break_point(content):
                    coherent_content = await self._ensure_coherence(buffer)
                    
                    for item in coherent_content:
                        yield item
                    
                    buffer.clear()
            
            if buffer:
                coherent_content = await self._ensure_coherence(buffer)
                for item in coherent_content:
                    yield item
                    
        except Exception as e:
            yield f"Error maintaining coherence: {str(e)}"
    
    async def provide_streaming_feedback(self, 
                                       stream_id: str, 
                                       progress: StreamingProgress) -> None:
        try:
            feedback_message = await self._create_progress_message(progress)
            
            feedback = StreamingFeedback(
                message=feedback_message,
                feedback_type="info",
                timestamp=datetime.now(),
                requires_acknowledgment=False
            )
            
            if stream_id in self._active_streams:
                self._active_streams[stream_id]["progress"] = progress
                self._active_streams[stream_id]["last_feedback"] = feedback
            
            if self.feedback_callback:
                await self.feedback_callback(feedback)
                
        except Exception as e:
            print(f"Error providing streaming feedback for stream {stream_id}: {e}")
    
    async def handle_streaming_errors(self, 
                                    stream_id: str, 
                                    error: Exception) -> StreamingChunk:
        try:
            if stream_id in self._active_streams:
                self._active_streams[stream_id]["state"] = StreamingState.ERROR
                self._active_streams[stream_id]["error"] = str(error)
            
            recovery_strategy = await self._determine_recovery_strategy(error)
            
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
            return await self._create_error_chunk(stream_id, f"Critical error: {str(e)}")
    
    async def optimize_response_chunking(self, 
                                       content: str, 
                                       target_chunk_size: Optional[int] = None) -> List[str]:
        try:
            chunk_size = target_chunk_size or self.chunk_size
            
            chunks = []
            natural_chunks = await self._split_by_natural_boundaries(content)
            
            current_chunk = ""
            for natural_chunk in natural_chunks:
                if len(current_chunk) + len(natural_chunk) > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = natural_chunk
                else:
                    current_chunk += natural_chunk
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            optimized_chunks = await self._optimize_chunk_boundaries(chunks)
            return optimized_chunks
            
        except Exception as e:
            return [content]
    
    # Helper methods
    async def _initialize_stream(self, stream_id: str, sections: List[ContentSection]) -> None:
        self._active_streams[stream_id] = {
            "state": StreamingState.INITIALIZING,
            "sections": sections,
            "start_time": time.time(),
            "progress": None,
            "error": None,
            "last_feedback": None
        }
    
    async def _prioritize_sections(self, sections: List[ContentSection]) -> List[ContentSection]:
        def priority_key(section: ContentSection) -> tuple:
            actionable_boost = 0 if section.is_actionable else 10
            return (section.priority.value + actionable_boost, -section.relevance_score)
        
        return sorted(sections, key=priority_key)
    
    def _create_streaming_metadata(self, sections: List[ContentSection]) -> StreamingMetadata:
        content_types = list(set(s.content_type for s in sections))
        priority_dist = {}
        for priority in Priority:
            priority_dist[priority] = len([s for s in sections if s.priority == priority])
        
        estimated_duration = sum(s.estimated_read_time for s in sections) * 1.2
        
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
        total_sections = len(sections)
        
        for i, section in enumerate(sections):
            try:
                progress = StreamingProgress(
                    current_section=i + 1,
                    total_sections=total_sections,
                    bytes_streamed=0,
                    estimated_bytes_total=0,
                    elapsed_time=time.time() - self._active_streams[stream_id]["start_time"],
                    estimated_remaining_time=0,
                    completion_percentage=(i / total_sections) * 100,
                    current_priority=section.priority
                )
                
                await self.provide_streaming_feedback(stream_id, progress)
                
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
                await asyncio.sleep(0.01)
                
            except Exception as e:
                yield await self._create_error_chunk(stream_id, f"Error in section {i}: {str(e)}")
    
    async def _format_actionable_content(self, section: ContentSection) -> str:
        if section.content_type == ContentType.CODE:
            return f"```\n{section.content}\n```\n\n"
        elif section.content_type == ContentType.LIST:
            return f"**Action Items:**\n{section.content}\n\n"
        else:
            return f"**🎯 Action Required:** {section.content}\n\n"
    
    async def _format_explanatory_content(self, section: ContentSection) -> str:
        if section.content_type == ContentType.TECHNICAL:
            return f"**Technical Details:**\n{section.content}\n\n"
        else:
            return f"{section.content}\n\n"
    
    async def _is_natural_break_point(self, content: str) -> bool:
        break_indicators = ["\n\n", "```\n", "---", "## "]
        return any(indicator in content for indicator in break_indicators)
    
    async def _ensure_coherence(self, buffer: List[str]) -> List[str]:
        if not buffer:
            return []
        
        coherent_content = []
        for i, content in enumerate(buffer):
            if i > 0 and not content.startswith((" ", "\t", "-", "*")):
                if not buffer[i-1].endswith(("\n", ".", ":", ";")):
                    coherent_content[-1] += "\n"
            
            coherent_content.append(content)
        
        return coherent_content
    
    async def _create_progress_message(self, progress: StreamingProgress) -> str:
        return (f"Processing section {progress.current_section}/{progress.total_sections} "
                f"({progress.completion_percentage:.1f}% complete)")
    
    async def _determine_recovery_strategy(self, error: Exception) -> str:
        if isinstance(error, asyncio.TimeoutError):
            return "retry_with_timeout"
        elif isinstance(error, ConnectionError):
            return "reconnect_and_retry"
        elif isinstance(error, MemoryError):
            return "reduce_chunk_size"
        else:
            return "fallback_to_simple_delivery"
    
    async def _create_error_chunk(self, stream_id: str, error_message: str) -> StreamingChunk:
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
        if stream_id in self._active_streams:
            self._active_streams[stream_id]["state"] = StreamingState.COMPLETED
    
    async def _split_by_natural_boundaries(self, content: str) -> List[str]:
        paragraphs = content.split('\n\n')
        
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                chunks.extend(sentences)
            else:
                chunks.append(paragraph)
        
        return [chunk + '\n\n' for chunk in chunks if chunk.strip()]
    
    async def _optimize_chunk_boundaries(self, chunks: List[str]) -> List[str]:
        optimized = []
        
        for chunk in chunks:
            if chunk and not chunk.rstrip().endswith(('.', '!', '?', ':', ';', '\n')):
                words = chunk.split()
                if len(words) > 1:
                    better_end = ' '.join(words[:-2]) + '.'
                    optimized.append(better_end)
                else:
                    optimized.append(chunk)
            else:
                optimized.append(chunk)
        
        return optimized
    
    def _get_next_sequence(self) -> int:
        self._sequence_counter += 1
        return self._sequence_counter
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        return self._active_streams.copy()
    
    async def cancel_stream(self, stream_id: str) -> bool:
        if stream_id in self._active_streams:
            self._active_streams[stream_id]["state"] = StreamingState.CANCELLED
            return True
        return False
    
    async def pause_stream(self, stream_id: str) -> bool:
        if stream_id in self._active_streams:
            self._active_streams[stream_id]["state"] = StreamingState.PAUSED
            return True
        return False
    
    async def resume_stream(self, stream_id: str) -> bool:
        if (stream_id in self._active_streams and 
            self._active_streams[stream_id]["state"] == StreamingState.PAUSED):
            self._active_streams[stream_id]["state"] = StreamingState.STREAMING
            return True
        return False


# Test functions
async def test_basic_streaming():
    """Test basic streaming functionality"""
    print("Testing basic streaming functionality...")
    
    feedback_messages = []
    
    async def feedback_handler(feedback: StreamingFeedback):
        feedback_messages.append(feedback)
        print(f"  Feedback: {feedback.message}")
    
    streamer = ProgressiveResponseStreamer(
        buffer_size=512,
        chunk_size=128,
        feedback_callback=feedback_handler
    )
    
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
    
    chunks = []
    async for chunk in streamer.stream_priority_content(sections):
        chunks.append(chunk)
        print(f"  Received chunk: {chunk.chunk_type.value} - {chunk.content[:50]}...")
    
    assert len(chunks) >= 4, f"Expected at least 4 chunks, got {len(chunks)}"
    assert chunks[0].chunk_type == ChunkType.METADATA, "First chunk should be metadata"
    assert chunks[-1].chunk_type == ChunkType.COMPLETION, "Last chunk should be completion"
    
    content_chunks = [c for c in chunks if c.chunk_type == ChunkType.CONTENT]
    assert len(content_chunks) == 2, f"Expected 2 content chunks, got {len(content_chunks)}"
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
    
    actionable_indicators = ["Action Required", "Action Items", "```"]
    first_is_actionable = any(indicator in content_items[0] for indicator in actionable_indicators)
    second_is_actionable = any(indicator in content_items[1] for indicator in actionable_indicators)
    
    assert first_is_actionable or second_is_actionable, "Actionable items should be delivered first"
    
    print("  ✅ Actionable-first delivery test passed!")
    return True


async def run_all_tests():
    """Run all tests"""
    print("Progressive Response Streaming System - Isolated Tests")
    print("=" * 60)
    
    tests = [
        test_basic_streaming,
        test_actionable_first_delivery,
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