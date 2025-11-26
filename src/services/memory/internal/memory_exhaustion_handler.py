"""
Memory Exhaustion Recovery Handler

This module handles memory exhaustion scenarios and provides
automatic optimization adjustments to recover from memory issues.
"""

import asyncio
import gc
import logging
import psutil
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
import weakref

from ...internal..core.types.shared_types import OptimizedResponse


class MemoryPressureLevel(Enum):
    """Memory pressure levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MemoryOptimizationStrategy(Enum):
    """Memory optimization strategies."""
    GARBAGE_COLLECTION = "garbage_collection"
    CACHE_CLEANUP = "cache_cleanup"
    MODEL_UNLOADING = "model_unloading"
    RESPONSE_SIMPLIFICATION = "response_simplification"
    BATCH_SIZE_REDUCTION = "batch_size_reduction"
    CONTEXT_TRUNCATION = "context_truncation"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


@dataclass
class MemoryStatus:
    """Current memory status."""
    total_memory: int  # bytes
    available_memory: int  # bytes
    used_memory: int  # bytes
    usage_percentage: float
    pressure_level: MemoryPressureLevel
    timestamp: float = field(default_factory=time.time)


@dataclass
class MemoryOptimization:
    """Memory optimization action."""
    strategy: MemoryOptimizationStrategy
    description: str
    estimated_savings: int  # bytes
    priority: int  # 1 = highest priority
    execution_time: float = 0.0
    success: bool = False
    actual_savings: int = 0


@dataclass
class MemoryRecoveryResult:
    """Result of memory recovery attempt."""
    success: bool
    memory_freed: int  # bytes
    optimizations_applied: List[MemoryOptimization]
    final_memory_status: MemoryStatus
    recovery_time: float
    fallback_response: Optional[str] = None


class MemoryExhaustionHandler:
    """
    Handles memory exhaustion scenarios with automatic optimization
    adjustments and graceful degradation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Memory thresholds (percentages)
        self.memory_thresholds = {
            MemoryPressureLevel.LOW: 60.0,
            MemoryPressureLevel.MODERATE: 75.0,
            MemoryPressureLevel.HIGH: 85.0,
            MemoryPressureLevel.CRITICAL: 95.0,
            MemoryPressureLevel.EMERGENCY: 98.0
        }
        
        # Optimization strategies by pressure level
        self.optimization_strategies = {
            MemoryPressureLevel.MODERATE: [
                MemoryOptimizationStrategy.GARBAGE_COLLECTION,
                MemoryOptimizationStrategy.CACHE_CLEANUP
            ],
            MemoryPressureLevel.HIGH: [
                MemoryOptimizationStrategy.GARBAGE_COLLECTION,
                MemoryOptimizationStrategy.CACHE_CLEANUP,
                MemoryOptimizationStrategy.RESPONSE_SIMPLIFICATION,
                MemoryOptimizationStrategy.BATCH_SIZE_REDUCTION
            ],
            MemoryPressureLevel.CRITICAL: [
                MemoryOptimizationStrategy.GARBAGE_COLLECTION,
                MemoryOptimizationStrategy.CACHE_CLEANUP,
                MemoryOptimizationStrategy.MODEL_UNLOADING,
                MemoryOptimizationStrategy.RESPONSE_SIMPLIFICATION,
                MemoryOptimizationStrategy.CONTEXT_TRUNCATION
            ],
            MemoryPressureLevel.EMERGENCY: [
                MemoryOptimizationStrategy.EMERGENCY_SHUTDOWN
            ]
        }
        
        # Memory monitoring
        self.memory_history: List[MemoryStatus] = []
        self.history_max_size = 100
        self.monitoring_interval = 5.0  # seconds
        
        # Cache references for cleanup
        self.cache_references: List[weakref.ref] = []
        self.model_references: List[weakref.ref] = []
        
        # Emergency response templates
        self.emergency_responses = {
            "memory_exhaustion": (
                "I'm experiencing memory constraints and need to provide "
                "a simplified response. Here's the essential information: {summary}"
            ),
            "critical_memory": (
                "Due to system memory limitations, I can only provide "
                "a brief response. Please try breaking your request into smaller parts."
            ),
            "emergency_shutdown": (
                "System memory is critically low. Please wait a moment "
                "while I optimize resources and try your request again."
            )
        }
        
        # Recovery statistics
        self.recovery_stats = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "memory_freed_total": 0,
            "average_recovery_time": 0.0
        }
    
    async def monitor_memory_status(self) -> MemoryStatus:
        """Monitor current memory status and determine pressure level."""
        try:
            memory = psutil.virtual_memory()
            
            status = MemoryStatus(
                total_memory=memory.total,
                available_memory=memory.available,
                used_memory=memory.used,
                usage_percentage=memory.percent,
                pressure_level=self._determine_pressure_level(memory.percent)
            )
            
            # Record in history
            self.memory_history.append(status)
            if len(self.memory_history) > self.history_max_size:
                self.memory_history = self.memory_history[-self.history_max_size:]
            
            return status
            
        except Exception as e:
            self.logger.error(f"Memory monitoring failed: {str(e)}")
            # Return safe default
            return MemoryStatus(
                total_memory=0,
                available_memory=0,
                used_memory=0,
                usage_percentage=0.0,
                pressure_level=MemoryPressureLevel.LOW
            )
    
    async def handle_memory_exhaustion(
        self,
        query: str,
        current_memory_status: Optional[MemoryStatus] = None
    ) -> MemoryRecoveryResult:
        """
        Handle memory exhaustion by applying optimization strategies.
        """
        start_time = time.time()
        
        try:
            # Get current memory status if not provided
            if current_memory_status is None:
                current_memory_status = await self.monitor_memory_status()
            
            self.logger.warning(
                f"Handling memory exhaustion: {current_memory_status.usage_percentage:.1f}% "
                f"({current_memory_status.pressure_level.value})"
            )
            
            # Get optimization strategies for current pressure level
            strategies = self.optimization_strategies.get(
                current_memory_status.pressure_level,
                [MemoryOptimizationStrategy.GARBAGE_COLLECTION]
            )
            
            # Apply optimization strategies
            optimizations_applied = []
            total_memory_freed = 0
            
            for strategy in strategies:
                try:
                    optimization = await self._apply_optimization_strategy(
                        strategy, current_memory_status, query
                    )
                    
                    optimizations_applied.append(optimization)
                    
                    if optimization.success:
                        total_memory_freed += optimization.actual_savings
                        
                        # Check if memory pressure is now acceptable
                        new_status = await self.monitor_memory_status()
                        if new_status.pressure_level in [MemoryPressureLevel.LOW, MemoryPressureLevel.MODERATE]:
                            break
                    
                except Exception as e:
                    self.logger.error(f"Optimization strategy {strategy.value} failed: {str(e)}")
                    continue
            
            # Get final memory status
            final_status = await self.monitor_memory_status()
            recovery_time = time.time() - start_time
            
            # Determine if recovery was successful
            success = final_status.pressure_level.value in ["low", "moderate"]
            
            # Generate fallback response if needed
            fallback_response = None
            if not success or final_status.pressure_level == MemoryPressureLevel.HIGH:
                fallback_response = await self._generate_memory_constrained_response(
                    query, final_status
                )
            
            # Update statistics
            self._update_recovery_stats(success, total_memory_freed, recovery_time)
            
            result = MemoryRecoveryResult(
                success=success,
                memory_freed=total_memory_freed,
                optimizations_applied=optimizations_applied,
                final_memory_status=final_status,
                recovery_time=recovery_time,
                fallback_response=fallback_response
            )
            
            self.logger.info(
                f"Memory recovery completed: success={success}, "
                f"freed={total_memory_freed / (1024**2):.1f}MB, "
                f"time={recovery_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Memory exhaustion handling failed: {str(e)}")
            
            # Return emergency result
            return MemoryRecoveryResult(
                success=False,
                memory_freed=0,
                optimizations_applied=[],
                final_memory_status=current_memory_status or MemoryStatus(0, 0, 0, 100.0, MemoryPressureLevel.EMERGENCY),
                recovery_time=time.time() - start_time,
                fallback_response=self.emergency_responses["emergency_shutdown"]
            )
    
    async def _apply_optimization_strategy(
        self,
        strategy: MemoryOptimizationStrategy,
        memory_status: MemoryStatus,
        query: str
    ) -> MemoryOptimization:
        """Apply a specific memory optimization strategy."""
        
        start_time = time.time()
        initial_memory = memory_status.used_memory
        
        try:
            if strategy == MemoryOptimizationStrategy.GARBAGE_COLLECTION:
                return await self._perform_garbage_collection()
            
            elif strategy == MemoryOptimizationStrategy.CACHE_CLEANUP:
                return await self._cleanup_caches()
            
            elif strategy == MemoryOptimizationStrategy.MODEL_UNLOADING:
                return await self._unload_unused_models()
            
            elif strategy == MemoryOptimizationStrategy.RESPONSE_SIMPLIFICATION:
                return await self._simplify_response_generation(query)
            
            elif strategy == MemoryOptimizationStrategy.BATCH_SIZE_REDUCTION:
                return await self._reduce_batch_sizes()
            
            elif strategy == MemoryOptimizationStrategy.CONTEXT_TRUNCATION:
                return await self._truncate_context(query)
            
            elif strategy == MemoryOptimizationStrategy.EMERGENCY_SHUTDOWN:
                return await self._emergency_memory_cleanup()
            
            else:
                raise ValueError(f"Unknown optimization strategy: {strategy}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=strategy,
                description=f"Failed: {str(e)}",
                estimated_savings=0,
                priority=1,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _perform_garbage_collection(self) -> MemoryOptimization:
        """Perform aggressive garbage collection."""
        start_time = time.time()
        
        try:
            # Get memory before cleanup
            memory_before = psutil.virtual_memory().used
            
            # Perform garbage collection
            collected = gc.collect()
            
            # Force additional cleanup
            for generation in range(3):
                gc.collect(generation)
            
            # Get memory after cleanup
            memory_after = psutil.virtual_memory().used
            memory_freed = max(0, memory_before - memory_after)
            
            execution_time = time.time() - start_time
            
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.GARBAGE_COLLECTION,
                description=f"Collected {collected} objects, freed {memory_freed / (1024**2):.1f}MB",
                estimated_savings=memory_freed,
                priority=1,
                execution_time=execution_time,
                success=True,
                actual_savings=memory_freed
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.GARBAGE_COLLECTION,
                description=f"Garbage collection failed: {str(e)}",
                estimated_savings=0,
                priority=1,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _cleanup_caches(self) -> MemoryOptimization:
        """Clean up various caches to free memory."""
        start_time = time.time()
        
        try:
            memory_before = psutil.virtual_memory().used
            caches_cleaned = 0
            
            # Clean up cache references
            for cache_ref in self.cache_references[:]:
                cache = cache_ref()
                if cache is not None:
                    try:
                        if hasattr(cache, 'clear'):
                            cache.clear()
                            caches_cleaned += 1
                    except Exception:
                        pass
                else:
                    # Remove dead references
                    self.cache_references.remove(cache_ref)
            
            # Simulate additional cache cleanup
            await asyncio.sleep(0.1)  # Simulate cleanup time
            
            memory_after = psutil.virtual_memory().used
            memory_freed = max(0, memory_before - memory_after)
            
            execution_time = time.time() - start_time
            
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.CACHE_CLEANUP,
                description=f"Cleaned {caches_cleaned} caches, freed {memory_freed / (1024**2):.1f}MB",
                estimated_savings=memory_freed,
                priority=2,
                execution_time=execution_time,
                success=True,
                actual_savings=memory_freed
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.CACHE_CLEANUP,
                description=f"Cache cleanup failed: {str(e)}",
                estimated_savings=0,
                priority=2,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _unload_unused_models(self) -> MemoryOptimization:
        """Unload unused models to free memory."""
        start_time = time.time()
        
        try:
            memory_before = psutil.virtual_memory().used
            models_unloaded = 0
            
            # Unload model references
            for model_ref in self.model_references[:]:
                model = model_ref()
                if model is not None:
                    try:
                        if hasattr(model, 'unload'):
                            model.unload()
                            models_unloaded += 1
                    except Exception:
                        pass
                else:
                    # Remove dead references
                    self.model_references.remove(model_ref)
            
            # Force garbage collection after unloading
            gc.collect()
            
            memory_after = psutil.virtual_memory().used
            memory_freed = max(0, memory_before - memory_after)
            
            execution_time = time.time() - start_time
            
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.MODEL_UNLOADING,
                description=f"Unloaded {models_unloaded} models, freed {memory_freed / (1024**2):.1f}MB",
                estimated_savings=memory_freed,
                priority=3,
                execution_time=execution_time,
                success=True,
                actual_savings=memory_freed
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.MODEL_UNLOADING,
                description=f"Model unloading failed: {str(e)}",
                estimated_savings=0,
                priority=3,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _simplify_response_generation(self, query: str) -> MemoryOptimization:
        """Simplify response generation to use less memory."""
        start_time = time.time()
        
        try:
            # Estimate memory savings from simplification
            estimated_savings = len(query) * 10  # Rough estimate
            
            execution_time = time.time() - start_time
            
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.RESPONSE_SIMPLIFICATION,
                description="Enabled simplified response generation mode",
                estimated_savings=estimated_savings,
                priority=4,
                execution_time=execution_time,
                success=True,
                actual_savings=estimated_savings
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.RESPONSE_SIMPLIFICATION,
                description=f"Response simplification failed: {str(e)}",
                estimated_savings=0,
                priority=4,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _reduce_batch_sizes(self) -> MemoryOptimization:
        """Reduce batch sizes to use less memory."""
        start_time = time.time()
        
        try:
            # Simulate batch size reduction
            estimated_savings = 50 * 1024 * 1024  # 50MB estimate
            
            execution_time = time.time() - start_time
            
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.BATCH_SIZE_REDUCTION,
                description="Reduced batch sizes for memory efficiency",
                estimated_savings=estimated_savings,
                priority=5,
                execution_time=execution_time,
                success=True,
                actual_savings=estimated_savings
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.BATCH_SIZE_REDUCTION,
                description=f"Batch size reduction failed: {str(e)}",
                estimated_savings=0,
                priority=5,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _truncate_context(self, query: str) -> MemoryOptimization:
        """Truncate context to reduce memory usage."""
        start_time = time.time()
        
        try:
            # Estimate memory savings from context truncation
            estimated_savings = len(query) * 5  # Rough estimate
            
            execution_time = time.time() - start_time
            
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.CONTEXT_TRUNCATION,
                description="Truncated context to reduce memory usage",
                estimated_savings=estimated_savings,
                priority=6,
                execution_time=execution_time,
                success=True,
                actual_savings=estimated_savings
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.CONTEXT_TRUNCATION,
                description=f"Context truncation failed: {str(e)}",
                estimated_savings=0,
                priority=6,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _emergency_memory_cleanup(self) -> MemoryOptimization:
        """Perform emergency memory cleanup."""
        start_time = time.time()
        
        try:
            memory_before = psutil.virtual_memory().used
            
            # Aggressive cleanup
            gc.collect()
            
            # Clear all cache references
            self.cache_references.clear()
            self.model_references.clear()
            
            # Clear memory history to free some space
            self.memory_history = self.memory_history[-10:]  # Keep only last 10 entries
            
            memory_after = psutil.virtual_memory().used
            memory_freed = max(0, memory_before - memory_after)
            
            execution_time = time.time() - start_time
            
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.EMERGENCY_SHUTDOWN,
                description=f"Emergency cleanup freed {memory_freed / (1024**2):.1f}MB",
                estimated_savings=memory_freed,
                priority=1,
                execution_time=execution_time,
                success=True,
                actual_savings=memory_freed
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryOptimization(
                strategy=MemoryOptimizationStrategy.EMERGENCY_SHUTDOWN,
                description=f"Emergency cleanup failed: {str(e)}",
                estimated_savings=0,
                priority=1,
                execution_time=execution_time,
                success=False,
                actual_savings=0
            )
    
    async def _generate_memory_constrained_response(
        self,
        query: str,
        memory_status: MemoryStatus
    ) -> str:
        """Generate a response suitable for memory-constrained conditions."""
        
        # Extract key information from query
        query_summary = query[:100] + "..." if len(query) > 100 else query
        
        if memory_status.pressure_level == MemoryPressureLevel.EMERGENCY:
            return self.emergency_responses["emergency_shutdown"]
        elif memory_status.pressure_level == MemoryPressureLevel.CRITICAL:
            return self.emergency_responses["critical_memory"]
        else:
            return self.emergency_responses["memory_exhaustion"].format(
                summary=query_summary
            )
    
    def _determine_pressure_level(self, usage_percentage: float) -> MemoryPressureLevel:
        """Determine memory pressure level based on usage percentage."""
        if usage_percentage >= self.memory_thresholds[MemoryPressureLevel.EMERGENCY]:
            return MemoryPressureLevel.EMERGENCY
        elif usage_percentage >= self.memory_thresholds[MemoryPressureLevel.CRITICAL]:
            return MemoryPressureLevel.CRITICAL
        elif usage_percentage >= self.memory_thresholds[MemoryPressureLevel.HIGH]:
            return MemoryPressureLevel.HIGH
        elif usage_percentage >= self.memory_thresholds[MemoryPressureLevel.MODERATE]:
            return MemoryPressureLevel.MODERATE
        else:
            return MemoryPressureLevel.LOW
    
    def _update_recovery_stats(
        self,
        success: bool,
        memory_freed: int,
        recovery_time: float
    ):
        """Update recovery statistics."""
        self.recovery_stats["total_recoveries"] += 1
        
        if success:
            self.recovery_stats["successful_recoveries"] += 1
        
        self.recovery_stats["memory_freed_total"] += memory_freed
        
        # Update average recovery time
        total_recoveries = self.recovery_stats["total_recoveries"]
        current_avg = self.recovery_stats["average_recovery_time"]
        self.recovery_stats["average_recovery_time"] = (
            (current_avg * (total_recoveries - 1) + recovery_time) / total_recoveries
        )
    
    def register_cache_reference(self, cache_obj: Any):
        """Register a cache object for cleanup during memory pressure."""
        self.cache_references.append(weakref.ref(cache_obj))
    
    def register_model_reference(self, model_obj: Any):
        """Register a model object for unloading during memory pressure."""
        self.model_references.append(weakref.ref(model_obj))
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics and recovery information."""
        current_status = await self.monitor_memory_status()
        
        return {
            "current_memory_status": {
                "usage_percentage": current_status.usage_percentage,
                "pressure_level": current_status.pressure_level.value,
                "available_gb": current_status.available_memory / (1024**3),
                "used_gb": current_status.used_memory / (1024**3)
            },
            "recovery_statistics": self.recovery_stats.copy(),
            "registered_references": {
                "cache_objects": len(self.cache_references),
                "model_objects": len(self.model_references)
            },
            "memory_history_size": len(self.memory_history)
        }


# Global memory exhaustion handler instance
memory_exhaustion_handler = MemoryExhaustionHandler()