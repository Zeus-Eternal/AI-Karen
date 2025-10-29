"""
Graceful Degradation Coordinator

This module coordinates all error handling and graceful degradation
components to provide a unified error recovery system that maintains
functionality when models are unavailable or resources are constrained.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from contextlib import asynccontextmanager

from .error_recovery_system import (
    ErrorRecoverySystem, ErrorContext, ErrorType, RecoveryResult
)
from .model_availability_handler import (
    ModelAvailabilityHandler, ModalityRequirement, ModelAvailabilityStatus
)
from .timeout_performance_handler import (
    TimeoutPerformanceHandler, PerformanceIssue, PerformanceIssueType
)
from .memory_exhaustion_handler import (
    MemoryExhaustionHandler, MemoryPressureLevel, MemoryRecoveryResult
)
from .streaming_interruption_handler import (
    StreamingInterruptionHandler, InterruptionContext, InterruptionType
)

from ..core.types.shared_types import (
    ModelInfo, Modality, ModalityType, OptimizedResponse, PerformanceMetrics
)


class SystemHealthStatus(Enum):
    """Overall system health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class DegradationLevel(Enum):
    """Levels of system degradation."""
    NONE = 0
    MINIMAL = 1
    MODERATE = 2
    SIGNIFICANT = 3
    SEVERE = 4
    EMERGENCY = 5


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""
    overall_status: SystemHealthStatus
    degradation_level: DegradationLevel
    available_models: List[str]
    unavailable_models: List[str]
    memory_pressure: MemoryPressureLevel
    performance_issues: List[PerformanceIssue]
    active_recoveries: int
    timestamp: float = field(default_factory=time.time)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DegradationContext:
    """Context for graceful degradation decisions."""
    query: str
    requested_model: Optional[str] = None
    required_modalities: List[Modality] = field(default_factory=list)
    user_priority: int = 1  # 1 = high, 5 = low
    timeout_tolerance: float = 30.0
    quality_tolerance: float = 0.7  # 0.0 = any quality, 1.0 = perfect quality
    allow_fallback: bool = True
    allow_degradation: bool = True


@dataclass
class DegradationResponse:
    """Response with degradation information."""
    content: str
    degradation_level: DegradationLevel
    model_used: Optional[str]
    fallback_applied: bool
    optimizations_applied: List[str]
    quality_score: float
    response_time: float
    warnings: List[str] = field(default_factory=list)


