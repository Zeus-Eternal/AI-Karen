"""
Analytics and Monitoring Service for AI Karen Engine

This service provides comprehensive analytics, monitoring, and health checking capabilities
for the AI Karen system, including performance metrics, user interaction tracking,
and system resource monitoring.
"""

import asyncio
import time
import psutil
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque, Counter
import json
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field


class MetricType(str, Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert notification data"""
    id: str
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class UserInteractionEvent(BaseModel):
    """User interaction tracking event"""
    user_id: str
    session_id: Optional[str] = None
    event_type: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SystemResourceMetrics(BaseModel):
    """System resource usage metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime = Field(default_factory=datetime.now)


class PerformanceMetrics(BaseModel):
    """Performance metrics for services"""
    service_name: str
    operation: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricsCollector:
    """Collects and stores metrics data"""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_metric(self, metric: Metric):
        """Record a metric"""
        with self._lock:
            self.metrics.append(metric)
            
            if metric.metric_type == MetricType.COUNTER:
                self.counters[metric.name] += metric.value
            elif metric.metric_type == MetricType.GAUGE:
                self.gauges[metric.name] = metric.value
            elif metric.metric_type == MetricType.HISTOGRAM:
                self.histograms[metric.name].append(metric.value)
            elif metric.metric_type == MetricType.TIMER:
                self.timers[metric.name].append(metric.value)
    
    def get_counter(self, name: str) -> int:
        """Get counter value"""
        return self.counters.get(name, 0)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get gauge value"""
        return self.gauges.get(name)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        values_sorted = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "p50": values_sorted[int(count * 0.5)],
            "p95": values_sorted[int(count * 0.95)],
            "p99": values_sorted[int(count * 0.99)]
        }
    
    def get_recent_metrics(self, minutes: int = 5) -> List[Metric]:
        """Get metrics from the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        with self._lock:
            return [m for m in self.metrics if m.timestamp >= cutoff]


class SystemMonitor:
    """Monitors system resources and performance"""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.is_running = False
        self.metrics_collector = MetricsCollector()
        self._monitor_thread = None
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start system monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.record_metric(
                Metric("system.cpu.percent", cpu_percent, MetricType.GAUGE)
            )
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_collector.record_metric(
                Metric("system.memory.percent", memory.percent, MetricType.GAUGE)
            )
            self.metrics_collector.record_metric(
                Metric("system.memory.used_mb", memory.used / 1024 / 1024, MetricType.GAUGE)
            )
            self.metrics_collector.record_metric(
                Metric("system.memory.available_mb", memory.available / 1024 / 1024, MetricType.GAUGE)
            )
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.metrics_collector.record_metric(
                Metric("system.disk.percent", disk_percent, MetricType.GAUGE)
            )
            self.metrics_collector.record_metric(
                Metric("system.disk.free_gb", disk.free / 1024 / 1024 / 1024, MetricType.GAUGE)
            )
            
            # Network metrics
            network = psutil.net_io_counters()
            self.metrics_collector.record_metric(
                Metric("system.network.bytes_sent", network.bytes_sent, MetricType.COUNTER)
            )
            self.metrics_collector.record_metric(
                Metric("system.network.bytes_recv", network.bytes_recv, MetricType.COUNTER)
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def get_system_metrics(self) -> SystemResourceMetrics:
        """Get current system metrics"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return SystemResourceMetrics(
                cpu_percent=psutil.cpu_percent(),
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=(disk.used / disk.total) * 100,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv
            )
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            raise


class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_functions: Dict[str, callable] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_health_check(self, name: str, check_function: callable):
        """Register a health check function"""
        self.check_functions[name] = check_function
        self.logger.info(f"Registered health check: {name}")
    
    async def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        if name not in self.check_functions:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' not found"
            )
        
        start_time = time.time()
        try:
            check_function = self.check_functions[name]
            if asyncio.iscoroutinefunction(check_function):
                result = await check_function()
            else:
                result = check_function()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if isinstance(result, HealthCheck):
                result.response_time = response_time
                health_check = result
            else:
                health_check = HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message="OK",
                    response_time=response_time
                )
            
            self.health_checks[name] = health_check
            return health_check
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            health_check = HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time=response_time
            )
            self.health_checks[name] = health_check
            self.logger.error(f"Health check '{name}' failed: {e}")
            return health_check
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        results = {}
        for name in self.check_functions:
            results[name] = await self.run_health_check(name)
        return results
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.health_checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self.health_checks.values()]
        
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, max_alerts: int = 1000):
        self.alerts: deque = deque(maxlen=max_alerts)
        self.alert_handlers: List[callable] = []
        self.thresholds: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def add_alert_handler(self, handler: callable):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    def set_threshold(self, metric_name: str, threshold_value: float, 
                     level: AlertLevel = AlertLevel.WARNING, 
                     comparison: str = "greater_than"):
        """Set alert threshold for a metric"""
        self.thresholds[metric_name] = {
            "value": threshold_value,
            "level": level,
            "comparison": comparison
        }
    
    def create_alert(self, level: AlertLevel, message: str, source: str, 
                    metadata: Dict[str, Any] = None) -> Alert:
        """Create and process an alert"""
        alert = Alert(
            id=f"{source}_{int(time.time())}",
            level=level,
            message=message,
            source=source,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(alert))
                else:
                    handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
        
        self.logger.warning(f"Alert created: {level.value} - {message}")
        return alert
    
    def check_metric_thresholds(self, metric: Metric):
        """Check if metric exceeds thresholds"""
        if metric.name not in self.thresholds:
            return
        
        threshold = self.thresholds[metric.name]
        threshold_value = threshold["value"]
        comparison = threshold["comparison"]
        
        should_alert = False
        if comparison == "greater_than" and metric.value > threshold_value:
            should_alert = True
        elif comparison == "less_than" and metric.value < threshold_value:
            should_alert = True
        elif comparison == "equals" and metric.value == threshold_value:
            should_alert = True
        
        if should_alert:
            self.create_alert(
                level=threshold["level"],
                message=f"Metric {metric.name} ({metric.value}) exceeded threshold ({threshold_value})",
                source="threshold_monitor",
                metadata={"metric": metric.name, "value": metric.value, "threshold": threshold_value}
            )
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Alert]:
        """Get alerts from the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        with self._lock:
            return [alert for alert in self.alerts if alert.timestamp >= cutoff]


class UserInteractionTracker:
    """Tracks user interactions and behavior"""
    
    def __init__(self, max_events: int = 10000):
        self.events: deque = deque(maxlen=max_events)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def track_event(self, event: UserInteractionEvent):
        """Track a user interaction event"""
        with self._lock:
            self.events.append(event)
            
            # Update session tracking
            if event.session_id:
                if event.session_id not in self.user_sessions:
                    self.user_sessions[event.session_id] = {
                        "user_id": event.user_id,
                        "start_time": event.timestamp,
                        "last_activity": event.timestamp,
                        "event_count": 0,
                        "events": []
                    }
                
                session = self.user_sessions[event.session_id]
                session["last_activity"] = event.timestamp
                session["event_count"] += 1
                session["events"].append(event.event_type)
    
    def get_user_activity(self, user_id: str, hours: int = 24) -> List[UserInteractionEvent]:
        """Get user activity for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._lock:
            return [
                event for event in self.events 
                if event.user_id == user_id and event.timestamp >= cutoff
            ]
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a user session"""
        return self.user_sessions.get(session_id)
    
    def get_popular_events(self, hours: int = 24) -> Dict[str, int]:
        """Get most popular event types in the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        event_counts = defaultdict(int)
        
        with self._lock:
            for event in self.events:
                if event.timestamp >= cutoff:
                    event_counts[event.event_type] += 1
        
        return dict(event_counts)


class PerformanceTracker:
    """Tracks performance metrics for services and operations"""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def record_performance(self, metric: PerformanceMetrics):
        """Record a performance metric"""
        with self._lock:
            self.metrics.append(metric)
    
    def get_service_stats(self, service_name: str, hours: int = 1) -> Dict[str, Any]:
        """Get performance statistics for a service"""
        cutoff = datetime.now() - timedelta(hours=hours)
        service_metrics = []
        
        with self._lock:
            service_metrics = [
                m for m in self.metrics 
                if m.service_name == service_name and m.timestamp >= cutoff
            ]
        
        if not service_metrics:
            return {}
        
        durations = [m.duration_ms for m in service_metrics]
        success_count = sum(1 for m in service_metrics if m.success)
        total_count = len(service_metrics)
        
        durations_sorted = sorted(durations)
        
        return {
            "total_requests": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p50_duration_ms": durations_sorted[int(len(durations) * 0.5)],
            "p95_duration_ms": durations_sorted[int(len(durations) * 0.95)],
            "p99_duration_ms": durations_sorted[int(len(durations) * 0.99)]
        }


# Default health check functions
async def database_health_check() -> HealthCheck:
    """Default database health check"""
    try:
        # This would typically check database connectivity
        # For now, return a basic check
        return HealthCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection OK"
        )
    except Exception as e:
        return HealthCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}"
        )


async def memory_service_health_check() -> HealthCheck:
    """Memory service health check"""
    try:
        # This would typically check memory service functionality
        return HealthCheck(
            name="memory_service",
            status=HealthStatus.HEALTHY,
            message="Memory service OK"
        )
    except Exception as e:
        return HealthCheck(
            name="memory_service",
            status=HealthStatus.UNHEALTHY,
            message=f"Memory service failed: {str(e)}"
        )


async def ai_orchestrator_health_check() -> HealthCheck:
    """AI Orchestrator health check"""
    try:
        # This would typically check AI orchestrator functionality
        return HealthCheck(
            name="ai_orchestrator",
            status=HealthStatus.HEALTHY,
            message="AI Orchestrator OK"
        )
    except Exception as e:
        return HealthCheck(
            name="ai_orchestrator",
            status=HealthStatus.UNHEALTHY,
            message=f"AI Orchestrator failed: {str(e)}"
        )


class AnalyticsService:
    """
    Main Analytics and Monitoring Service

    Provides comprehensive analytics, monitoring, and health checking capabilities
    for the AI Karen system. Integrates all monitoring components and provides
    a unified interface for metrics collection, health checks, and alerting.
    """

    TIME_RANGE_MULTIPLIERS = {
        "h": 1,
        "d": 24,
        "w": 24 * 7,
        "m": 24 * 30,
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.metrics_collector = MetricsCollector(
            max_metrics=self.config.get("max_metrics", 10000)
        )
        self.system_monitor = SystemMonitor(
            collection_interval=self.config.get("system_monitor_interval", 30)
        )
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager(
            max_alerts=self.config.get("max_alerts", 1000)
        )
        self.user_tracker = UserInteractionTracker(
            max_events=self.config.get("max_user_events", 10000)
        )
        self.performance_tracker = PerformanceTracker(
            max_metrics=self.config.get("max_performance_metrics", 10000)
        )
        
        # Setup default health checks
        self._register_default_health_checks()
        
        # Setup default alert thresholds
        self._setup_default_thresholds()
        
        # Start monitoring
        self.system_monitor.start_monitoring()
        
        self.logger.info("Analytics Service initialized")

    @staticmethod
    def parse_time_range(range_value: str) -> int:
        """Convert a human-friendly time range string (e.g. "24h", "7d") to hours."""
        if not range_value:
            raise ValueError("Time range value cannot be empty")

        normalized = range_value.strip().lower()
        match = re.fullmatch(r"(\d+)([hdwm])", normalized)
        if not match:
            raise ValueError(
                "Invalid time range format. Use values like 24h, 7d, 4w, or 1m"
            )

        value = int(match.group(1))
        if value <= 0:
            raise ValueError("Time range value must be greater than zero")

        unit = match.group(2)
        multiplier = AnalyticsService.TIME_RANGE_MULTIPLIERS[unit]
        return value * multiplier

    @staticmethod
    def _normalize_timestamp(timestamp: Optional[datetime]) -> Optional[datetime]:
        """Ensure timestamps are timezone-aware and normalized to UTC."""
        if timestamp is None:
            return None
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

    def get_usage_report(self, hours: int) -> Dict[str, Any]:
        """Aggregate usage information for the requested time window."""
        if hours <= 0:
            raise ValueError("Hours must be greater than zero")

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        with self.user_tracker._lock:
            events_snapshot = list(self.user_tracker.events)
            sessions_snapshot = {
                session_id: session.copy()
                for session_id, session in self.user_tracker.user_sessions.items()
            }

        filtered_events: List[tuple[UserInteractionEvent, datetime]] = []
        event_counts: Counter[str] = Counter()
        hour_counts: Counter[int] = Counter()
        user_activity_map: Dict[str, Dict[str, Any]] = {}

        for event in events_snapshot:
            event_ts = self._normalize_timestamp(event.timestamp)
            if event_ts is None or event_ts < cutoff:
                continue

            filtered_events.append((event, event_ts))
            event_counts[event.event_type] += 1
            hour_counts[event_ts.hour] += 1

            if event.user_id:
                activity = user_activity_map.setdefault(
                    event.user_id,
                    {"events": 0, "last_seen": event_ts},
                )
                activity["events"] += 1
                if event_ts > activity["last_seen"]:
                    activity["last_seen"] = event_ts

        unique_users = {event.user_id for event, _ in filtered_events if event.user_id}

        session_durations: List[float] = []
        session_count_by_user: Counter[str] = Counter()
        for session in sessions_snapshot.values():
            user_id = session.get("user_id")
            start_time = self._normalize_timestamp(session.get("start_time"))
            last_activity = self._normalize_timestamp(session.get("last_activity"))

            if not start_time or not last_activity or last_activity < cutoff:
                continue

            duration = (last_activity - start_time).total_seconds() / 60.0
            session_durations.append(max(duration, 0.0))

            if user_id:
                session_count_by_user[user_id] += 1

        average_session_minutes = (
            sum(session_durations) / len(session_durations)
            if session_durations
            else 0.0
        )

        with self.performance_tracker._lock:
            performance_snapshot = list(self.performance_tracker.metrics)

        relevant_performance = []
        for metric in performance_snapshot:
            metric_timestamp = self._normalize_timestamp(metric.timestamp)
            if metric_timestamp and metric_timestamp >= cutoff:
                relevant_performance.append(metric)

        if relevant_performance:
            success_rate = sum(1 for metric in relevant_performance if metric.success) / len(
                relevant_performance
            )
            user_satisfaction = round(success_rate * 100, 2)
        else:
            user_satisfaction = 100.0

        total_sessions = sum(session_count_by_user.values())

        user_activity_breakdown = {}
        for user_id, activity in user_activity_map.items():
            if not user_id:
                continue
            user_activity_breakdown[user_id] = {
                "events": activity["events"],
                "session_count": session_count_by_user.get(user_id, 0),
                "last_seen": activity["last_seen"].isoformat(),
            }

        return {
            "total_interactions": len(filtered_events),
            "unique_users": len(unique_users),
            "popular_features": [
                {"name": name, "usage_count": count}
                for name, count in event_counts.most_common(10)
            ],
            "peak_hours": [hour for hour, _ in hour_counts.most_common(8)],
            "user_satisfaction": user_satisfaction,
            "average_session_minutes": round(average_session_minutes, 2),
            "total_sessions": total_sessions,
            "user_activity": {
                "active_users": len(unique_users),
                "total_sessions": total_sessions,
                "events_per_user": {
                    user_id: activity["events"]
                    for user_id, activity in user_activity_map.items()
                    if user_id
                },
                "session_counts": dict(session_count_by_user),
                "per_user": user_activity_breakdown,
            },
            "event_counts": dict(event_counts),
        }

    def _register_default_health_checks(self):
        """Register default health check functions"""
        self.health_checker.register_health_check("database", database_health_check)
        self.health_checker.register_health_check("memory_service", memory_service_health_check)
        self.health_checker.register_health_check("ai_orchestrator", ai_orchestrator_health_check)
    
    def _setup_default_thresholds(self):
        """Setup default alert thresholds"""
        # CPU usage threshold
        self.alert_manager.set_threshold(
            "system.cpu.percent", 80.0, AlertLevel.WARNING, "greater_than"
        )
        self.alert_manager.set_threshold(
            "system.cpu.percent", 95.0, AlertLevel.CRITICAL, "greater_than"
        )
        
        # Memory usage threshold
        self.alert_manager.set_threshold(
            "system.memory.percent", 85.0, AlertLevel.WARNING, "greater_than"
        )
        self.alert_manager.set_threshold(
            "system.memory.percent", 95.0, AlertLevel.CRITICAL, "greater_than"
        )
        
        # Disk usage threshold
        self.alert_manager.set_threshold(
            "system.disk.percent", 90.0, AlertLevel.WARNING, "greater_than"
        )
        self.alert_manager.set_threshold(
            "system.disk.percent", 95.0, AlertLevel.CRITICAL, "greater_than"
        )
    
    # Metrics Collection Methods
    def record_metric(self, name: str, value: Union[int, float], 
                     metric_type: MetricType, tags: Dict[str, str] = None,
                     metadata: Dict[str, Any] = None):
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            metadata=metadata or {}
        )
        self.metrics_collector.record_metric(metric)
        
        # Check thresholds
        self.alert_manager.check_metric_thresholds(metric)
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        self.record_metric(name, value, MetricType.COUNTER, tags)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, tags)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        self.record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timer value"""
        self.record_metric(name, duration_ms, MetricType.TIMER, tags)
    
    # Performance Tracking Methods
    def record_performance(self, service_name: str, operation: str, 
                          duration_ms: float, success: bool,
                          error_message: str = None, metadata: Dict[str, Any] = None):
        """Record performance metrics for a service operation"""
        metric = PerformanceMetrics(
            service_name=service_name,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        self.performance_tracker.record_performance(metric)
        
        # Also record as timer metric
        self.record_timer(f"service.{service_name}.{operation}.duration", duration_ms)
        
        # Record success/failure counter
        status = "success" if success else "failure"
        self.increment_counter(f"service.{service_name}.{operation}.{status}")
    
    def get_service_performance(self, service_name: str, hours: int = 1) -> Dict[str, Any]:
        """Get performance statistics for a service"""
        return self.performance_tracker.get_service_stats(service_name, hours)
    
    # User Interaction Tracking Methods
    def track_user_event(self, user_id: str, event_type: str, 
                        event_data: Dict[str, Any] = None,
                        session_id: str = None, ip_address: str = None,
                        user_agent: str = None):
        """Track a user interaction event"""
        event = UserInteractionEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            event_data=event_data or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.user_tracker.track_event(event)
        
        # Also record as counter
        self.increment_counter(f"user.events.{event_type}")
    
    def get_user_activity(self, user_id: str, hours: int = 24) -> List[UserInteractionEvent]:
        """Get user activity for the last N hours"""
        return self.user_tracker.get_user_activity(user_id, hours)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a user session"""
        return self.user_tracker.get_session_stats(session_id)
    
    def get_popular_events(self, hours: int = 24) -> Dict[str, int]:
        """Get most popular event types"""
        return self.user_tracker.get_popular_events(hours)
    
    # Health Check Methods
    def register_health_check(self, name: str, check_function: callable):
        """Register a custom health check"""
        self.health_checker.register_health_check(name, check_function)
    
    async def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        return await self.health_checker.run_health_check(name)
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        return await self.health_checker.run_all_health_checks()
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall system health"""
        return self.health_checker.get_overall_health()
    
    # Alert Management Methods
    def create_alert(self, level: AlertLevel, message: str, source: str,
                    metadata: Dict[str, Any] = None) -> Alert:
        """Create an alert"""
        return self.alert_manager.create_alert(level, message, source, metadata)
    
    def add_alert_handler(self, handler: callable):
        """Add an alert handler"""
        self.alert_manager.add_alert_handler(handler)
    
    def set_alert_threshold(self, metric_name: str, threshold_value: float,
                           level: AlertLevel = AlertLevel.WARNING,
                           comparison: str = "greater_than"):
        """Set alert threshold for a metric"""
        self.alert_manager.set_threshold(metric_name, threshold_value, level, comparison)
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Alert]:
        """Get recent alerts"""
        return self.alert_manager.get_recent_alerts(minutes)
    
    # System Monitoring Methods
    def get_system_metrics(self) -> SystemResourceMetrics:
        """Get current system resource metrics"""
        return self.system_monitor.get_system_metrics()
    
    def get_metric_stats(self, metric_name: str) -> Dict[str, Any]:
        """Get statistics for a specific metric"""
        if metric_name in self.metrics_collector.counters:
            return {"type": "counter", "value": self.metrics_collector.get_counter(metric_name)}
        elif metric_name in self.metrics_collector.gauges:
            return {"type": "gauge", "value": self.metrics_collector.get_gauge(metric_name)}
        elif metric_name in self.metrics_collector.histograms:
            return {"type": "histogram", **self.metrics_collector.get_histogram_stats(metric_name)}
        elif metric_name in self.metrics_collector.timers:
            return {"type": "timer", **self.metrics_collector.get_histogram_stats(metric_name)}
        else:
            return {}
    
    def get_recent_metrics(self, minutes: int = 5) -> List[Metric]:
        """Get recent metrics"""
        return self.metrics_collector.get_recent_metrics(minutes)
    
    # Utility Methods
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        return {
            "system_health": self.get_overall_health().value,
            "system_metrics": self.get_system_metrics().model_dump(),
            "recent_alerts": len(self.get_recent_alerts(60)),
            "popular_events": self.get_popular_events(24),
            "total_metrics": len(self.metrics_collector.metrics),
            "total_alerts": len(self.alert_manager.alerts),
            "total_user_events": len(self.user_tracker.events),
            "active_sessions": len(self.user_tracker.user_sessions)
        }
    
    async def shutdown(self):
        """Shutdown the analytics service"""
        self.system_monitor.stop_monitoring()
        self.logger.info("Analytics Service shutdown")


# Global analytics service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(config: Dict[str, Any] = None) -> AnalyticsService:
    """Get or create the global analytics service instance"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(config)
    return _analytics_service


def initialize_analytics_service(config: Dict[str, Any] = None) -> AnalyticsService:
    """Initialize the analytics service with configuration"""
    global _analytics_service
    _analytics_service = AnalyticsService(config)
    return _analytics_service


# Context manager for performance tracking
class PerformanceTimer:
    """Context manager for tracking operation performance"""
    
    def __init__(self, service_name: str, operation: str, 
                 analytics_service: AnalyticsService = None):
        self.service_name = service_name
        self.operation = operation
        self.analytics_service = analytics_service or get_analytics_service()
        self.start_time = None
        self.success = True
        self.error_message = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
        
        duration_ms = (time.time() - self.start_time) * 1000
        self.analytics_service.record_performance(
            self.service_name,
            self.operation,
            duration_ms,
            self.success,
            self.error_message
        )
    
    def mark_failure(self, error_message: str):
        """Mark the operation as failed"""
        self.success = False
        self.error_message = error_message


# Decorator for automatic performance tracking
def track_performance(service_name: str, operation: str = None):
    """Decorator to automatically track function performance"""
    def decorator(func):
        op_name = operation or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with PerformanceTimer(service_name, op_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with PerformanceTimer(service_name, op_name):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator