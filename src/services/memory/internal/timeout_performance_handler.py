"""
Timeout and Performance Degradation Handler

This module handles timeout issues and automatic model switching
for performance problems, ensuring responsive system behavior.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
from contextlib import asynccontextmanager
import psutil

from ...internal..core.types.shared_types import ModelInfo, PerformanceMetrics


class PerformanceIssueType(Enum):
    """Types of performance issues."""
    TIMEOUT = "timeout"
    SLOW_RESPONSE = "slow_response"
    HIGH_CPU_USAGE = "high_cpu_usage"
    HIGH_MEMORY_USAGE = "high_memory_usage"
    HIGH_LATENCY = "high_latency"
    THROUGHPUT_DEGRADATION = "throughput_degradation"


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    unit: str
    check_interval: float = 1.0


@dataclass
class PerformanceIssue:
    """Detected performance issue."""
    issue_type: PerformanceIssueType
    model_id: str
    current_value: float
    threshold_value: float
    severity: str  # "warning" or "critical"
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeoutConfig:
    """Timeout configuration for different operations."""
    model_loading: float = 30.0
    inference: float = 15.0
    streaming_chunk: float = 5.0
    health_check: float = 3.0
    fallback_switch: float = 2.0


class TimeoutPerformanceHandler:
    """
    Handles timeout issues and performance degradation with
    automatic model switching and optimization adjustments.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Timeout configurations
        self.timeout_config = TimeoutConfig()
        
        # Performance thresholds
        self.performance_thresholds = {
            "response_time": PerformanceThreshold(
                metric_name="response_time",
                warning_threshold=10.0,
                critical_threshold=20.0,
                unit="seconds"
            ),
            "cpu_usage": PerformanceThreshold(
                metric_name="cpu_usage",
                warning_threshold=70.0,
                critical_threshold=85.0,
                unit="percent"
            ),
            "memory_usage": PerformanceThreshold(
                metric_name="memory_usage",
                warning_threshold=75.0,
                critical_threshold=90.0,
                unit="percent"
            ),
            "gpu_memory": PerformanceThreshold(
                metric_name="gpu_memory",
                warning_threshold=80.0,
                critical_threshold=95.0,
                unit="percent"
            ),
            "throughput": PerformanceThreshold(
                metric_name="throughput",
                warning_threshold=0.5,  # tokens per second
                critical_threshold=0.1,
                unit="tokens/sec"
            )
        }
        
        # Performance history for trend analysis
        self.performance_history: Dict[str, List[PerformanceMetrics]] = {}
        self.history_max_size = 100
        
        # Model performance baselines
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        
        # Active performance issues
        self.active_issues: Dict[str, List[PerformanceIssue]] = {}
        
        # Model switching history
        self.switch_history: List[Dict[str, Any]] = []
        
        # Performance optimization settings
        self.optimization_settings = {
            "auto_switch_enabled": True,
            "performance_monitoring_enabled": True,
            "adaptive_timeouts": True,
            "resource_based_switching": True
        }
    
    @asynccontextmanager
    async def timeout_context(
        self,
        operation_type: str,
        model_id: Optional[str] = None,
        custom_timeout: Optional[float] = None
    ):
        """
        Context manager for timeout handling with automatic fallback.
        """
        # Determine timeout value
        timeout_map = {
            "model_loading": self.timeout_config.model_loading,
            "inference": self.timeout_config.inference,
            "streaming": self.timeout_config.streaming_chunk,
            "health_check": self.timeout_config.health_check,
            "fallback_switch": self.timeout_config.fallback_switch
        }
        
        timeout = custom_timeout or timeout_map.get(operation_type, 10.0)
        
        # Adaptive timeout based on model performance history
        if model_id and self.optimization_settings["adaptive_timeouts"]:
            timeout = await self._calculate_adaptive_timeout(
                model_id, operation_type, timeout
            )
        
        start_time = time.time()
        
        try:
            async with asyncio.timeout(timeout):
                yield timeout
                
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            
            self.logger.warning(
                f"Timeout occurred for {operation_type} "
                f"(model: {model_id}, timeout: {timeout}s, elapsed: {elapsed_time:.2f}s)"
            )
            
            # Record timeout issue
            if model_id:
                await self._record_performance_issue(
                    PerformanceIssue(
                        issue_type=PerformanceIssueType.TIMEOUT,
                        model_id=model_id,
                        current_value=elapsed_time,
                        threshold_value=timeout,
                        severity="critical",
                        context={"operation_type": operation_type}
                    )
                )
            
            # Re-raise timeout error for handling by caller
            raise
    
    async def monitor_performance(
        self,
        model_id: str,
        operation_type: str,
        start_time: float,
        end_time: Optional[float] = None
    ) -> PerformanceMetrics:
        """
        Monitor and record performance metrics for an operation.
        """
        if end_time is None:
            end_time = time.time()
        
        try:
            # Calculate basic metrics
            response_time = end_time - start_time
            
            # Get system resource usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Get GPU metrics if available
            gpu_usage = None
            gpu_memory = None
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_usage = gpu.load * 100
                    gpu_memory = gpu.memoryUtil * 100
            except ImportError:
                pass
            
            # Create performance metrics
            metrics = PerformanceMetrics(
                response_time=response_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                gpu_memory_usage=gpu_memory,
                cache_hit_rate=0.0,  # Would be calculated by cache manager
                user_satisfaction_score=None,
                model_efficiency=await self._calculate_model_efficiency(
                    model_id, response_time
                ),
                content_relevance_score=0.0,  # Would be calculated by content optimizer
                cuda_acceleration_gain=None
            )
            
            # Record metrics in history
            await self._record_performance_metrics(model_id, metrics)
            
            # Check for performance issues
            await self._check_performance_thresholds(model_id, metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {str(e)}")
            # Return minimal metrics
            return PerformanceMetrics(
                response_time=end_time - start_time,
                cpu_usage=0.0,
                memory_usage=0.0,
                cache_hit_rate=0.0,
                model_efficiency=0.0,
                content_relevance_score=0.0
            )
    
    async def handle_performance_degradation(
        self,
        model_id: str,
        issue: PerformanceIssue
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Handle performance degradation by switching models or adjusting settings.
        
        Returns:
            Tuple of (switched, new_model_id, optimization_adjustments)
        """
        try:
            self.logger.warning(
                f"Handling performance degradation for {model_id}: "
                f"{issue.issue_type.value} ({issue.current_value} > {issue.threshold_value})"
            )
            
            # Determine if model switching is needed
            should_switch = await self._should_switch_model(model_id, issue)
            
            if should_switch and self.optimization_settings["auto_switch_enabled"]:
                # Find better performing model
                new_model_id = await self._find_better_performing_model(
                    model_id, issue
                )
                
                if new_model_id:
                    # Record the switch
                    await self._record_model_switch(
                        model_id, new_model_id, issue
                    )
                    
                    self.logger.info(
                        f"Switched from {model_id} to {new_model_id} "
                        f"due to {issue.issue_type.value}"
                    )
                    
                    return True, new_model_id, None
            
            # If not switching, try optimization adjustments
            optimizations = await self._generate_optimization_adjustments(
                model_id, issue
            )
            
            if optimizations:
                self.logger.info(
                    f"Applied optimizations for {model_id}: {list(optimizations.keys())}"
                )
                return False, None, optimizations
            
            return False, None, None
            
        except Exception as e:
            self.logger.error(f"Performance degradation handling failed: {str(e)}")
            return False, None, None
    
    async def get_performance_recommendations(
        self,
        model_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get performance optimization recommendations for a model.
        """
        try:
            recommendations = []
            
            # Get recent performance history
            recent_metrics = await self._get_recent_performance_metrics(model_id)
            if not recent_metrics:
                return recommendations
            
            # Analyze trends
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            avg_cpu_usage = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory_usage = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            
            # Generate recommendations based on metrics
            if avg_response_time > self.performance_thresholds["response_time"].warning_threshold:
                recommendations.append({
                    "type": "timeout_adjustment",
                    "description": "Consider increasing timeout values or switching to a faster model",
                    "priority": "high" if avg_response_time > self.performance_thresholds["response_time"].critical_threshold else "medium",
                    "current_value": avg_response_time,
                    "threshold": self.performance_thresholds["response_time"].warning_threshold
                })
            
            if avg_cpu_usage > self.performance_thresholds["cpu_usage"].warning_threshold:
                recommendations.append({
                    "type": "cpu_optimization",
                    "description": "High CPU usage detected. Consider enabling GPU acceleration or using a lighter model",
                    "priority": "high" if avg_cpu_usage > self.performance_thresholds["cpu_usage"].critical_threshold else "medium",
                    "current_value": avg_cpu_usage,
                    "threshold": self.performance_thresholds["cpu_usage"].warning_threshold
                })
            
            if avg_memory_usage > self.performance_thresholds["memory_usage"].warning_threshold:
                recommendations.append({
                    "type": "memory_optimization",
                    "description": "High memory usage detected. Consider using model quantization or smaller batch sizes",
                    "priority": "high" if avg_memory_usage > self.performance_thresholds["memory_usage"].critical_threshold else "medium",
                    "current_value": avg_memory_usage,
                    "threshold": self.performance_thresholds["memory_usage"].warning_threshold
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance recommendations: {str(e)}")
            return []
    
    # Helper methods
    
    async def _calculate_adaptive_timeout(
        self,
        model_id: str,
        operation_type: str,
        base_timeout: float
    ) -> float:
        """Calculate adaptive timeout based on model performance history."""
        try:
            recent_metrics = await self._get_recent_performance_metrics(model_id, limit=10)
            if not recent_metrics:
                return base_timeout
            
            # Calculate average response time
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            
            # Adjust timeout based on historical performance
            # Add 50% buffer to average response time, but cap at 3x base timeout
            adaptive_timeout = min(avg_response_time * 1.5, base_timeout * 3)
            
            # Ensure minimum timeout
            return max(adaptive_timeout, base_timeout * 0.5)
            
        except Exception as e:
            self.logger.error(f"Adaptive timeout calculation failed: {str(e)}")
            return base_timeout
    
    async def _record_performance_issue(self, issue: PerformanceIssue):
        """Record a performance issue."""
        if issue.model_id not in self.active_issues:
            self.active_issues[issue.model_id] = []
        
        self.active_issues[issue.model_id].append(issue)
        
        # Keep only recent issues (last 50)
        if len(self.active_issues[issue.model_id]) > 50:
            self.active_issues[issue.model_id] = self.active_issues[issue.model_id][-50:]
    
    async def _record_performance_metrics(
        self,
        model_id: str,
        metrics: PerformanceMetrics
    ):
        """Record performance metrics in history."""
        if model_id not in self.performance_history:
            self.performance_history[model_id] = []
        
        self.performance_history[model_id].append(metrics)
        
        # Keep only recent metrics
        if len(self.performance_history[model_id]) > self.history_max_size:
            self.performance_history[model_id] = self.performance_history[model_id][-self.history_max_size:]
    
    async def _check_performance_thresholds(
        self,
        model_id: str,
        metrics: PerformanceMetrics
    ):
        """Check if performance metrics exceed thresholds."""
        checks = [
            ("response_time", metrics.response_time),
            ("cpu_usage", metrics.cpu_usage),
            ("memory_usage", metrics.memory_usage)
        ]
        
        if metrics.gpu_memory_usage is not None:
            checks.append(("gpu_memory", metrics.gpu_memory_usage))
        
        for metric_name, value in checks:
            threshold = self.performance_thresholds.get(metric_name)
            if not threshold:
                continue
            
            severity = None
            if value > threshold.critical_threshold:
                severity = "critical"
            elif value > threshold.warning_threshold:
                severity = "warning"
            
            if severity:
                issue_type_map = {
                    "response_time": PerformanceIssueType.SLOW_RESPONSE,
                    "cpu_usage": PerformanceIssueType.HIGH_CPU_USAGE,
                    "memory_usage": PerformanceIssueType.HIGH_MEMORY_USAGE,
                    "gpu_memory": PerformanceIssueType.HIGH_MEMORY_USAGE
                }
                
                issue = PerformanceIssue(
                    issue_type=issue_type_map.get(metric_name, PerformanceIssueType.SLOW_RESPONSE),
                    model_id=model_id,
                    current_value=value,
                    threshold_value=threshold.warning_threshold if severity == "warning" else threshold.critical_threshold,
                    severity=severity
                )
                
                await self._record_performance_issue(issue)
                
                # Handle critical issues immediately
                if severity == "critical":
                    await self.handle_performance_degradation(model_id, issue)
    
    async def _calculate_model_efficiency(
        self,
        model_id: str,
        response_time: float
    ) -> float:
        """Calculate model efficiency score."""
        # Get baseline performance
        baseline = self.performance_baselines.get(model_id, {}).get("response_time", 5.0)
        
        # Calculate efficiency as inverse of response time ratio
        efficiency = baseline / max(response_time, 0.1)
        return min(efficiency, 1.0)
    
    async def _should_switch_model(
        self,
        model_id: str,
        issue: PerformanceIssue
    ) -> bool:
        """Determine if model switching is warranted."""
        # Check if issue is critical
        if issue.severity == "critical":
            return True
        
        # Check if there have been multiple recent issues
        recent_issues = [
            i for i in self.active_issues.get(model_id, [])
            if time.time() - i.timestamp < 300  # Last 5 minutes
        ]
        
        if len(recent_issues) >= 3:
            return True
        
        return False
    
    async def _find_better_performing_model(
        self,
        current_model_id: str,
        issue: PerformanceIssue
    ) -> Optional[str]:
        """Find a better performing model for the given issue."""
        # This would integrate with the model availability handler
        # For now, return a simple fallback
        fallback_models = [
            "tinyllama-1.1b-chat",
            "gpt-3.5-turbo",
            "claude-3-haiku"
        ]
        
        for model in fallback_models:
            if model != current_model_id:
                return model
        
        return None
    
    async def _record_model_switch(
        self,
        from_model: str,
        to_model: str,
        issue: PerformanceIssue
    ):
        """Record model switch event."""
        switch_record = {
            "timestamp": time.time(),
            "from_model": from_model,
            "to_model": to_model,
            "reason": issue.issue_type.value,
            "issue_severity": issue.severity,
            "trigger_value": issue.current_value,
            "threshold": issue.threshold_value
        }
        
        self.switch_history.append(switch_record)
        
        # Keep only recent switches
        if len(self.switch_history) > 100:
            self.switch_history = self.switch_history[-100:]
    
    async def _generate_optimization_adjustments(
        self,
        model_id: str,
        issue: PerformanceIssue
    ) -> Optional[Dict[str, Any]]:
        """Generate optimization adjustments for performance issues."""
        adjustments = {}
        
        if issue.issue_type == PerformanceIssueType.HIGH_CPU_USAGE:
            adjustments.update({
                "enable_gpu_acceleration": True,
                "reduce_batch_size": True,
                "enable_model_quantization": True
            })
        
        elif issue.issue_type == PerformanceIssueType.HIGH_MEMORY_USAGE:
            adjustments.update({
                "reduce_context_length": True,
                "enable_memory_optimization": True,
                "clear_cache": True
            })
        
        elif issue.issue_type == PerformanceIssueType.SLOW_RESPONSE:
            adjustments.update({
                "increase_timeout": True,
                "enable_response_streaming": True,
                "reduce_response_complexity": True
            })
        
        return adjustments if adjustments else None
    
    async def _get_recent_performance_metrics(
        self,
        model_id: str,
        limit: int = 20
    ) -> List[PerformanceMetrics]:
        """Get recent performance metrics for a model."""
        metrics = self.performance_history.get(model_id, [])
        return metrics[-limit:] if metrics else []


# Global timeout and performance handler instance
timeout_performance_handler = TimeoutPerformanceHandler()