class GracefulDegradationCoordinator:
    """
    Coordinates all error handling and graceful degradation components
    to provide unified error recovery and maintain system functionality.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize component handlers
        self.error_recovery = ErrorRecoverySystem()
        self.model_availability = ModelAvailabilityHandler()
        self.timeout_performance = TimeoutPerformanceHandler()
        self.memory_exhaustion = MemoryExhaustionHandler()
        self.streaming_interruption = StreamingInterruptionHandler()
        
        # System health monitoring
        self.health_check_interval = 30.0  # seconds
        self.last_health_check = 0.0
        self.current_health_status = SystemHealthStatus.HEALTHY
        self.current_degradation_level = DegradationLevel.NONE
        
        # Degradation policies
        self.degradation_policies = {
            DegradationLevel.MINIMAL: {
                "allow_model_fallback": True,
                "allow_response_simplification": False,
                "allow_timeout_extension": True,
                "allow_cache_fallback": True
            },
            DegradationLevel.MODERATE: {
                "allow_model_fallback": True,
                "allow_response_simplification": True,
                "allow_timeout_extension": True,
                "allow_cache_fallback": True,
                "reduce_response_quality": 0.1
            },
            DegradationLevel.SIGNIFICANT: {
                "allow_model_fallback": True,
                "allow_response_simplification": True,
                "allow_timeout_extension": True,
                "allow_cache_fallback": True,
                "reduce_response_quality": 0.3,
                "enable_emergency_responses": False
            },
            DegradationLevel.SEVERE: {
                "allow_model_fallback": True,
                "allow_response_simplification": True,
                "allow_timeout_extension": False,
                "allow_cache_fallback": True,
                "reduce_response_quality": 0.5,
                "enable_emergency_responses": True
            },
            DegradationLevel.EMERGENCY: {
                "allow_model_fallback": True,
                "allow_response_simplification": True,
                "allow_timeout_extension": False,
                "allow_cache_fallback": True,
                "reduce_response_quality": 0.8,
                "enable_emergency_responses": True,
                "force_minimal_responses": True
            }
        }
        
        # Recovery coordination
        self.active_recoveries: Dict[str, Dict[str, Any]] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.degradation_stats = {
            "total_requests": 0,
            "degraded_requests": 0,
            "fallback_requests": 0,
            "emergency_responses": 0,
            "average_degradation_level": 0.0
        }
    
    @asynccontextmanager
    async def graceful_execution(
        self,
        context: DegradationContext
    ):
        """
        Context manager for graceful execution with automatic
        error recovery and degradation handling.
        """
        execution_id = f"exec_{int(time.time())}_{id(context)}"
        start_time = time.time()
        
        try:
            # Update request statistics
            self.degradation_stats["total_requests"] += 1
            
            # Check system health
            health_report = await self.assess_system_health()
            
            # Determine if degradation is needed
            degradation_needed = await self._should_apply_degradation(
                context, health_report
            )
            
            if degradation_needed:
                self.degradation_stats["degraded_requests"] += 1
                
                # Apply preemptive degradation
                degraded_context = await self._apply_preemptive_degradation(
                    context, health_report
                )
                
                yield degraded_context
            else:
                yield context
                
        except Exception as e:
            # Handle error with coordinated recovery
            recovery_result = await self._coordinate_error_recovery(
                execution_id, context, e
            )
            
            if recovery_result and recovery_result.success:
                # Store recovered response for retrieval
                self._recovery_result = recovery_result.response
            else:
                # Re-raise if recovery failed
                raise e
                
        finally:
            # Cleanup and update statistics
            execution_time = time.time() - start_time
            await self._cleanup_execution(execution_id, execution_time)
    
    async def assess_system_health(self) -> SystemHealthReport:
        """
        Assess overall system health and determine degradation needs.
        """
        try:
            current_time = time.time()
            
            # Skip if recent health check exists
            if current_time - self.last_health_check < self.health_check_interval:
                return await self._get_cached_health_report()
            
            # Check memory status
            memory_status = await self.memory_exhaustion.monitor_memory_status()
            
            # Check model availability
            available_models = []
            unavailable_models = []
            
            # Simulate model availability check
            test_models = ["tinyllama", "gpt-3.5-turbo", "claude-3-haiku"]
            for model_id in test_models:
                health_check = await self.model_availability.check_model_availability(model_id)
                if health_check.status == ModelAvailabilityStatus.AVAILABLE:
                    available_models.append(model_id)
                else:
                    unavailable_models.append(model_id)
            
            # Get performance issues
            performance_issues = []
            # This would be populated by actual performance monitoring
            
            # Determine overall health status
            overall_status = self._determine_overall_health_status(
                memory_status, available_models, performance_issues
            )
            
            # Determine degradation level
            degradation_level = self._determine_degradation_level(
                overall_status, memory_status, len(unavailable_models)
            )
            
            # Generate recommendations
            recommendations = await self._generate_health_recommendations(
                memory_status, available_models, unavailable_models
            )
            
            health_report = SystemHealthReport(
                overall_status=overall_status,
                degradation_level=degradation_level,
                available_models=available_models,
                unavailable_models=unavailable_models,
                memory_pressure=memory_status.pressure_level,
                performance_issues=performance_issues,
                active_recoveries=len(self.active_recoveries),
                recommendations=recommendations
            )
            
            # Update cached status
            self.current_health_status = overall_status
            self.current_degradation_level = degradation_level
            self.last_health_check = current_time
            
            return health_report
            
        except Exception as e:
            self.logger.error(f"System health assessment failed: {str(e)}")
            
            # Return safe default
            return SystemHealthReport(
                overall_status=SystemHealthStatus.CRITICAL,
                degradation_level=DegradationLevel.SEVERE,
                available_models=[],
                unavailable_models=[],
                memory_pressure=MemoryPressureLevel.HIGH,
                performance_issues=[],
                active_recoveries=0,
                recommendations=["System health assessment failed - manual intervention needed"]
            )
    
    async def handle_coordinated_recovery(
        self,
        query: str,
        error: Exception,
        model_id: Optional[str] = None,
        modalities: Optional[List[Modality]] = None
    ) -> DegradationResponse:
        """
        Handle coordinated recovery across all error handling components.
        """
        start_time = time.time()
        recovery_id = f"recovery_{int(time.time())}_{id(error)}"
        
        try:
            self.logger.info(f"Starting coordinated recovery: {recovery_id}")
            
            # Classify the error and determine primary handler
            error_classification = await self._classify_error_for_coordination(error)
            
            # Create recovery context
            context = DegradationContext(
                query=query,
                requested_model=model_id,
                required_modalities=modalities or []
            )
            
            # Track active recovery
            self.active_recoveries[recovery_id] = {
                "start_time": start_time,
                "error_type": error_classification,
                "context": context
            }
            
            # Coordinate recovery based on error type
            recovery_result = await self._execute_coordinated_recovery(
                recovery_id, error_classification, error, context
            )
            
            # Create degradation response
            response = DegradationResponse(
                content=recovery_result.get("content", ""),
                degradation_level=recovery_result.get("degradation_level", DegradationLevel.MODERATE),
                model_used=recovery_result.get("model_used"),
                fallback_applied=recovery_result.get("fallback_applied", False),
                optimizations_applied=recovery_result.get("optimizations_applied", []),
                quality_score=recovery_result.get("quality_score", 0.5),
                response_time=time.time() - start_time,
                warnings=recovery_result.get("warnings", [])
            )
            
            # Update statistics
            self._update_degradation_stats(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Coordinated recovery failed: {str(e)}")
            
            # Return emergency response
            return DegradationResponse(
                content="I apologize, but I'm experiencing technical difficulties. Please try your request again.",
                degradation_level=DegradationLevel.EMERGENCY,
                model_used=None,
                fallback_applied=True,
                optimizations_applied=["emergency_response"],
                quality_score=0.1,
                response_time=time.time() - start_time,
                warnings=["Emergency response due to system failure"]
            )
            
        finally:
            # Cleanup recovery tracking
            if recovery_id in self.active_recoveries:
                del self.active_recoveries[recovery_id]
    
    # Helper methods
    
    async def _should_apply_degradation(
        self,
        context: DegradationContext,
        health_report: SystemHealthReport
    ) -> bool:
        """Determine if preemptive degradation should be applied."""
        
        # Apply degradation if system health is poor
        if health_report.overall_status in [SystemHealthStatus.CRITICAL, SystemHealthStatus.EMERGENCY]:
            return True
        
        # Apply degradation if memory pressure is high
        if health_report.memory_pressure in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
            return True
        
        # Apply degradation if requested model is unavailable
        if context.requested_model and context.requested_model in health_report.unavailable_models:
            return True
        
        # Apply degradation if too many performance issues
        if len(health_report.performance_issues) > 3:
            return True
        
        return False
    
    async def _apply_preemptive_degradation(
        self,
        context: DegradationContext,
        health_report: SystemHealthReport
    ) -> DegradationContext:
        """Apply preemptive degradation to context."""
        
        degraded_context = DegradationContext(
            query=context.query,
            requested_model=context.requested_model,
            required_modalities=context.required_modalities,
            user_priority=context.user_priority,
            timeout_tolerance=context.timeout_tolerance,
            quality_tolerance=context.quality_tolerance,
            allow_fallback=context.allow_fallback,
            allow_degradation=context.allow_degradation
        )
        
        # Apply degradation based on health status
        if health_report.overall_status == SystemHealthStatus.CRITICAL:
            degraded_context.timeout_tolerance *= 0.5
            degraded_context.quality_tolerance *= 0.7
        elif health_report.overall_status == SystemHealthStatus.EMERGENCY:
            degraded_context.timeout_tolerance *= 0.3
            degraded_context.quality_tolerance *= 0.5
        
        # Apply model fallback if needed
        if context.requested_model in health_report.unavailable_models:
            if health_report.available_models:
                degraded_context.requested_model = health_report.available_models[0]
            else:
                degraded_context.requested_model = None
        
        return degraded_context
    
    async def _coordinate_error_recovery(
        self,
        execution_id: str,
        context: DegradationContext,
        error: Exception
    ) -> Optional[RecoveryResult]:
        """Coordinate error recovery across all handlers."""
        
        try:
            # Classify error
            error_type = self._classify_error_type(error)
            
            # Create error context
            error_context = ErrorContext(
                error_type=error_type,
                original_error=error,
                query=context.query,
                model_id=context.requested_model,
                modalities=context.required_modalities
            )
            
            # Use appropriate handler based on error type
            if error_type == ErrorType.MODEL_UNAVAILABLE:
                # Use model availability handler
                fallback_model, error_msg = await self.model_availability.handle_routing_error(
                    context.requested_model or "",
                    error,
                    [ModalityRequirement(m.type) for m in context.required_modalities]
                )
                
                if fallback_model:
                    return RecoveryResult(
                        success=True,
                        response=f"Switched to fallback model: {fallback_model}",
                        strategy_used=None,
                        fallback_model=fallback_model
                    )
            
            elif error_type == ErrorType.MEMORY_EXHAUSTION:
                # Use memory exhaustion handler
                memory_recovery = await self.memory_exhaustion.handle_memory_exhaustion(
                    context.query
                )
                
                if memory_recovery.success:
                    return RecoveryResult(
                        success=True,
                        response=memory_recovery.fallback_response or "Memory optimized",
                        strategy_used=None
                    )
            
            elif error_type == ErrorType.STREAMING_INTERRUPTION:
                # Use streaming interruption handler
                interruption_context = InterruptionContext(
                    interruption_type=InterruptionType.SERVER_ERROR,
                    original_error=error,
                    query=context.query,
                    model_id=context.requested_model
                )
                
                streaming_recovery = await self.streaming_interruption.handle_streaming_interruption(
                    interruption_context
                )
                
                if streaming_recovery.success:
                    return RecoveryResult(
                        success=True,
                        response=streaming_recovery.recovered_content,
                        strategy_used=None
                    )
            
            # Fall back to general error recovery
            return await self.error_recovery.handle_error(error_context)
            
        except Exception as e:
            self.logger.error(f"Error recovery coordination failed: {str(e)}")
            return None
    
    def _classify_error_type(self, error: Exception) -> ErrorType:
        """Classify error type for coordination."""
        error_str = str(error).lower()
        
        if "model" in error_str and ("unavailable" in error_str or "not found" in error_str):
            return ErrorType.MODEL_UNAVAILABLE
        elif "timeout" in error_str:
            return ErrorType.MODEL_TIMEOUT
        elif "memory" in error_str or "oom" in error_str:
            return ErrorType.MEMORY_EXHAUSTION
        elif "stream" in error_str or "interrupt" in error_str:
            return ErrorType.STREAMING_INTERRUPTION
        elif "connection" in error_str or "network" in error_str:
            return ErrorType.CONNECTION_FAILURE
        else:
            return ErrorType.PERFORMANCE_DEGRADATION
    
    def _determine_overall_health_status(
        self,
        memory_status,
        available_models: List[str],
        performance_issues: List[PerformanceIssue]
    ) -> SystemHealthStatus:
        """Determine overall system health status."""
        
        # Check memory pressure
        if memory_status.pressure_level == MemoryPressureLevel.EMERGENCY:
            return SystemHealthStatus.EMERGENCY
        elif memory_status.pressure_level == MemoryPressureLevel.CRITICAL:
            return SystemHealthStatus.CRITICAL
        
        # Check model availability
        if not available_models:
            return SystemHealthStatus.EMERGENCY
        elif len(available_models) < 2:
            return SystemHealthStatus.CRITICAL
        
        # Check performance issues
        critical_issues = [i for i in performance_issues if i.severity == "critical"]
        if len(critical_issues) > 2:
            return SystemHealthStatus.CRITICAL
        elif len(critical_issues) > 0 or len(performance_issues) > 5:
            return SystemHealthStatus.DEGRADED
        
        return SystemHealthStatus.HEALTHY
    
    def _determine_degradation_level(
        self,
        health_status: SystemHealthStatus,
        memory_status,
        unavailable_model_count: int
    ) -> DegradationLevel:
        """Determine appropriate degradation level."""
        
        if health_status == SystemHealthStatus.EMERGENCY:
            return DegradationLevel.EMERGENCY
        elif health_status == SystemHealthStatus.CRITICAL:
            return DegradationLevel.SEVERE
        elif health_status == SystemHealthStatus.DEGRADED:
            if memory_status.pressure_level == MemoryPressureLevel.HIGH:
                return DegradationLevel.SIGNIFICANT
            else:
                return DegradationLevel.MODERATE
        elif unavailable_model_count > 0:
            return DegradationLevel.MINIMAL
        else:
            return DegradationLevel.NONE
    
    async def _generate_health_recommendations(
        self,
        memory_status,
        available_models: List[str],
        unavailable_models: List[str]
    ) -> List[str]:
        """Generate health improvement recommendations."""
        
        recommendations = []
        
        if memory_status.pressure_level in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
            recommendations.append("Consider freeing memory or adding more RAM")
        
        if len(unavailable_models) > len(available_models):
            recommendations.append("Check model availability and restart failed models")
        
        if not available_models:
            recommendations.append("URGENT: No models available - system restart may be required")
        
        return recommendations
    
    async def _get_cached_health_report(self) -> SystemHealthReport:
        """Get cached health report."""
        return SystemHealthReport(
            overall_status=self.current_health_status,
            degradation_level=self.current_degradation_level,
            available_models=[],  # Would be cached
            unavailable_models=[],  # Would be cached
            memory_pressure=MemoryPressureLevel.LOW,  # Would be cached
            performance_issues=[],
            active_recoveries=len(self.active_recoveries)
        )
    
    async def _cleanup_execution(self, execution_id: str, execution_time: float):
        """Cleanup execution tracking."""
        # Update performance statistics
        pass
    
    def _update_degradation_stats(self, response: DegradationResponse):
        """Update degradation statistics."""
        if response.fallback_applied:
            self.degradation_stats["fallback_requests"] += 1
        
        if response.degradation_level == DegradationLevel.EMERGENCY:
            self.degradation_stats["emergency_responses"] += 1
        
        # Update average degradation level
        total_requests = self.degradation_stats["total_requests"]
        current_avg = self.degradation_stats["average_degradation_level"]
        new_level = response.degradation_level.value
        
        self.degradation_stats["average_degradation_level"] = (
            (current_avg * (total_requests - 1) + new_level) / total_requests
        )
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        health_report = await self.assess_system_health()
        
        return {
            "health_report": {
                "overall_status": health_report.overall_status.value,
                "degradation_level": health_report.degradation_level.value,
                "available_models": health_report.available_models,
                "unavailable_models": health_report.unavailable_models,
                "memory_pressure": health_report.memory_pressure.value,
                "active_recoveries": health_report.active_recoveries,
                "recommendations": health_report.recommendations
            },
            "degradation_stats": self.degradation_stats.copy(),
            "component_status": {
                "error_recovery": "active",
                "model_availability": "active",
                "timeout_performance": "active",
                "memory_exhaustion": "active",
                "streaming_interruption": "active"
            }
        }


# Global graceful degradation coordinator instance
graceful_degradation_coordinator = GracefulDegradationCoordinator()