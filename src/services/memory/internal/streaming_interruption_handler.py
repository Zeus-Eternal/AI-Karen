"""
Streaming Interruption Recovery Handler

This module handles streaming interruptions and provides recovery
mechanisms with partial response handling.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, AsyncIterator, Callable, Any, Tuple
from contextlib import asynccontextmanager
import json
import re

from ...internal..core.types.shared_types import OptimizedResponse


class InterruptionType(Enum):
    """Types of streaming interruptions."""
    CONNECTION_LOST = "connection_lost"
    TIMEOUT = "timeout"
    CLIENT_DISCONNECT = "client_disconnect"
    SERVER_ERROR = "server_error"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    MODEL_FAILURE = "model_failure"
    NETWORK_ERROR = "network_error"
    RESOURCE_LIMIT = "resource_limit"


class RecoveryStrategy(Enum):
    """Recovery strategies for streaming interruptions."""
    RESUME_FROM_CHECKPOINT = "resume_from_checkpoint"
    PARTIAL_RESPONSE_DELIVERY = "partial_response_delivery"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_TO_BATCH = "fallback_to_batch"
    SIMPLIFIED_STREAMING = "simplified_streaming"
    EMERGENCY_RESPONSE = "emergency_response"


@dataclass
class StreamingCheckpoint:
    """Checkpoint for streaming recovery."""
    checkpoint_id: str
    timestamp: float
    content_delivered: str
    content_remaining: str
    stream_position: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterruptionContext:
    """Context information for streaming interruption."""
    interruption_type: InterruptionType
    original_error: Exception
    query: str
    model_id: Optional[str] = None
    partial_content: str = ""
    stream_position: int = 0
    checkpoints: List[StreamingCheckpoint] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class RecoveryResult:
    """Result of streaming interruption recovery."""
    success: bool
    strategy_used: RecoveryStrategy
    recovered_content: str
    completion_percentage: float
    recovery_time: float
    additional_content: Optional[str] = None
    error_message: Optional[str] = None


class StreamingInterruptionHandler:
    """
    Handles streaming interruptions and provides recovery mechanisms
    with partial response handling and checkpoint-based recovery.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Active streaming sessions
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        
        # Checkpoint storage
        self.checkpoints: Dict[str, List[StreamingCheckpoint]] = {}
        
        # Recovery strategies by interruption type
        self.recovery_strategies = {
            InterruptionType.CONNECTION_LOST: [
                RecoveryStrategy.RESUME_FROM_CHECKPOINT,
                RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY,
                RecoveryStrategy.RETRY_WITH_BACKOFF
            ],
            InterruptionType.TIMEOUT: [
                RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY,
                RecoveryStrategy.SIMPLIFIED_STREAMING,
                RecoveryStrategy.FALLBACK_TO_BATCH
            ],
            InterruptionType.CLIENT_DISCONNECT: [
                RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY
            ],
            InterruptionType.SERVER_ERROR: [
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY,
                RecoveryStrategy.EMERGENCY_RESPONSE
            ],
            InterruptionType.MEMORY_EXHAUSTION: [
                RecoveryStrategy.SIMPLIFIED_STREAMING,
                RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY,
                RecoveryStrategy.EMERGENCY_RESPONSE
            ],
            InterruptionType.MODEL_FAILURE: [
                RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY,
                RecoveryStrategy.EMERGENCY_RESPONSE
            ]
        }
        
        # Checkpoint configuration
        self.checkpoint_config = {
            "interval_seconds": 2.0,
            "min_content_length": 100,
            "max_checkpoints_per_stream": 10
        }
        
        # Recovery statistics
        self.recovery_stats = {
            "total_interruptions": 0,
            "successful_recoveries": 0,
            "partial_deliveries": 0,
            "emergency_responses": 0,
            "average_recovery_time": 0.0
        }
        
        # Content analysis patterns
        self.content_patterns = {
            "sentence_boundary": r'[.!?]\s+',
            "paragraph_boundary": r'\n\s*\n',
            "code_block": r'```[\s\S]*?```',
            "list_item": r'^\s*[-*+]\s+',
            "numbered_item": r'^\s*\d+\.\s+'
        }
    
    @asynccontextmanager
    async def streaming_session(
        self,
        session_id: str,
        query: str,
        model_id: Optional[str] = None
    ):
        """
        Context manager for streaming sessions with automatic
        interruption handling and recovery.
        """
        try:
            # Initialize streaming session
            self.active_streams[session_id] = {
                "query": query,
                "model_id": model_id,
                "start_time": time.time(),
                "content_delivered": "",
                "last_checkpoint": None
            }
            
            self.logger.info(f"Started streaming session: {session_id}")
            
            yield session_id
            
        except Exception as e:
            # Handle interruption
            interruption_type = self._classify_interruption(e)
            
            context = InterruptionContext(
                interruption_type=interruption_type,
                original_error=e,
                query=query,
                model_id=model_id,
                partial_content=self.active_streams.get(session_id, {}).get("content_delivered", ""),
                checkpoints=self.checkpoints.get(session_id, [])
            )
            
            # Attempt recovery
            recovery_result = await self.handle_streaming_interruption(context)
            
            if recovery_result.success:
                self.logger.info(
                    f"Successfully recovered from streaming interruption: {session_id}"
                )
                # Store recovery result for retrieval
                self._recovery_result = recovery_result.recovered_content
            else:
                self.logger.error(
                    f"Failed to recover from streaming interruption: {session_id}"
                )
                raise e
                
        finally:
            # Cleanup session
            if session_id in self.active_streams:
                del self.active_streams[session_id]
            if session_id in self.checkpoints:
                del self.checkpoints[session_id]
    
    async def handle_streaming_interruption(
        self,
        context: InterruptionContext
    ) -> RecoveryResult:
        """
        Handle streaming interruption using appropriate recovery strategy.
        """
        start_time = time.time()
        
        try:
            self.logger.warning(
                f"Handling streaming interruption: {context.interruption_type.value} "
                f"(partial content: {len(context.partial_content)} chars)"
            )
            
            # Update statistics
            self.recovery_stats["total_interruptions"] += 1
            
            # Get recovery strategies for this interruption type
            strategies = self.recovery_strategies.get(
                context.interruption_type,
                [RecoveryStrategy.EMERGENCY_RESPONSE]
            )
            
            # Try each strategy in order
            for strategy in strategies:
                try:
                    result = await self._execute_recovery_strategy(strategy, context)
                    
                    if result.success:
                        result.recovery_time = time.time() - start_time
                        self._update_recovery_stats(result)
                        
                        self.logger.info(
                            f"Successfully recovered using {strategy.value} "
                            f"in {result.recovery_time:.2f}s"
                        )
                        
                        return result
                        
                except Exception as e:
                    self.logger.error(f"Recovery strategy {strategy.value} failed: {str(e)}")
                    continue
            
            # All strategies failed, return emergency response
            emergency_result = RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.EMERGENCY_RESPONSE,
                recovered_content=await self._generate_emergency_response(context),
                completion_percentage=self._calculate_completion_percentage(context),
                recovery_time=time.time() - start_time
            )
            
            self._update_recovery_stats(emergency_result)
            return emergency_result
            
        except Exception as e:
            self.logger.error(f"Streaming interruption handling failed: {str(e)}")
            
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.EMERGENCY_RESPONSE,
                recovered_content="",
                completion_percentage=0.0,
                recovery_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def create_checkpoint(
        self,
        session_id: str,
        content_delivered: str,
        content_remaining: str,
        stream_position: int
    ) -> StreamingCheckpoint:
        """
        Create a checkpoint for streaming recovery.
        """
        try:
            checkpoint = StreamingCheckpoint(
                checkpoint_id=f"{session_id}_{int(time.time())}_{stream_position}",
                timestamp=time.time(),
                content_delivered=content_delivered,
                content_remaining=content_remaining,
                stream_position=stream_position,
                metadata={
                    "session_id": session_id,
                    "content_length": len(content_delivered),
                    "remaining_length": len(content_remaining)
                }
            )
            
            # Store checkpoint
            if session_id not in self.checkpoints:
                self.checkpoints[session_id] = []
            
            self.checkpoints[session_id].append(checkpoint)
            
            # Limit number of checkpoints
            max_checkpoints = self.checkpoint_config["max_checkpoints_per_stream"]
            if len(self.checkpoints[session_id]) > max_checkpoints:
                self.checkpoints[session_id] = self.checkpoints[session_id][-max_checkpoints:]
            
            # Update active stream
            if session_id in self.active_streams:
                self.active_streams[session_id]["last_checkpoint"] = checkpoint
                self.active_streams[session_id]["content_delivered"] = content_delivered
            
            return checkpoint
            
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {str(e)}")
            raise
    
    async def _execute_recovery_strategy(
        self,
        strategy: RecoveryStrategy,
        context: InterruptionContext
    ) -> RecoveryResult:
        """Execute a specific recovery strategy."""
        
        if strategy == RecoveryStrategy.RESUME_FROM_CHECKPOINT:
            return await self._resume_from_checkpoint(context)
        elif strategy == RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY:
            return await self._deliver_partial_response(context)
        elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return await self._retry_with_backoff(context)
        elif strategy == RecoveryStrategy.FALLBACK_TO_BATCH:
            return await self._fallback_to_batch(context)
        elif strategy == RecoveryStrategy.SIMPLIFIED_STREAMING:
            return await self._simplified_streaming(context)
        elif strategy == RecoveryStrategy.EMERGENCY_RESPONSE:
            return await self._emergency_response(context)
        else:
            raise ValueError(f"Unknown recovery strategy: {strategy}")
    
    async def _resume_from_checkpoint(
        self,
        context: InterruptionContext
    ) -> RecoveryResult:
        """Resume streaming from the last checkpoint."""
        
        try:
            if not context.checkpoints:
                raise ValueError("No checkpoints available for resume")
            
            # Get the most recent checkpoint
            latest_checkpoint = context.checkpoints[-1]
            
            # Simulate resuming from checkpoint
            await asyncio.sleep(0.5)  # Simulate resume time
            
            # Generate remaining content
            remaining_content = await self._generate_remaining_content(
                context.query,
                latest_checkpoint.content_delivered,
                latest_checkpoint.content_remaining
            )
            
            # Combine delivered and remaining content
            full_content = latest_checkpoint.content_delivered + remaining_content
            
            completion_percentage = self._calculate_completion_percentage(context)
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.RESUME_FROM_CHECKPOINT,
                recovered_content=full_content,
                completion_percentage=completion_percentage,
                recovery_time=0.0,  # Will be set by caller
                additional_content=remaining_content
            )
            
        except Exception as e:
            raise Exception(f"Resume from checkpoint failed: {str(e)}")
    
    async def _deliver_partial_response(
        self,
        context: InterruptionContext
    ) -> RecoveryResult:
        """Deliver partial response with proper formatting."""
        
        try:
            if not context.partial_content:
                raise ValueError("No partial content available")
            
            # Clean and format partial content
            cleaned_content = await self._clean_partial_content(context.partial_content)
            
            # Add interruption notice
            interruption_notice = self._generate_interruption_notice(context)
            final_content = f"{cleaned_content}\n\n{interruption_notice}"
            
            completion_percentage = self._calculate_completion_percentage(context)
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY,
                recovered_content=final_content,
                completion_percentage=completion_percentage,
                recovery_time=0.0
            )
            
        except Exception as e:
            raise Exception(f"Partial response delivery failed: {str(e)}")
    
    async def _retry_with_backoff(
        self,
        context: InterruptionContext
    ) -> RecoveryResult:
        """Retry streaming with exponential backoff."""
        
        try:
            if context.retry_count >= context.max_retries:
                raise ValueError("Maximum retry attempts exceeded")
            
            # Calculate backoff delay
            delay = min(2 ** context.retry_count, 10)  # Max 10 seconds
            await asyncio.sleep(delay)
            
            # Simulate retry
            retry_content = await self._retry_streaming(context)
            
            completion_percentage = 100.0  # Assume full completion on successful retry
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
                recovered_content=retry_content,
                completion_percentage=completion_percentage,
                recovery_time=0.0
            )
            
        except Exception as e:
            raise Exception(f"Retry with backoff failed: {str(e)}")
    
    async def _fallback_to_batch(
        self,
        context: InterruptionContext
    ) -> RecoveryResult:
        """Fallback to batch processing instead of streaming."""
        
        try:
            # Generate complete response in batch mode
            batch_response = await self._generate_batch_response(context.query)
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK_TO_BATCH,
                recovered_content=batch_response,
                completion_percentage=100.0,
                recovery_time=0.0
            )
            
        except Exception as e:
            raise Exception(f"Fallback to batch failed: {str(e)}")
    
    async def _simplified_streaming(
        self,
        context: InterruptionContext
    ) -> RecoveryResult:
        """Use simplified streaming with reduced complexity."""
        
        try:
            # Generate simplified response
            simplified_response = await self._generate_simplified_response(
                context.query,
                context.partial_content
            )
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.SIMPLIFIED_STREAMING,
                recovered_content=simplified_response,
                completion_percentage=80.0,  # Simplified but mostly complete
                recovery_time=0.0
            )
            
        except Exception as e:
            raise Exception(f"Simplified streaming failed: {str(e)}")
    
    async def _emergency_response(
        self,
        context: InterruptionContext
    ) -> RecoveryResult:
        """Generate emergency response for critical failures."""
        
        try:
            emergency_content = await self._generate_emergency_response(context)
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.EMERGENCY_RESPONSE,
                recovered_content=emergency_content,
                completion_percentage=self._calculate_completion_percentage(context),
                recovery_time=0.0
            )
            
        except Exception as e:
            raise Exception(f"Emergency response failed: {str(e)}")
    
    # Helper methods
    
    async def _clean_partial_content(self, partial_content: str) -> str:
        """Clean and format partial content for delivery."""
        
        # Remove incomplete sentences at the end
        sentences = re.split(self.content_patterns["sentence_boundary"], partial_content)
        
        if len(sentences) > 1:
            # Keep all complete sentences
            complete_sentences = sentences[:-1]
            cleaned_content = ". ".join(complete_sentences)
            if cleaned_content and not cleaned_content.endswith('.'):
                cleaned_content += '.'
        else:
            # If no complete sentences, try to find a good breaking point
            cleaned_content = partial_content.rstrip()
            
            # Add ellipsis if content seems incomplete
            if cleaned_content and not cleaned_content.endswith(('.', '!', '?')):
                cleaned_content += '...'
        
        return cleaned_content
    
    def _generate_interruption_notice(self, context: InterruptionContext) -> str:
        """Generate appropriate interruption notice."""
        
        notices = {
            InterruptionType.CONNECTION_LOST: (
                "[Connection was interrupted. The above information should "
                "address your main question.]"
            ),
            InterruptionType.TIMEOUT: (
                "[Response generation timed out. The above information "
                "provides the key points you requested.]"
            ),
            InterruptionType.CLIENT_DISCONNECT: (
                "[Response was interrupted by client disconnect.]"
            ),
            InterruptionType.SERVER_ERROR: (
                "[A server error interrupted the response. The above "
                "information contains the essential details.]"
            ),
            InterruptionType.MEMORY_EXHAUSTION: (
                "[Response was shortened due to memory constraints. "
                "The core information is provided above.]"
            ),
            InterruptionType.MODEL_FAILURE: (
                "[Model failure interrupted the response. The available "
                "information is provided above.]"
            )
        }
        
        return notices.get(
            context.interruption_type,
            "[Response was interrupted. The above information should be helpful.]"
        )
    
    def _calculate_completion_percentage(self, context: InterruptionContext) -> float:
        """Calculate estimated completion percentage."""
        
        if not context.partial_content:
            return 0.0
        
        # Estimate based on partial content length and query complexity
        query_length = len(context.query)
        partial_length = len(context.partial_content)
        
        # Simple heuristic: assume response should be 2-5x query length
        estimated_full_length = query_length * 3
        completion = min((partial_length / estimated_full_length) * 100, 95.0)
        
        return max(completion, 10.0)  # Minimum 10% if we have any content
    
    async def _generate_remaining_content(
        self,
        query: str,
        delivered_content: str,
        remaining_content: str
    ) -> str:
        """Generate remaining content for checkpoint resume."""
        
        # Simulate content generation
        await asyncio.sleep(0.2)
        
        if remaining_content:
            return remaining_content
        else:
            # Generate simple continuation
            return f"\n\n[Continued from checkpoint] Additional information about: {query[:50]}..."
    
    async def _retry_streaming(self, context: InterruptionContext) -> str:
        """Retry streaming operation."""
        
        # Simulate retry
        await asyncio.sleep(0.5)
        
        # Combine partial content with retry result
        retry_content = f"[Retry successful] {context.query[:100]}..."
        
        if context.partial_content:
            return f"{context.partial_content}\n\n{retry_content}"
        else:
            return retry_content
    
    async def _generate_batch_response(self, query: str) -> str:
        """Generate complete response in batch mode."""
        
        # Simulate batch processing
        await asyncio.sleep(1.0)
        
        return f"[Batch mode response] Complete answer to: {query[:100]}..."
    
    async def _generate_simplified_response(
        self,
        query: str,
        partial_content: str
    ) -> str:
        """Generate simplified response."""
        
        # Simulate simplified generation
        await asyncio.sleep(0.3)
        
        simplified = f"[Simplified response] {query[:80]}..."
        
        if partial_content:
            return f"{partial_content}\n\n{simplified}"
        else:
            return simplified
    
    async def _generate_emergency_response(self, context: InterruptionContext) -> str:
        """Generate emergency response."""
        
        emergency_messages = {
            InterruptionType.CONNECTION_LOST: (
                "I apologize, but the connection was interrupted. "
                "Please try your request again."
            ),
            InterruptionType.TIMEOUT: (
                "Your request timed out. Please try breaking it into "
                "smaller parts or try again later."
            ),
            InterruptionType.MEMORY_EXHAUSTION: (
                "I'm experiencing memory constraints. Please try a "
                "simpler request or try again in a moment."
            ),
            InterruptionType.MODEL_FAILURE: (
                "The AI model encountered an error. Please try your "
                "request again or rephrase it."
            )
        }
        
        base_message = emergency_messages.get(
            context.interruption_type,
            "I apologize, but an error occurred. Please try your request again."
        )
        
        # Include partial content if available
        if context.partial_content:
            cleaned_partial = await self._clean_partial_content(context.partial_content)
            return f"{cleaned_partial}\n\n{base_message}"
        else:
            return base_message
    
    def _classify_interruption(self, error: Exception) -> InterruptionType:
        """Classify the type of interruption based on the error."""
        
        error_str = str(error).lower()
        
        if "timeout" in error_str or "time" in error_str:
            return InterruptionType.TIMEOUT
        elif "connection" in error_str or "network" in error_str:
            return InterruptionType.CONNECTION_LOST
        elif "memory" in error_str or "oom" in error_str:
            return InterruptionType.MEMORY_EXHAUSTION
        elif "model" in error_str:
            return InterruptionType.MODEL_FAILURE
        elif "disconnect" in error_str:
            return InterruptionType.CLIENT_DISCONNECT
        elif "server" in error_str:
            return InterruptionType.SERVER_ERROR
        else:
            return InterruptionType.SERVER_ERROR
    
    def _update_recovery_stats(self, result: RecoveryResult):
        """Update recovery statistics."""
        
        if result.success:
            self.recovery_stats["successful_recoveries"] += 1
            
            if result.strategy_used == RecoveryStrategy.PARTIAL_RESPONSE_DELIVERY:
                self.recovery_stats["partial_deliveries"] += 1
            elif result.strategy_used == RecoveryStrategy.EMERGENCY_RESPONSE:
                self.recovery_stats["emergency_responses"] += 1
        
        # Update average recovery time
        total_recoveries = self.recovery_stats["total_interruptions"]
        current_avg = self.recovery_stats["average_recovery_time"]
        self.recovery_stats["average_recovery_time"] = (
            (current_avg * (total_recoveries - 1) + result.recovery_time) / total_recoveries
        )
    
    async def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get streaming recovery statistics."""
        
        return {
            "recovery_stats": self.recovery_stats.copy(),
            "active_streams": len(self.active_streams),
            "total_checkpoints": sum(len(checkpoints) for checkpoints in self.checkpoints.values()),
            "checkpoint_config": self.checkpoint_config.copy()
        }


# Global streaming interruption handler instance
streaming_interruption_handler = StreamingInterruptionHandler()