"""
Response Performance Metrics Collection System

This module provides comprehensive performance tracking and analytics for the
intelligent response optimization system, including detailed metrics collection,
real-time monitoring, and performance analysis capabilities.
"""

import asyncio
import time
import psutil
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, AsyncIterator
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    GPU_USAGE = "gpu_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    USER_SATISFACTION = "user_satisfaction"
    MODEL_EFFICIENCY = "model_efficiency"
    CONTENT_RELEVANCE = "content_relevance"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"


class OptimizationType(Enum):
    """Types of response optimizations"""
    CONTENT_OPTIMIZATION = "content_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    MODEL_ROUTING = "model_routing"
    PROGRESSIVE_STREAMING = "progressive_streaming"
    GPU_ACCELERATION = "gpu_acceleration"
    RESOURCE_ALLOCATION = "resource_allocation"


@dataclass
class ResponsePerformanceMetrics:
    """Comprehensive performance metrics for a single response"""
    response_id: str
    timestamp: datetime
    query: str
    model_used: str
    response_time: float
    cpu_usage: float
    memory_usage: int
    gpu_usage: Optional[float] = None
    gpu_memory_usage: Optional[int] = None
    cache_hit_rate: float = 0.0
    user_satisfaction_score: Optional[float] = None
    model_efficiency: float = 0.0
    content_relevance_score: float = 0.0
    cuda_acceleration_gain: Optional[float] = None
    optimizations_applied: List[OptimizationType] = None
    response_size: int = 0
    streaming_chunks: int = 0
    error_occurred: bool = False
    error_type: Optional[str] = None
    bottlenecks: List[str] = None
    
    def __post_init__(self):
        if self.optimizations_applied is None:
            self.optimizations_applied = []
        if self.bottlenecks is None:
            self.bottlenecks = []


@dataclass
class AggregatedMetrics:
    """Aggregated performance metrics over a time period"""
    period_start: datetime
    period_end: datetime
    total_responses: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_gpu_usage: Optional[float]
    cache_hit_rate: float
    avg_user_satisfaction: Optional[float]
    error_rate: float
    throughput: float
    most_used_models: Dict[str, int]
    optimization_effectiveness: Dict[OptimizationType, float]
    identified_bottlenecks: Dict[str, int]


@dataclass
class BottleneckAnalysis:
    """Analysis of performance bottlenecks"""
    bottleneck_type: str
    frequency: int
    avg_impact: float
    affected_models: List[str]
    suggested_optimizations: List[str]
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


class ResponsePerformanceCollector:
    """Collects and manages response performance metrics"""
    
    def __init__(self, max_metrics_history: int = 10000):
        self.max_metrics_history = max_metrics_history
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        self.active_responses: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Real-time metrics tracking
        self.current_metrics = {
            'active_responses': 0,
            'avg_response_time_1min': 0.0,
            'cpu_usage_current': 0.0,
            'memory_usage_current': 0,
            'cache_hit_rate_1min': 0.0,
            'throughput_1min': 0.0,
            'error_rate_1min': 0.0
        }
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def start_response_tracking(self, response_id: str, query: str, model_used: str) -> None:
        """Start tracking performance for a response"""
        with self.lock:
            self.active_responses[response_id] = {
                'start_time': time.time(),
                'query': query,
                'model_used': model_used,
                'cpu_start': psutil.cpu_percent(),
                'memory_start': psutil.virtual_memory().used,
                'optimizations_applied': [],
                'bottlenecks': [],
                'streaming_chunks': 0,
                'error_occurred': False,
                'error_type': None
            }
            self.current_metrics['active_responses'] += 1
    
    def record_optimization_applied(self, response_id: str, optimization: OptimizationType) -> None:
        """Record that an optimization was applied to a response"""
        with self.lock:
            if response_id in self.active_responses:
                self.active_responses[response_id]['optimizations_applied'].append(optimization)
    
    def record_bottleneck(self, response_id: str, bottleneck: str) -> None:
        """Record a performance bottleneck for a response"""
        with self.lock:
            if response_id in self.active_responses:
                self.active_responses[response_id]['bottlenecks'].append(bottleneck)
    
    def record_streaming_chunk(self, response_id: str) -> None:
        """Record a streaming chunk delivery"""
        with self.lock:
            if response_id in self.active_responses:
                self.active_responses[response_id]['streaming_chunks'] += 1
    
    def record_error(self, response_id: str, error_type: str) -> None:
        """Record an error for a response"""
        with self.lock:
            if response_id in self.active_responses:
                self.active_responses[response_id]['error_occurred'] = True
                self.active_responses[response_id]['error_type'] = error_type
    
    def finish_response_tracking(
        self, 
        response_id: str, 
        response_size: int = 0,
        cache_hit_rate: float = 0.0,
        model_efficiency: float = 0.0,
        content_relevance_score: float = 0.0,
        cuda_acceleration_gain: Optional[float] = None,
        gpu_usage: Optional[float] = None,
        gpu_memory_usage: Optional[int] = None
    ) -> ResponsePerformanceMetrics:
        """Finish tracking and create performance metrics"""
        with self.lock:
            if response_id not in self.active_responses:
                logger.warning(f"Response {response_id} not found in active tracking")
                return None
            
            tracking_data = self.active_responses.pop(response_id)
            end_time = time.time()
            
            # Calculate metrics
            response_time = end_time - tracking_data['start_time']
            cpu_usage = psutil.cpu_percent() - tracking_data['cpu_start']
            memory_usage = psutil.virtual_memory().used - tracking_data['memory_start']
            
            metrics = ResponsePerformanceMetrics(
                response_id=response_id,
                timestamp=datetime.now(),
                query=tracking_data['query'],
                model_used=tracking_data['model_used'],
                response_time=response_time,
                cpu_usage=max(0, cpu_usage),  # Ensure non-negative
                memory_usage=max(0, memory_usage),  # Ensure non-negative
                gpu_usage=gpu_usage,
                gpu_memory_usage=gpu_memory_usage,
                cache_hit_rate=cache_hit_rate,
                model_efficiency=model_efficiency,
                content_relevance_score=content_relevance_score,
                cuda_acceleration_gain=cuda_acceleration_gain,
                optimizations_applied=tracking_data['optimizations_applied'],
                response_size=response_size,
                streaming_chunks=tracking_data['streaming_chunks'],
                error_occurred=tracking_data['error_occurred'],
                error_type=tracking_data['error_type'],
                bottlenecks=tracking_data['bottlenecks']
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            self.current_metrics['active_responses'] -= 1
            
            # Update real-time metrics
            self._update_realtime_metrics()
            
            return metrics
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[ResponsePerformanceMetrics]:
        """Get historical performance metrics"""
        with self.lock:
            if limit:
                return list(self.metrics_history)[-limit:]
            return list(self.metrics_history)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        with self.lock:
            return self.current_metrics.copy()
    
    def get_aggregated_metrics(self, time_period: timedelta) -> AggregatedMetrics:
        """Get aggregated metrics for a time period"""
        cutoff_time = datetime.now() - time_period
        
        with self.lock:
            relevant_metrics = [
                m for m in self.metrics_history 
                if m.timestamp >= cutoff_time
            ]
        
        if not relevant_metrics:
            return AggregatedMetrics(
                period_start=cutoff_time,
                period_end=datetime.now(),
                total_responses=0,
                avg_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                avg_cpu_usage=0.0,
                avg_memory_usage=0.0,
                avg_gpu_usage=None,
                cache_hit_rate=0.0,
                avg_user_satisfaction=None,
                error_rate=0.0,
                throughput=0.0,
                most_used_models={},
                optimization_effectiveness={},
                identified_bottlenecks={}
            )
        
        # Calculate aggregated metrics
        response_times = [m.response_time for m in relevant_metrics]
        cpu_usages = [m.cpu_usage for m in relevant_metrics]
        memory_usages = [m.memory_usage for m in relevant_metrics]
        gpu_usages = [m.gpu_usage for m in relevant_metrics if m.gpu_usage is not None]
        cache_hit_rates = [m.cache_hit_rate for m in relevant_metrics]
        user_satisfactions = [m.user_satisfaction_score for m in relevant_metrics if m.user_satisfaction_score is not None]
        
        # Model usage statistics
        model_counts = defaultdict(int)
        for m in relevant_metrics:
            model_counts[m.model_used] += 1
        
        # Optimization effectiveness
        optimization_effectiveness = {}
        for opt_type in OptimizationType:
            with_opt = [m for m in relevant_metrics if opt_type in m.optimizations_applied]
            without_opt = [m for m in relevant_metrics if opt_type not in m.optimizations_applied]
            
            if with_opt and without_opt:
                avg_with = statistics.mean([m.response_time for m in with_opt])
                avg_without = statistics.mean([m.response_time for m in without_opt])
                effectiveness = max(0, (avg_without - avg_with) / avg_without * 100)
                optimization_effectiveness[opt_type] = effectiveness
        
        # Bottleneck analysis
        bottleneck_counts = defaultdict(int)
        for m in relevant_metrics:
            for bottleneck in m.bottlenecks:
                bottleneck_counts[bottleneck] += 1
        
        return AggregatedMetrics(
            period_start=cutoff_time,
            period_end=datetime.now(),
            total_responses=len(relevant_metrics),
            avg_response_time=statistics.mean(response_times),
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else response_times[0],
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 1 else response_times[0],
            avg_cpu_usage=statistics.mean(cpu_usages),
            avg_memory_usage=statistics.mean(memory_usages),
            avg_gpu_usage=statistics.mean(gpu_usages) if gpu_usages else None,
            cache_hit_rate=statistics.mean(cache_hit_rates),
            avg_user_satisfaction=statistics.mean(user_satisfactions) if user_satisfactions else None,
            error_rate=len([m for m in relevant_metrics if m.error_occurred]) / len(relevant_metrics) * 100,
            throughput=len(relevant_metrics) / time_period.total_seconds() * 60,  # responses per minute
            most_used_models=dict(model_counts),
            optimization_effectiveness=optimization_effectiveness,
            identified_bottlenecks=dict(bottleneck_counts)
        )
    
    def analyze_bottlenecks(self, time_period: timedelta) -> List[BottleneckAnalysis]:
        """Analyze performance bottlenecks"""
        cutoff_time = datetime.now() - time_period
        
        with self.lock:
            relevant_metrics = [
                m for m in self.metrics_history 
                if m.timestamp >= cutoff_time
            ]
        
        bottleneck_analysis = defaultdict(lambda: {
            'frequency': 0,
            'total_impact': 0.0,
            'affected_models': set(),
            'response_times': []
        })
        
        # Analyze each bottleneck
        for metrics in relevant_metrics:
            for bottleneck in metrics.bottlenecks:
                analysis = bottleneck_analysis[bottleneck]
                analysis['frequency'] += 1
                analysis['total_impact'] += metrics.response_time
                analysis['affected_models'].add(metrics.model_used)
                analysis['response_times'].append(metrics.response_time)
        
        # Create bottleneck analysis objects
        analyses = []
        for bottleneck_type, data in bottleneck_analysis.items():
            avg_impact = data['total_impact'] / data['frequency']
            
            # Determine severity
            if avg_impact > 10.0:  # > 10 seconds
                severity = "CRITICAL"
            elif avg_impact > 5.0:  # > 5 seconds
                severity = "HIGH"
            elif avg_impact > 2.0:  # > 2 seconds
                severity = "MEDIUM"
            else:
                severity = "LOW"
            
            # Generate optimization suggestions
            suggestions = self._generate_optimization_suggestions(bottleneck_type, avg_impact)
            
            analyses.append(BottleneckAnalysis(
                bottleneck_type=bottleneck_type,
                frequency=data['frequency'],
                avg_impact=avg_impact,
                affected_models=list(data['affected_models']),
                suggested_optimizations=suggestions,
                severity=severity
            ))
        
        # Sort by severity and frequency
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        analyses.sort(key=lambda x: (severity_order[x.severity], x.frequency), reverse=True)
        
        return analyses
    
    def _generate_optimization_suggestions(self, bottleneck_type: str, avg_impact: float) -> List[str]:
        """Generate optimization suggestions for a bottleneck"""
        suggestions = []
        
        if "model_loading" in bottleneck_type.lower():
            suggestions.extend([
                "Enable model preloading and caching",
                "Use model quantization to reduce loading time",
                "Implement model connection pooling"
            ])
        
        if "memory" in bottleneck_type.lower():
            suggestions.extend([
                "Increase system memory allocation",
                "Implement more aggressive garbage collection",
                "Use memory-efficient model variants"
            ])
        
        if "gpu" in bottleneck_type.lower():
            suggestions.extend([
                "Optimize GPU memory allocation",
                "Implement GPU batch processing",
                "Use CUDA memory pooling"
            ])
        
        if "cache" in bottleneck_type.lower():
            suggestions.extend([
                "Increase cache size limits",
                "Optimize cache eviction policies",
                "Implement cache warming strategies"
            ])
        
        if "network" in bottleneck_type.lower():
            suggestions.extend([
                "Implement request batching",
                "Use connection pooling",
                "Optimize network timeouts"
            ])
        
        return suggestions
    
    def _update_realtime_metrics(self) -> None:
        """Update real-time metrics"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Get recent metrics
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= one_minute_ago
        ]
        
        if recent_metrics:
            self.current_metrics['avg_response_time_1min'] = statistics.mean([m.response_time for m in recent_metrics])
            self.current_metrics['cache_hit_rate_1min'] = statistics.mean([m.cache_hit_rate for m in recent_metrics])
            self.current_metrics['throughput_1min'] = len(recent_metrics)
            self.current_metrics['error_rate_1min'] = len([m for m in recent_metrics if m.error_occurred]) / len(recent_metrics) * 100
        
        # Current system metrics
        self.current_metrics['cpu_usage_current'] = psutil.cpu_percent()
        self.current_metrics['memory_usage_current'] = psutil.virtual_memory().used
    
    def _start_background_monitoring(self) -> None:
        """Start background monitoring thread"""
        def monitor():
            while True:
                try:
                    self._update_realtime_metrics()
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    logger.error(f"Error in background monitoring: {e}")
                    time.sleep(30)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def export_metrics(self, filepath: str, time_period: Optional[timedelta] = None) -> None:
        """Export metrics to JSON file"""
        if time_period:
            cutoff_time = datetime.now() - time_period
            metrics_to_export = [
                m for m in self.metrics_history 
                if m.timestamp >= cutoff_time
            ]
        else:
            metrics_to_export = list(self.metrics_history)
        
        # Convert to serializable format
        export_data = []
        for metrics in metrics_to_export:
            data = asdict(metrics)
            data['timestamp'] = metrics.timestamp.isoformat()
            data['optimizations_applied'] = [opt.value for opt in metrics.optimizations_applied]
            export_data.append(data)
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(export_data)} metrics to {filepath}")


# Global performance collector instance
performance_collector = ResponsePerformanceCollector()