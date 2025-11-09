"""
Extension Performance Monitor

Monitors and reports on extension performance metrics.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .cache_manager import ExtensionCacheManager, CacheStats
from .resource_optimizer import ExtensionResourceOptimizer, ResourceUsage
from .scaling_manager import ExtensionScalingManager, ScalingMetrics


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for an extension."""
    extension_name: str
    timestamp: float
    
    # Loading metrics
    load_time_seconds: float
    initialization_time_seconds: float
    startup_memory_mb: float
    
    # Runtime metrics
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_io_mb_per_sec: float
    network_io_mb_per_sec: float
    
    # Request metrics
    requests_per_second: float
    average_response_time_ms: float
    error_rate_percent: float
    
    # Cache metrics
    cache_hit_rate: float
    cache_size_mb: float
    
    # Scaling metrics
    active_instances: int
    scaling_events: int
    
    # Custom metrics
    custom_metrics: Dict[str, float]


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations."""
    extension_name: str
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: float


@dataclass
class PerformanceSummary:
    """Performance summary for an extension over a time period."""
    extension_name: str
    time_period_hours: float
    
    # Aggregated metrics
    avg_cpu_usage: float
    max_cpu_usage: float
    avg_memory_usage: float
    max_memory_usage: float
    total_requests: int
    avg_response_time: float
    total_errors: int
    
    # Performance scores (0-100)
    performance_score: float
    reliability_score: float
    efficiency_score: float
    
    # Recommendations
    recommendations: List[str]


class ExtensionPerformanceMonitor:
    """
    Monitors and reports on extension performance metrics.
    
    Features:
    - Real-time performance monitoring
    - Performance alerting and thresholds
    - Historical performance analysis
    - Performance scoring and recommendations
    - Integration with other performance components
    """
    
    def __init__(
        self,
        cache_manager: ExtensionCacheManager,
        resource_optimizer: ExtensionResourceOptimizer,
        scaling_manager: ExtensionScalingManager,
        monitoring_interval: float = 30.0,
        alert_check_interval: float = 60.0,
        metrics_retention_hours: float = 168.0  # 1 week
    ):
        self.cache_manager = cache_manager
        self.resource_optimizer = resource_optimizer
        self.scaling_manager = scaling_manager
        self.monitoring_interval = monitoring_interval
        self.alert_check_interval = alert_check_interval
        self.metrics_retention_hours = metrics_retention_hours
        
        self._performance_metrics: Dict[str, List[PerformanceMetrics]] = {}
        self._performance_thresholds: Dict[str, Dict[str, float]] = {}
        self._active_alerts: Dict[str, List[PerformanceAlert]] = {}
        self._custom_metric_collectors: Dict[str, callable] = {}
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start the performance monitor."""
        if self._running:
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._alert_task = asyncio.create_task(self._alert_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Extension performance monitor started")
    
    async def stop(self) -> None:
        """Stop the performance monitor."""
        self._running = False
        
        for task in [self._monitoring_task, self._alert_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.logger.info("Extension performance monitor stopped")
    
    async def configure_thresholds(
        self,
        extension_name: str,
        thresholds: Dict[str, float]
    ) -> None:
        """Configure performance thresholds for an extension."""
        self._performance_thresholds[extension_name] = thresholds
        self.logger.info(f"Configured performance thresholds for {extension_name}")
    
    async def register_custom_metric_collector(
        self,
        extension_name: str,
        collector: callable
    ) -> None:
        """Register a custom metric collector for an extension."""
        self._custom_metric_collectors[extension_name] = collector
        self.logger.info(f"Registered custom metric collector for {extension_name}")
    
    async def get_current_metrics(
        self,
        extension_name: str
    ) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics for an extension."""
        metrics_list = self._performance_metrics.get(extension_name, [])
        return metrics_list[-1] if metrics_list else None
    
    async def get_metrics_history(
        self,
        extension_name: str,
        time_window_hours: Optional[float] = None
    ) -> List[PerformanceMetrics]:
        """Get performance metrics history for an extension."""
        metrics_list = self._performance_metrics.get(extension_name, [])
        
        if time_window_hours is None:
            return metrics_list
        
        cutoff_time = time.time() - (time_window_hours * 3600)
        return [m for m in metrics_list if m.timestamp >= cutoff_time]
    
    async def get_performance_summary(
        self,
        extension_name: str,
        time_period_hours: float = 24.0
    ) -> Optional[PerformanceSummary]:
        """Get performance summary for an extension over a time period."""
        metrics = await self.get_metrics_history(extension_name, time_period_hours)
        if not metrics:
            return None
        
        # Calculate aggregated metrics
        cpu_values = [m.cpu_usage_percent for m in metrics]
        memory_values = [m.memory_usage_mb for m in metrics]
        response_times = [m.average_response_time_ms for m in metrics if m.average_response_time_ms > 0]
        
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        max_cpu = max(cpu_values) if cpu_values else 0
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0
        max_memory = max(memory_values) if memory_values else 0
        
        total_requests = sum(m.requests_per_second * self.monitoring_interval for m in metrics)
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        total_errors = sum(m.error_rate_percent * m.requests_per_second * self.monitoring_interval / 100 for m in metrics)
        
        # Calculate performance scores
        performance_score = self._calculate_performance_score(metrics)
        reliability_score = self._calculate_reliability_score(metrics)
        efficiency_score = self._calculate_efficiency_score(metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(extension_name, metrics)
        
        return PerformanceSummary(
            extension_name=extension_name,
            time_period_hours=time_period_hours,
            avg_cpu_usage=avg_cpu,
            max_cpu_usage=max_cpu,
            avg_memory_usage=avg_memory,
            max_memory_usage=max_memory,
            total_requests=int(total_requests),
            avg_response_time=avg_response_time,
            total_errors=int(total_errors),
            performance_score=performance_score,
            reliability_score=reliability_score,
            efficiency_score=efficiency_score,
            recommendations=recommendations
        )
    
    async def get_active_alerts(
        self,
        extension_name: Optional[str] = None
    ) -> List[PerformanceAlert]:
        """Get active performance alerts."""
        if extension_name:
            return self._active_alerts.get(extension_name, [])
        
        all_alerts = []
        for alerts in self._active_alerts.values():
            all_alerts.extend(alerts)
        
        return sorted(all_alerts, key=lambda x: x.timestamp, reverse=True)
    
    async def export_metrics(
        self,
        extension_name: str,
        output_path: Path,
        format: str = "json"
    ) -> None:
        """Export performance metrics to a file."""
        metrics = self._performance_metrics.get(extension_name, [])
        
        if format.lower() == "json":
            data = [asdict(m) for m in metrics]
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        elif format.lower() == "csv":
            import csv
            if metrics:
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=asdict(metrics[0]).keys())
                    writer.writeheader()
                    for metric in metrics:
                        writer.writerow(asdict(metric))
        
        self.logger.info(f"Exported {len(metrics)} metrics for {extension_name} to {output_path}")
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _alert_loop(self) -> None:
        """Background alert checking loop."""
        while self._running:
            try:
                await self._check_performance_alerts()
                await asyncio.sleep(self.alert_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance alert checking error: {e}")
                await asyncio.sleep(self.alert_check_interval)
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for old metrics."""
        while self._running:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _collect_performance_metrics(self) -> None:
        """Collect performance metrics from all sources."""
        current_time = time.time()
        
        # Get list of extensions to monitor
        extensions_to_monitor = set()
        extensions_to_monitor.update(self._performance_thresholds.keys())
        extensions_to_monitor.update(self._custom_metric_collectors.keys())
        
        for extension_name in extensions_to_monitor:
            try:
                # Get resource usage
                resource_usage = await self.resource_optimizer.get_resource_usage(
                    extension_name, time_window=60
                )
                latest_resource = resource_usage[-1] if resource_usage else None
                
                # Get cache stats
                cache_stats = await self.cache_manager.get_stats()
                
                # Get scaling metrics
                scaling_metrics = await self.scaling_manager.get_scaling_metrics(
                    extension_name, time_window=60
                )
                latest_scaling = scaling_metrics[-1] if scaling_metrics else None
                
                # Collect custom metrics
                custom_metrics = {}
                collector = self._custom_metric_collectors.get(extension_name)
                if collector:
                    try:
                        custom_metrics = await collector()
                    except Exception as e:
                        self.logger.warning(f"Custom metric collection failed for {extension_name}: {e}")
                
                # Create performance metrics
                metrics = PerformanceMetrics(
                    extension_name=extension_name,
                    timestamp=current_time,
                    load_time_seconds=0.0,  # Would be tracked during loading
                    initialization_time_seconds=0.0,  # Would be tracked during loading
                    startup_memory_mb=0.0,  # Would be tracked during loading
                    cpu_usage_percent=latest_resource.cpu_percent if latest_resource else 0.0,
                    memory_usage_mb=latest_resource.memory_mb if latest_resource else 0.0,
                    disk_io_mb_per_sec=(latest_resource.disk_read_mb + latest_resource.disk_write_mb) if latest_resource else 0.0,
                    network_io_mb_per_sec=(latest_resource.network_sent_mb + latest_resource.network_recv_mb) if latest_resource else 0.0,
                    requests_per_second=custom_metrics.get('requests_per_second', 0.0),
                    average_response_time_ms=custom_metrics.get('average_response_time_ms', 0.0),
                    error_rate_percent=custom_metrics.get('error_rate_percent', 0.0),
                    cache_hit_rate=cache_stats.hit_rate,
                    cache_size_mb=cache_stats.total_size / (1024 * 1024),
                    active_instances=latest_scaling.active_instances if latest_scaling else 1,
                    scaling_events=0,  # Would be tracked by scaling manager
                    custom_metrics=custom_metrics
                )
                
                # Store metrics
                if extension_name not in self._performance_metrics:
                    self._performance_metrics[extension_name] = []
                
                self._performance_metrics[extension_name].append(metrics)
                
            except Exception as e:
                self.logger.error(f"Failed to collect metrics for {extension_name}: {e}")
    
    async def _check_performance_alerts(self) -> None:
        """Check for performance threshold violations and generate alerts."""
        for extension_name, thresholds in self._performance_thresholds.items():
            try:
                current_metrics = await self.get_current_metrics(extension_name)
                if not current_metrics:
                    continue
                
                # Clear existing alerts for this extension
                self._active_alerts[extension_name] = []
                
                # Check each threshold
                for metric_name, threshold_value in thresholds.items():
                    current_value = self._get_metric_value(current_metrics, metric_name)
                    
                    if current_value > threshold_value:
                        severity = self._determine_alert_severity(
                            current_value, threshold_value, metric_name
                        )
                        
                        alert = PerformanceAlert(
                            extension_name=extension_name,
                            alert_type="threshold_violation",
                            severity=severity,
                            message=f"{metric_name} ({current_value:.2f}) exceeds threshold ({threshold_value:.2f})",
                            metric_name=metric_name,
                            current_value=current_value,
                            threshold_value=threshold_value,
                            timestamp=time.time()
                        )
                        
                        self._active_alerts[extension_name].append(alert)
                        
                        self.logger.warning(f"Performance alert for {extension_name}: {alert.message}")
                
            except Exception as e:
                self.logger.error(f"Alert checking failed for {extension_name}: {e}")
    
    def _get_metric_value(self, metrics: PerformanceMetrics, metric_name: str) -> float:
        """Get a metric value by name."""
        metric_map = {
            'cpu_usage_percent': metrics.cpu_usage_percent,
            'memory_usage_mb': metrics.memory_usage_mb,
            'disk_io_mb_per_sec': metrics.disk_io_mb_per_sec,
            'network_io_mb_per_sec': metrics.network_io_mb_per_sec,
            'average_response_time_ms': metrics.average_response_time_ms,
            'error_rate_percent': metrics.error_rate_percent,
        }
        
        return metric_map.get(metric_name, metrics.custom_metrics.get(metric_name, 0.0))
    
    def _determine_alert_severity(
        self,
        current_value: float,
        threshold_value: float,
        metric_name: str
    ) -> str:
        """Determine alert severity based on how much the threshold is exceeded."""
        ratio = current_value / threshold_value
        
        if ratio >= 2.0:
            return "critical"
        elif ratio >= 1.5:
            return "high"
        elif ratio >= 1.2:
            return "medium"
        else:
            return "low"
    
    def _calculate_performance_score(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate overall performance score (0-100)."""
        if not metrics:
            return 0.0
        
        # Simple scoring based on resource usage
        cpu_scores = [max(0, 100 - m.cpu_usage_percent) for m in metrics]
        memory_scores = [max(0, 100 - min(m.memory_usage_mb / 1024, 100)) for m in metrics]  # Assume 1GB baseline
        response_scores = [max(0, 100 - min(m.average_response_time_ms / 10, 100)) for m in metrics if m.average_response_time_ms > 0]
        
        all_scores = cpu_scores + memory_scores + response_scores
        return sum(all_scores) / len(all_scores) if all_scores else 0.0
    
    def _calculate_reliability_score(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate reliability score based on error rates and uptime."""
        if not metrics:
            return 0.0
        
        error_rates = [m.error_rate_percent for m in metrics]
        avg_error_rate = sum(error_rates) / len(error_rates)
        
        # Score based on error rate (lower is better)
        return max(0, 100 - avg_error_rate * 10)
    
    def _calculate_efficiency_score(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate efficiency score based on resource usage vs performance."""
        if not metrics:
            return 0.0
        
        # Simple efficiency calculation
        efficiency_scores = []
        for m in metrics:
            if m.requests_per_second > 0:
                # Requests per unit of resource
                cpu_efficiency = m.requests_per_second / max(m.cpu_usage_percent, 1)
                memory_efficiency = m.requests_per_second / max(m.memory_usage_mb, 1)
                efficiency_scores.append((cpu_efficiency + memory_efficiency) / 2)
        
        if not efficiency_scores:
            return 50.0  # Neutral score if no request data
        
        # Normalize to 0-100 scale (this would need calibration in practice)
        avg_efficiency = sum(efficiency_scores) / len(efficiency_scores)
        return min(100, avg_efficiency * 10)
    
    def _generate_recommendations(
        self,
        extension_name: str,
        metrics: List[PerformanceMetrics]
    ) -> List[str]:
        """Generate performance recommendations based on metrics."""
        recommendations = []
        
        if not metrics:
            return recommendations
        
        recent_metrics = metrics[-10:]  # Last 10 measurements
        
        # CPU recommendations
        avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
        if avg_cpu > 80:
            recommendations.append("Consider optimizing CPU-intensive operations or scaling horizontally")
        elif avg_cpu < 10:
            recommendations.append("CPU usage is very low - consider reducing allocated resources")
        
        # Memory recommendations
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        memory_trend = recent_metrics[-1].memory_usage_mb - recent_metrics[0].memory_usage_mb
        if memory_trend > 100:  # Growing by more than 100MB
            recommendations.append("Memory usage is increasing - check for memory leaks")
        
        # Response time recommendations
        response_times = [m.average_response_time_ms for m in recent_metrics if m.average_response_time_ms > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time > 1000:  # More than 1 second
                recommendations.append("Response times are high - consider caching or optimization")
        
        # Cache recommendations
        cache_hit_rates = [m.cache_hit_rate for m in recent_metrics]
        if cache_hit_rates:
            avg_hit_rate = sum(cache_hit_rates) / len(cache_hit_rates)
            if avg_hit_rate < 0.5:  # Less than 50% hit rate
                recommendations.append("Cache hit rate is low - review caching strategy")
        
        return recommendations
    
    async def _cleanup_old_metrics(self) -> None:
        """Clean up old performance metrics to prevent memory growth."""
        cutoff_time = time.time() - (self.metrics_retention_hours * 3600)
        
        for extension_name, metrics_list in self._performance_metrics.items():
            original_count = len(metrics_list)
            self._performance_metrics[extension_name] = [
                m for m in metrics_list if m.timestamp >= cutoff_time
            ]
            
            cleaned_count = original_count - len(self._performance_metrics[extension_name])
            if cleaned_count > 0:
                self.logger.debug(f"Cleaned up {cleaned_count} old metrics for {extension_name}")
        
        # Clean up old alerts
        alert_cutoff = time.time() - 86400  # Keep alerts for 24 hours
        for extension_name, alerts in self._active_alerts.items():
            self._active_alerts[extension_name] = [
                a for a in alerts if a.timestamp >= alert_cutoff
            ]