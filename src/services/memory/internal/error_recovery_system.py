"""
Comprehensive Error Recovery System for Intelligent Response Optimization

This module provides comprehensive error handling and graceful degradation
capabilities for the response optimization system, ensuring robust operation
even when models fail or resources are constrained.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, AsyncIterator, Union
from contextlib import asynccontextmanager
import psutil
import traceback

from ...internal..core.types.shared_types import (
    ModelInfo, Modality, ModalityType, ModelStatus, 
    ResponseStrategy, OptimizedResponse, PerformanceMetrics
)


class ErrorType(Enum):
    """Types of errors that can occur in the response system."""
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_TIMEOUT = "model_timeout"
    ROUTING_ERROR = "routing_error"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    STREAMING_INTERRUPTION = "streaming_interruption"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_CONSTRAINT = "resource_constraint"
    CONNECTION_FAILURE = "connection_failure"
    REASONING_FAILURE = "reasoning_failure"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    FALLBACK_MODEL = "fallback_model"
    REDUCE_COMPLEXITY = "reduce_complexity"
    CACHE_FALLBACK = "cache_fallback"
    PARTIAL_RESPONSE = "partial_response"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    EMERGENCY_RESPONSE = "emergency_response"


@dataclass
class ErrorContext:
    """Context information for error recovery."""
    error_type: ErrorType
    original_error: Exception
    query: str
    model_id: Optional[str] = None
    modalities: List[Modality] = field(default_factory=list)
    attempt_count: int = 0
    max_attempts: int = 3
    timestamp: float = field(default_factory=time.time)
    resource_usage: Optional[Dict[str, float]] = None
    partial_response: Optional[str] = None


@dataclass
class RecoveryResult:
    """Result of error recovery attempt."""
    success: bool
    response: Optional[Union[str, OptimizedResponse]] = None
    strategy_used: Optional[RecoveryStrategy] = None
    fallback_model: Optional[str] = None
    degradation_level: int = 0  # 0 = no degradation, higher = more degraded
    recovery_time: float = 0.0
    error_message: Optional[str] = None


class ErrorRecoverySystem:
    """
    Comprehensive error recovery system that handles various failure modes
    and provides graceful degradation capabilities.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recovery_strategies: Dict[ErrorType, List[RecoveryStrategy]] = {
            ErrorType.MODEL_UNAVAILABLE: [
                RecoveryStrategy.FALLBACK_MODEL,
                RecoveryStrategy.CACHE_FALLBACK,
                RecoveryStrategy.EMERGENCY_RESPONSE
            ],
            ErrorType.MODEL_TIMEOUT: [
                RecoveryStrategy.FALLBACK_MODEL,
                RecoveryStrategy.REDUCE_COMPLEXITY,
                RecoveryStrategy.RETRY_WITH_BACKOFF
            ],
            ErrorType.ROUTING_ERROR: [
                RecoveryStrategy.FALLBACK_MODEL,
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                RecoveryStrategy.EMERGENCY_RESPONSE
            ],
            ErrorType.MEMORY_EXHAUSTION: [
                RecoveryStrategy.REDUCE_COMPLEXITY,
                RecoveryStrategy.FALLBACK_MODEL,
                RecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorType.STREAMING_INTERRUPTION: [
                RecoveryStrategy.PARTIAL_RESPONSE,
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                RecoveryStrategy.CACHE_FALLBACK
            ],
            ErrorType.PERFORMANCE_DEGRADATION: [
                RecoveryStrategy.FALLBACK_MODEL,
                RecoveryStrategy.REDUCE_COMPLEXITY,
                RecoveryStrategy.GRACEFUL_DEGRADATION
            ]
        }
        
        # Available fallback models by modality
        self.fallback_models: Dict[ModalityType, List[str]] = {
            ModalityType.TEXT: ["tinyllama", "gpt-3.5-turbo", "claude-3-haiku"],
            ModalityType.IMAGE: ["clip", "blip-2"],
            ModalityType.AUDIO: ["whisper-tiny"],
            ModalityType.VIDEO: ["clip"]
        }
        
        # Emergency response templates
        self.emergency_responses = {
            "general": "I apologize, but I'm experiencing technical difficulties. Please try your request again in a moment.",
            "model_unavailable": "The requested model is currently unavailable. I've switched to an alternative model to assist you.",
            "timeout": "Your request is taking longer than expected. I'm processing a simplified version of your query.",
            "memory": "I'm optimizing my response due to resource constraints. The core information you need is provided below."
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            "cpu_usage": 80.0,  # Percentage
            "memory_usage": 85.0,  # Percentage
            "response_time": 30.0,  # Seconds
            "gpu_memory": 90.0  # Percentage if GPU available
        }
    
    async def handle_error(self, error_context: ErrorContext) -> RecoveryResult:
        """
        Main error handling entry point that determines and executes
        the appropriate recovery strategy.
        """
        start_time = time.time()
        
        try:
            self.logger.warning(
                f"Handling error: {error_context.error_type.value} "
                f"for query: {error_context.query[:100]}..."
            )
            
            # Get recovery strategies for this error type
            strategies = self.recovery_strategies.get(
                error_context.error_type, 
                [RecoveryStrategy.EMERGENCY_RESPONSE]
            )
            
            # Try each strategy in order
            for strategy in strategies:
                try:
                    result = await self._execute_recovery_strategy(
                        strategy, error_context
                    )
                    
                    if result.success:
                        result.recovery_time = time.time() - start_time
                        self.logger.info(
                            f"Successfully recovered using {strategy.value} "
                            f"in {result.recovery_time:.2f}s"
                        )
                        return result
                        
                except Exception as e:
                    self.logger.error(
                        f"Recovery strategy {strategy.value} failed: {str(e)}"
                    )
                    continue
            
            # All strategies failed, return emergency response
            return RecoveryResult(
                success=True,
                response=self._get_emergency_response(error_context),
                strategy_used=RecoveryStrategy.EMERGENCY_RESPONSE,
                degradation_level=5,
                recovery_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error recovery system failed: {str(e)}")
            return RecoveryResult(
                success=False,
                error_message=str(e),
                recovery_time=time.time() - start_time
            )
    
    async def _execute_recovery_strategy(
        self, 
        strategy: RecoveryStrategy, 
        context: ErrorContext
    ) -> RecoveryResult:
        """Execute a specific recovery strategy."""
        
        if strategy == RecoveryStrategy.FALLBACK_MODEL:
            return await self._fallback_to_alternative_model(context)
        elif strategy == RecoveryStrategy.REDUCE_COMPLEXITY:
            return await self._reduce_query_complexity(context)
        elif strategy == RecoveryStrategy.CACHE_FALLBACK:
            return await self._fallback_to_cache(context)
        elif strategy == RecoveryStrategy.PARTIAL_RESPONSE:
            return await self._handle_partial_response(context)
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._graceful_degradation(context)
        elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return await self._retry_with_backoff(context)
        elif strategy == RecoveryStrategy.EMERGENCY_RESPONSE:
            return RecoveryResult(
                success=True,
                response=self._get_emergency_response(context),
                strategy_used=strategy,
                degradation_level=5
            )
        else:
            raise ValueError(f"Unknown recovery strategy: {strategy}")
    
    async def _fallback_to_alternative_model(
        self, 
        context: ErrorContext
    ) -> RecoveryResult:
        """Find and switch to an alternative model that supports required modalities."""
        
        try:
            # Determine required modalities
            required_modalities = context.modalities or [
                Modality(type=ModalityType.TEXT, input_supported=True, output_supported=True)
            ]
            
            # Find suitable fallback models
            fallback_candidates = []
            for modality in required_modalities:
                candidates = self.fallback_models.get(modality.type, [])
                fallback_candidates.extend(candidates)
            
            # Remove duplicates and exclude the failed model
            fallback_candidates = list(set(fallback_candidates))
            if context.model_id in fallback_candidates:
                fallback_candidates.remove(context.model_id)
            
            if not fallback_candidates:
                raise ValueError("No suitable fallback models available")
            
            # Try each fallback model
            for fallback_model in fallback_candidates:
                try:
                    # Simulate model switching and response generation
                    # In real implementation, this would use the actual model router
                    response = await self._generate_fallback_response(
                        context.query, fallback_model
                    )
                    
                    return RecoveryResult(
                        success=True,
                        response=response,
                        strategy_used=RecoveryStrategy.FALLBACK_MODEL,
                        fallback_model=fallback_model,
                        degradation_level=1
                    )
                    
                except Exception as e:
                    self.logger.warning(
                        f"Fallback model {fallback_model} failed: {str(e)}"
                    )
                    continue
            
            raise ValueError("All fallback models failed")
            
        except Exception as e:
            raise Exception(f"Fallback model strategy failed: {str(e)}")
    
    async def _reduce_query_complexity(
        self, 
        context: ErrorContext
    ) -> RecoveryResult:
        """Reduce query complexity to handle resource constraints."""
        
        try:
            # Simplify the query by removing complex requirements
            simplified_query = await self._simplify_query(context.query)
            
            # Generate response with reduced complexity
            response = await self._generate_simplified_response(
                simplified_query, context.model_id
            )
            
            return RecoveryResult(
                success=True,
                response=response,
                strategy_used=RecoveryStrategy.REDUCE_COMPLEXITY,
                degradation_level=2
            )
            
        except Exception as e:
            raise Exception(f"Complexity reduction strategy failed: {str(e)}")
    
    async def _fallback_to_cache(self, context: ErrorContext) -> RecoveryResult:
        """Attempt to serve response from cache."""
        
        try:
            # Simulate cache lookup
            # In real implementation, this would use the smart cache manager
            cached_response = await self._lookup_similar_cached_response(
                context.query
            )
            
            if cached_response:
                return RecoveryResult(
                    success=True,
                    response=cached_response,
                    strategy_used=RecoveryStrategy.CACHE_FALLBACK,
                    degradation_level=1
                )
            else:
                raise ValueError("No suitable cached response found")
                
        except Exception as e:
            raise Exception(f"Cache fallback strategy failed: {str(e)}")
    
    async def _handle_partial_response(
        self, 
        context: ErrorContext
    ) -> RecoveryResult:
        """Handle streaming interruption by providing partial response."""
        
        try:
            if context.partial_response:
                # Clean up and format partial response
                cleaned_response = await self._clean_partial_response(
                    context.partial_response
                )
                
                # Add interruption notice
                final_response = (
                    f"{cleaned_response}\n\n"
                    f"[Response was interrupted. The above information "
                    f"should address your main question.]"
                )
                
                return RecoveryResult(
                    success=True,
                    response=final_response,
                    strategy_used=RecoveryStrategy.PARTIAL_RESPONSE,
                    degradation_level=2
                )
            else:
                raise ValueError("No partial response available")
                
        except Exception as e:
            raise Exception(f"Partial response strategy failed: {str(e)}")
    
    async def _graceful_degradation(
        self, 
        context: ErrorContext
    ) -> RecoveryResult:
        """Implement graceful degradation with reduced functionality."""
        
        try:
            # Determine degradation level based on error type and resources
            degradation_level = await self._calculate_degradation_level(context)
            
            # Generate degraded response
            response = await self._generate_degraded_response(
                context.query, degradation_level
            )
            
            return RecoveryResult(
                success=True,
                response=response,
                strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                degradation_level=degradation_level
            )
            
        except Exception as e:
            raise Exception(f"Graceful degradation strategy failed: {str(e)}")
    
    async def _retry_with_backoff(self, context: ErrorContext) -> RecoveryResult:
        """Retry the operation with exponential backoff."""
        
        try:
            if context.attempt_count >= context.max_attempts:
                raise ValueError("Maximum retry attempts exceeded")
            
            # Calculate backoff delay
            delay = min(2 ** context.attempt_count, 10)  # Max 10 seconds
            await asyncio.sleep(delay)
            
            # Increment attempt count
            context.attempt_count += 1
            
            # Retry the original operation (simplified simulation)
            response = await self._retry_original_operation(context)
            
            return RecoveryResult(
                success=True,
                response=response,
                strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
                degradation_level=0
            )
            
        except Exception as e:
            raise Exception(f"Retry with backoff strategy failed: {str(e)}")
    
    # Helper methods for strategy implementation
    
    async def _generate_fallback_response(
        self, 
        query: str, 
        model_id: str
    ) -> str:
        """Generate response using fallback model."""
        # Simulate fallback model response generation
        await asyncio.sleep(0.1)  # Simulate processing time
        return f"[Fallback response using {model_id}] {query[:100]}..."
    
    async def _simplify_query(self, query: str) -> str:
        """Simplify query by removing complex requirements."""
        # Basic query simplification
        simplified = query.replace("detailed", "").replace("comprehensive", "")
        simplified = simplified.replace("in-depth", "").replace("thorough", "")
        return simplified.strip()
    
    async def _generate_simplified_response(
        self, 
        query: str, 
        model_id: Optional[str]
    ) -> str:
        """Generate simplified response."""
        await asyncio.sleep(0.1)
        return f"[Simplified response] {query[:50]}..."
    
    async def _lookup_similar_cached_response(self, query: str) -> Optional[str]:
        """Look up similar cached response."""
        # Simulate cache lookup
        await asyncio.sleep(0.05)
        if len(query) > 10:  # Simple heuristic
            return f"[Cached response] Similar to: {query[:30]}..."
        return None
    
    async def _clean_partial_response(self, partial_response: str) -> str:
        """Clean and format partial response."""
        # Remove incomplete sentences and format nicely
        lines = partial_response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.endswith(('...', '..', '.')):
                # Add period if missing
                if line and line[-1] not in '.!?':
                    line += '.'
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    async def _calculate_degradation_level(self, context: ErrorContext) -> int:
        """Calculate appropriate degradation level."""
        if context.error_type == ErrorType.MEMORY_EXHAUSTION:
            return 4
        elif context.error_type == ErrorType.PERFORMANCE_DEGRADATION:
            return 3
        elif context.error_type == ErrorType.MODEL_TIMEOUT:
            return 2
        else:
            return 1
    
    async def _generate_degraded_response(
        self, 
        query: str, 
        degradation_level: int
    ) -> str:
        """Generate response with specified degradation level."""
        await asyncio.sleep(0.1)
        
        if degradation_level >= 4:
            return f"[Minimal response due to resource constraints] {query[:20]}..."
        elif degradation_level >= 3:
            return f"[Reduced functionality response] {query[:40]}..."
        elif degradation_level >= 2:
            return f"[Simplified response] {query[:60]}..."
        else:
            return f"[Slightly degraded response] {query[:80]}..."
    
    async def _retry_original_operation(self, context: ErrorContext) -> str:
        """Retry the original operation."""
        # Simulate retry
        await asyncio.sleep(0.2)
        return f"[Retry successful] {context.query[:100]}..."
    
    def _get_emergency_response(self, context: ErrorContext) -> str:
        """Get appropriate emergency response."""
        error_type_map = {
            ErrorType.MODEL_UNAVAILABLE: "model_unavailable",
            ErrorType.MODEL_TIMEOUT: "timeout",
            ErrorType.MEMORY_EXHAUSTION: "memory"
        }
        
        response_type = error_type_map.get(context.error_type, "general")
        return self.emergency_responses[response_type]
    
    # Resource monitoring methods
    
    async def monitor_system_resources(self) -> Dict[str, float]:
        """Monitor current system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            resources = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "available_memory": memory.available / (1024**3)  # GB
            }
            
            # Add GPU monitoring if available
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    resources["gpu_memory_usage"] = gpu.memoryUtil * 100
                    resources["gpu_utilization"] = gpu.load * 100
            except ImportError:
                pass
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Resource monitoring failed: {str(e)}")
            return {}
    
    async def check_performance_thresholds(self) -> List[str]:
        """Check if any performance thresholds are exceeded."""
        resources = await self.monitor_system_resources()
        violations = []
        
        for metric, threshold in self.performance_thresholds.items():
            if metric in resources and resources[metric] > threshold:
                violations.append(f"{metric}: {resources[metric]:.1f}% > {threshold}%")
        
        return violations
    
    @asynccontextmanager
    async def error_recovery_context(
        self, 
        query: str, 
        model_id: Optional[str] = None,
        modalities: Optional[List[Modality]] = None
    ):
        """Context manager for automatic error recovery."""
        try:
            yield
        except Exception as e:
            # Determine error type
            error_type = self._classify_error(e)
            
            # Create error context
            context = ErrorContext(
                error_type=error_type,
                original_error=e,
                query=query,
                model_id=model_id,
                modalities=modalities or []
            )
            
            # Attempt recovery
            recovery_result = await self.handle_error(context)
            
            if recovery_result.success:
                # Log successful recovery
                self.logger.info(
                    f"Recovered from {error_type.value} using "
                    f"{recovery_result.strategy_used.value}"
                )
                # Store recovery result for retrieval
                self._recovery_result = recovery_result.response
            else:
                # Re-raise if recovery failed
                raise e
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception details."""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "time" in error_str:
            return ErrorType.MODEL_TIMEOUT
        elif "memory" in error_str or "oom" in error_str:
            return ErrorType.MEMORY_EXHAUSTION
        elif "connection" in error_str or "network" in error_str:
            return ErrorType.CONNECTION_FAILURE
        elif "model" in error_str and "unavailable" in error_str:
            return ErrorType.MODEL_UNAVAILABLE
        elif "routing" in error_str or "route" in error_str:
            return ErrorType.ROUTING_ERROR
        elif "stream" in error_str or "interrupt" in error_str:
            return ErrorType.STREAMING_INTERRUPTION
        else:
            return ErrorType.PERFORMANCE_DEGRADATION


# Global error recovery system instance
error_recovery_system = ErrorRecoverySystem()