"""
Enhanced Performance Metrics Collection and Monitoring System.

This module provides comprehensive performance metrics collection, real-time monitoring,
historical data storage, regression detection, and benchmarking capabilities.
"""

import asyncio
import logging
import json
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
from collections import defaultdict, deque
import statistics
import psutil
# import aiofiles  # Not available, using standard file operations
# import aiosqlite  # Not available, using standard sqlite3

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Enhanced performance metric data model."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    service_name: str
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'metric_type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'service_name': self.service_name,
            'tags': self.tags,
            'unit': self.unit,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """Create metric from dictionary."""
        return cls(
            name=data['name'],
            value=data['value'],
            metric_type=MetricType(data['metric_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            service_name=data['service_name'],
            tags=data.get('tags', {}),
            unit=data.get('unit', ''),
            description=data.get('description', '')
        )


@dataclass
class SystemMetrics:
    """System-wide performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_usage: int
    memory_percent: float
    disk_usage: int
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: Tuple[float, float, float]
    process_count: int
    thread_count: int
    
    def to_metrics(self) -> List[PerformanceMetric]:
        """Convert to list of PerformanceMetric objects."""
        return [
            PerformanceMetric("system.cpu.percent", self.cpu_percent, MetricType.GAUGE, self.timestamp, "system", unit="%"),
            PerformanceMetric("system.memory.usage", self.memory_usage, MetricType.GAUGE, self.timestamp, "system", unit="bytes"),
            PerformanceMetric("system.memory.percent", self.memory_percent, MetricType.GAUGE, self.timestamp, "system", unit="%"),
            PerformanceMetric("system.disk.usage", self.disk_usage, MetricType.GAUGE, self.timestamp, "system", unit="bytes"),
            PerformanceMetric("system.disk.percent", self.disk_percent, MetricType.GAUGE, self.timestamp, "system", unit="%"),
            PerformanceMetric("system.network.bytes_sent", self.network_bytes_sent, MetricType.COUNTER, self.timestamp, "system", unit="bytes"),
            PerformanceMetric("system.network.bytes_recv", self.network_bytes_recv, MetricType.COUNTER, self.timestamp, "system", unit="bytes"),
            PerformanceMetric("system.load.1min", self.load_average[0], MetricType.GAUGE, self.timestamp, "system"),
            PerformanceMetric("system.load.5min", self.load_average[1], MetricType.GAUGE, self.timestamp, "system"),
            PerformanceMetric("system.load.15min", self.load_average[2], MetricType.GAUGE, self.timestamp, "system"),
            PerformanceMetric("system.processes.count", self.process_count, MetricType.GAUGE, self.timestamp, "system"),
            PerformanceMetric("system.threads.count", self.thread_count, MetricType.GAUGE, self.timestamp, "system"),
        ]


@dataclass
class ServiceMetrics:
    """Service-specific performance metrics."""
    service_name: str
    timestamp: datetime
    cpu_percent: float
    memory_usage: int
    memory_percent: float
    io_read_bytes: int
    io_write_bytes: int
    thread_count: int
    open_files: int
    network_connections: int
    response_time: Optional[float] = None
    request_count: int = 0
    error_count: int = 0
    
    def to_metrics(self) -> List[PerformanceMetric]:
        """Convert to list of PerformanceMetric objects."""
        metrics = [
            PerformanceMetric(f"service.{self.service_name}.cpu.percent", self.cpu_percent, MetricType.GAUGE, self.timestamp, self.service_name, unit="%"),
            PerformanceMetric(f"service.{self.service_name}.memory.usage", self.memory_usage, MetricType.GAUGE, self.timestamp, self.service_name, unit="bytes"),
            PerformanceMetric(f"service.{self.service_name}.memory.percent", self.memory_percent, MetricType.GAUGE, self.timestamp, self.service_name, unit="%"),
            PerformanceMetric(f"service.{self.service_name}.io.read_bytes", self.io_read_bytes, MetricType.COUNTER, self.timestamp, self.service_name, unit="bytes"),
            PerformanceMetric(f"service.{self.service_name}.io.write_bytes", self.io_write_bytes, MetricType.COUNTER, self.timestamp, self.service_name, unit="bytes"),
            PerformanceMetric(f"service.{self.service_name}.threads.count", self.thread_count, MetricType.GAUGE, self.timestamp, self.service_name),
            PerformanceMetric(f"service.{self.service_name}.files.open", self.open_files, MetricType.GAUGE, self.timestamp, self.service_name),
            PerformanceMetric(f"service.{self.service_name}.network.connections", self.network_connections, MetricType.GAUGE, self.timestamp, self.service_name),
            PerformanceMetric(f"service.{self.service_name}.requests.count", self.request_count, MetricType.COUNTER, self.timestamp, self.service_name),
            PerformanceMetric(f"service.{self.service_name}.errors.count", self.error_count, MetricType.COUNTER, self.timestamp, self.service_name),
        ]
        
        if self.response_time is not None:
            metrics.append(PerformanceMetric(f"service.{self.service_name}.response_time", self.response_time, MetricType.TIMER, self.timestamp, self.service_name, unit="seconds"))
        
        return metrics


@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    id: str
    name: str
    description: str
    metric_name: str
    threshold: float
    comparison: str  # >, <, >=, <=, ==, !=
    severity: AlertSeverity
    service_name: Optional[str] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class RegressionDetection:
    """Performance regression detection result."""
    metric_name: str
    service_name: str
    baseline_value: float
    current_value: float
    change_percent: float
    is_regression: bool
    severity: AlertSeverity
    detected_at: datetime
    description: str


class MetricsStorage:
    """Storage backend for performance metrics."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    tags TEXT,
                    unit TEXT,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp 
                ON metrics(name, timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_service_timestamp 
                ON metrics(service_name, timestamp)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    metric_name TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    comparison TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    service_name TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TEXT,
                    trigger_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    metric_name TEXT,
                    service_name TEXT,
                    baseline_value REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (metric_name, service_name)
                )
            """)
    
    async def store_metric(self, metric: PerformanceMetric):
        """Store a single metric."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metrics (name, value, metric_type, timestamp, service_name, tags, unit, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.name,
                metric.value,
                metric.metric_type.value,
                metric.timestamp.isoformat(),
                metric.service_name,
                json.dumps(metric.tags),
                metric.unit,
                metric.description
            ))
            conn.commit()
    
    async def store_metrics(self, metrics: List[PerformanceMetric]):
        """Store multiple metrics efficiently."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT INTO metrics (name, value, metric_type, timestamp, service_name, tags, unit, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    metric.name,
                    metric.value,
                    metric.metric_type.value,
                    metric.timestamp.isoformat(),
                    metric.service_name,
                    json.dumps(metric.tags),
                    metric.unit,
                    metric.description
                )
                for metric in metrics
            ])
            conn.commit()
    
    async def get_metrics(self, 
                         metric_name: Optional[str] = None,
                         service_name: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 1000) -> List[PerformanceMetric]:
        """Retrieve metrics with filtering."""
        query = "SELECT name, value, metric_type, timestamp, service_name, tags, unit, description FROM metrics WHERE 1=1"
        params = []
        
        if metric_name:
            query += " AND name = ?"
            params.append(metric_name)
        
        if service_name:
            query += " AND service_name = ?"
            params.append(service_name)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            metrics = []
            for row in rows:
                tags = json.loads(row[5]) if row[5] else {}
                metrics.append(PerformanceMetric(
                    name=row[0],
                    value=row[1],
                    metric_type=MetricType(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    service_name=row[4],
                    tags=tags,
                    unit=row[6] or "",
                    description=row[7] or ""
                ))
            
            return metrics
    
    async def store_baseline(self, metric_name: str, service_name: str, baseline_value: float, sample_count: int):
        """Store performance baseline."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO baselines (metric_name, service_name, baseline_value, sample_count)
                VALUES (?, ?, ?, ?)
            """, (metric_name, service_name, baseline_value, sample_count))
            conn.commit()
    
    async def get_baseline(self, metric_name: str, service_name: str) -> Optional[Tuple[float, int]]:
        """Get performance baseline."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT baseline_value, sample_count FROM baselines 
                WHERE metric_name = ? AND service_name = ?
            """, (metric_name, service_name))
            row = cursor.fetchone()
            return (row[0], row[1]) if row else None
    
    async def store_alert(self, alert: PerformanceAlert):
        """Store or update a performance alert."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alerts
                (id, name, description, metric_name, threshold, comparison, severity,
                 service_name, enabled, last_triggered, trigger_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.name,
                alert.description,
                alert.metric_name,
                alert.threshold,
                alert.comparison,
                alert.severity.value,
                alert.service_name,
                1 if alert.enabled else 0,
                alert.last_triggered.isoformat() if alert.last_triggered else None,
                alert.trigger_count
            ))
            conn.commit()

    async def get_alerts(self, enabled_only: bool = True) -> List[PerformanceAlert]:
        """Get all configured alerts."""
        query = "SELECT * FROM alerts"
        if enabled_only:
            query += " WHERE enabled = 1"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            alerts = []
            for row in rows:
                alert = PerformanceAlert(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    metric_name=row[3],
                    threshold=row[4],
                    comparison=row[5],
                    severity=AlertSeverity(row[6]),
                    service_name=row[7],
                    enabled=bool(row[8]),
                    last_triggered=datetime.fromisoformat(row[10]) if row[10] else None,
                    trigger_count=row[11]
                )
                alerts.append(alert)

            return alerts

    async def update_alert_trigger(self, alert_id: str, triggered_at: datetime):
        """Update alert trigger information."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE alerts
                SET last_triggered = ?, trigger_count = trigger_count + 1
                WHERE id = ?
            """, (triggered_at.isoformat(), alert_id))
            conn.commit()

    async def cleanup_old_metrics(self, retention_days: int = 30):
        """Clean up old metrics data."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM metrics WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            conn.commit()
            
            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} old metrics records")
            return deleted_count


class MetricsCollector:
    """Collects performance metrics from various sources."""
    
    def __init__(self):
        self.custom_collectors: Dict[str, Callable] = {}
        self.last_network_stats = None
        self.last_collection_time = None
    
    def register_collector(self, name: str, collector_func: Callable):
        """Register a custom metrics collector."""
        self.custom_collectors[name] = collector_func
        logger.info(f"Registered custom collector: {name}")
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide performance metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        
        # Load average (Unix-like systems)
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            # Windows doesn't have load average
            load_avg = (0.0, 0.0, 0.0)
        
        # Process and thread counts
        process_count = len(psutil.pids())
        thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']) if p.info['num_threads'])
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_usage=memory.used,
            memory_percent=memory.percent,
            disk_usage=disk.used,
            disk_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            load_average=load_avg,
            process_count=process_count,
            thread_count=thread_count
        )
    
    async def collect_service_metrics(self, service_name: str, pid: Optional[int] = None) -> Optional[ServiceMetrics]:
        """Collect metrics for a specific service."""
        try:
            if pid:
                process = psutil.Process(pid)
            else:
                # Find process by name
                processes = [p for p in psutil.process_iter(['pid', 'name']) if service_name in p.info['name']]
                if not processes:
                    return None
                process = processes[0]
            
            # Get process info
            proc_info = process.as_dict([
                'cpu_percent', 'memory_info', 'memory_percent',
                'io_counters', 'num_threads', 'num_fds', 'connections'
            ])
            
            # I/O counters
            io_counters = proc_info.get('io_counters')
            io_read = io_counters.read_bytes if io_counters else 0
            io_write = io_counters.write_bytes if io_counters else 0
            
            return ServiceMetrics(
                service_name=service_name,
                timestamp=datetime.now(),
                cpu_percent=proc_info['cpu_percent'],
                memory_usage=proc_info['memory_info'].rss,
                memory_percent=proc_info['memory_percent'],
                io_read_bytes=io_read,
                io_write_bytes=io_write,
                thread_count=proc_info['num_threads'],
                open_files=proc_info.get('num_fds', 0),
                network_connections=len(proc_info.get('connections', []))
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception as e:
            logger.debug(f"Error collecting metrics for {service_name}: {e}")
            return None
    
    async def collect_custom_metrics(self) -> List[PerformanceMetric]:
        """Collect metrics from custom collectors."""
        metrics = []
        
        for name, collector in self.custom_collectors.items():
            try:
                custom_metrics = await collector()
                if isinstance(custom_metrics, list):
                    metrics.extend(custom_metrics)
                elif isinstance(custom_metrics, PerformanceMetric):
                    metrics.append(custom_metrics)
            except Exception as e:
                logger.error(f"Error in custom collector {name}: {e}")
        
        return metrics


class RegressionDetector:
    """Detects performance regressions by comparing against baselines."""
    
    def __init__(self, storage: MetricsStorage):
        self.storage = storage
        self.regression_thresholds = {
            'cpu_percent': 20.0,  # 20% increase is a regression
            'memory_usage': 15.0,  # 15% increase is a regression
            'response_time': 25.0,  # 25% increase is a regression
            'error_count': 5.0,    # 5% increase is a regression
        }
    
    async def detect_regressions(self, 
                               lookback_hours: int = 24,
                               min_samples: int = 10) -> List[RegressionDetection]:
        """Detect performance regressions."""
        regressions = []
        
        # Get recent metrics
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        recent_metrics = await self.storage.get_metrics(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # Group metrics by name and service
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            key = (metric.name, metric.service_name)
            metric_groups[key].append(metric)
        
        # Check each metric group for regressions
        for (metric_name, service_name), metrics in metric_groups.items():
            if len(metrics) < min_samples:
                continue
            
            regression = await self._check_metric_regression(
                metric_name, service_name, metrics
            )
            if regression:
                regressions.append(regression)
        
        return regressions
    
    async def _check_metric_regression(self, 
                                     metric_name: str, 
                                     service_name: str, 
                                     metrics: List[PerformanceMetric]) -> Optional[RegressionDetection]:
        """Check if a specific metric shows regression."""
        # Get baseline
        baseline_data = await self.storage.get_baseline(metric_name, service_name)
        if not baseline_data:
            # No baseline, create one from current data
            values = [m.value for m in metrics]
            baseline_value = statistics.mean(values)
            await self.storage.store_baseline(metric_name, service_name, baseline_value, len(values))
            return None
        
        baseline_value, _ = baseline_data
        
        # Calculate current average
        recent_values = [m.value for m in metrics[-min(10, len(metrics)):]]  # Last 10 samples
        current_value = statistics.mean(recent_values)
        
        # Calculate change percentage
        if baseline_value == 0:
            change_percent = 0.0
        else:
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
        
        # Determine if this is a regression
        threshold = self._get_regression_threshold(metric_name)
        is_regression = abs(change_percent) > threshold
        
        if not is_regression:
            return None
        
        # Determine severity
        if abs(change_percent) > threshold * 2:
            severity = AlertSeverity.CRITICAL
        elif abs(change_percent) > threshold * 1.5:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO
        
        # Create description
        direction = "increased" if change_percent > 0 else "decreased"
        description = f"{metric_name} for {service_name} has {direction} by {abs(change_percent):.1f}% from baseline"
        
        return RegressionDetection(
            metric_name=metric_name,
            service_name=service_name,
            baseline_value=baseline_value,
            current_value=current_value,
            change_percent=change_percent,
            is_regression=is_regression,
            severity=severity,
            detected_at=datetime.now(),
            description=description
        )
    
    def _get_regression_threshold(self, metric_name: str) -> float:
        """Get regression threshold for a metric."""
        for pattern, threshold in self.regression_thresholds.items():
            if pattern in metric_name.lower():
                return threshold
        return 10.0  # Default threshold


class PerformanceDashboard:
    """Real-time performance dashboard."""
    
    def __init__(self, storage: MetricsStorage):
        self.storage = storage
        self.dashboard_data = {}
        self.update_interval = 30  # seconds
        self.running = False
        self.update_task = None
    
    async def start(self):
        """Start the dashboard update loop."""
        if self.running:
            return
        
        self.running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("Performance dashboard started")
    
    async def stop(self):
        """Stop the dashboard update loop."""
        self.running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance dashboard stopped")
    
    async def _update_loop(self):
        """Main dashboard update loop."""
        while self.running:
            try:
                await self._update_dashboard_data()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _update_dashboard_data(self):
        """Update dashboard data."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)  # Last hour
        
        # Get recent metrics
        recent_metrics = await self.storage.get_metrics(
            start_time=start_time,
            end_time=end_time,
            limit=5000
        )
        
        # Group by service
        service_metrics = defaultdict(list)
        system_metrics = []
        
        for metric in recent_metrics:
            if metric.service_name == "system":
                system_metrics.append(metric)
            else:
                service_metrics[metric.service_name].append(metric)
        
        # Update dashboard data
        self.dashboard_data = {
            'last_updated': end_time.isoformat(),
            'system_overview': self._create_system_overview(system_metrics),
            'services': {
                service: self._create_service_overview(metrics)
                for service, metrics in service_metrics.items()
            },
            'alerts': await self._get_active_alerts()
        }
    
    def _create_system_overview(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Create system overview data."""
        if not metrics:
            return {}
        
        # Group by metric name
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_groups[metric.name].append(metric.value)
        
        overview = {}
        for metric_name, values in metric_groups.items():
            if values:
                overview[metric_name] = {
                    'current': values[-1],
                    'average': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'trend': self._calculate_trend(values)
                }
        
        return overview
    
    def _create_service_overview(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Create service overview data."""
        if not metrics:
            return {}
        
        # Group by metric name
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_groups[metric.name].append(metric.value)
        
        overview = {}
        for metric_name, values in metric_groups.items():
            if values:
                overview[metric_name] = {
                    'current': values[-1],
                    'average': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'trend': self._calculate_trend(values)
                }
        
        return overview
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get active alerts by checking current metrics against configured thresholds.
        Production implementation with real-time alert evaluation.
        """
        try:
            # Get all enabled alerts
            alerts = await self.storage.get_alerts(enabled_only=True)

            if not alerts:
                return []

            active_alerts = []
            current_time = datetime.now()

            # Check each alert
            for alert in alerts:
                try:
                    # Get recent metrics for this alert
                    recent_metrics = await self.storage.get_metrics(
                        metric_name=alert.metric_name,
                        service_name=alert.service_name,
                        start_time=current_time - timedelta(minutes=5),  # Check last 5 minutes
                        limit=10
                    )

                    if not recent_metrics:
                        continue

                    # Get the most recent metric value
                    latest_metric = recent_metrics[0]
                    current_value = latest_metric.value

                    # Check if alert condition is met
                    is_triggered = self._evaluate_alert_condition(
                        current_value,
                        alert.threshold,
                        alert.comparison
                    )

                    if is_triggered:
                        # Build alert info
                        alert_info = {
                            'id': alert.id,
                            'name': alert.name,
                            'description': alert.description,
                            'severity': alert.severity.value,
                            'metric_name': alert.metric_name,
                            'service_name': alert.service_name or 'system',
                            'current_value': current_value,
                            'threshold': alert.threshold,
                            'comparison': alert.comparison,
                            'triggered_at': current_time.isoformat(),
                            'trigger_count': alert.trigger_count + 1,
                            'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None
                        }

                        active_alerts.append(alert_info)

                        # Update alert trigger information
                        await self.storage.update_alert_trigger(alert.id, current_time)

                except Exception as e:
                    logger.error(f"Error evaluating alert {alert.name}: {e}")
                    continue

            # Sort by severity (critical first)
            severity_order = {'critical': 0, 'warning': 1, 'info': 2}
            active_alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))

            return active_alerts

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []

    def _evaluate_alert_condition(self, value: float, threshold: float, comparison: str) -> bool:
        """
        Evaluate if an alert condition is met.

        Args:
            value: Current metric value
            threshold: Alert threshold value
            comparison: Comparison operator (>, <, >=, <=, ==, !=)

        Returns:
            True if alert condition is met, False otherwise
        """
        try:
            if comparison == '>':
                return value > threshold
            elif comparison == '<':
                return value < threshold
            elif comparison == '>=':
                return value >= threshold
            elif comparison == '<=':
                return value <= threshold
            elif comparison == '==':
                return abs(value - threshold) < 0.001  # Float equality with tolerance
            elif comparison == '!=':
                return abs(value - threshold) >= 0.001
            else:
                logger.warning(f"Unknown comparison operator: {comparison}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        return self.dashboard_data.copy()
    
    async def export_dashboard_data(self, file_path: Path):
        """Export dashboard data to file."""
        with open(file_path, 'w') as f:
            f.write(json.dumps(self.dashboard_data, indent=2))


class PerformanceBenchmark:
    """Performance benchmarking tools."""
    
    def __init__(self, storage: MetricsStorage):
        self.storage = storage
        self.benchmarks = {}
    
    async def create_baseline(self, 
                            name: str, 
                            duration_minutes: int = 60,
                            services: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create performance baseline from current metrics."""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=duration_minutes)
        
        # Get metrics for baseline period
        metrics = await self.storage.get_metrics(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        if services:
            metrics = [m for m in metrics if m.service_name in services]
        
        # Calculate baseline statistics
        baseline = self._calculate_baseline_stats(metrics)
        baseline['name'] = name
        baseline['created_at'] = datetime.now().isoformat()
        baseline['duration_minutes'] = duration_minutes
        baseline['services'] = services
        
        # Store baseline
        self.benchmarks[name] = baseline
        
        # Store individual metric baselines
        metric_groups = defaultdict(list)
        for metric in metrics:
            key = (metric.name, metric.service_name)
            metric_groups[key].append(metric.value)
        
        for (metric_name, service_name), values in metric_groups.items():
            if values:
                avg_value = statistics.mean(values)
                await self.storage.store_baseline(metric_name, service_name, avg_value, len(values))
        
        logger.info(f"Created performance baseline '{name}' with {len(metrics)} metrics")
        return baseline
    
    def _calculate_baseline_stats(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate baseline statistics from metrics."""
        if not metrics:
            return {}
        
        # Group by metric name and service
        metric_groups = defaultdict(list)
        for metric in metrics:
            key = f"{metric.service_name}.{metric.name}"
            metric_groups[key].append(metric.value)
        
        stats = {}
        for metric_key, values in metric_groups.items():
            if values:
                stats[metric_key] = {
                    'count': len(values),
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0
                }
        
        return {
            'metrics': stats,
            'total_samples': len(metrics),
            'unique_metrics': len(metric_groups)
        }
    
    async def compare_to_baseline(self, 
                                baseline_name: str,
                                duration_minutes: int = 60) -> Dict[str, Any]:
        """Compare current performance to a baseline."""
        if baseline_name not in self.benchmarks:
            raise ValueError(f"Baseline '{baseline_name}' not found")
        
        baseline = self.benchmarks[baseline_name]
        
        # Get current metrics
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=duration_minutes)
        
        current_metrics = await self.storage.get_metrics(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # Calculate current stats
        current_stats = self._calculate_baseline_stats(current_metrics)
        
        # Compare
        comparison = {
            'baseline_name': baseline_name,
            'comparison_time': datetime.now().isoformat(),
            'baseline_stats': baseline['metrics'],
            'current_stats': current_stats['metrics'],
            'differences': {},
            'summary': {
                'improved_metrics': 0,
                'degraded_metrics': 0,
                'stable_metrics': 0
            }
        }
        
        # Calculate differences
        for metric_key in baseline['metrics']:
            if metric_key in current_stats['metrics']:
                baseline_val = baseline['metrics'][metric_key]['mean']
                current_val = current_stats['metrics'][metric_key]['mean']
                
                if baseline_val != 0:
                    change_percent = ((current_val - baseline_val) / baseline_val) * 100
                else:
                    change_percent = 0.0
                
                comparison['differences'][metric_key] = {
                    'baseline_value': baseline_val,
                    'current_value': current_val,
                    'change_percent': change_percent,
                    'status': self._classify_change(metric_key, change_percent)
                }
                
                # Update summary
                status = comparison['differences'][metric_key]['status']
                if status == 'improved':
                    comparison['summary']['improved_metrics'] += 1
                elif status == 'degraded':
                    comparison['summary']['degraded_metrics'] += 1
                else:
                    comparison['summary']['stable_metrics'] += 1
        
        return comparison
    
    def _classify_change(self, metric_key: str, change_percent: float) -> str:
        """Classify performance change as improved, degraded, or stable."""
        # For most metrics, lower is better (CPU, memory, response time)
        # For some metrics, higher might be better (throughput, success rate)
        
        threshold = 5.0  # 5% threshold for significant change
        
        # Metrics where higher is worse
        worse_when_higher = ['cpu', 'memory', 'response_time', 'error', 'latency']
        
        is_worse_when_higher = any(pattern in metric_key.lower() for pattern in worse_when_higher)
        
        if abs(change_percent) < threshold:
            return 'stable'
        elif is_worse_when_higher:
            return 'degraded' if change_percent > 0 else 'improved'
        else:
            return 'improved' if change_percent > 0 else 'degraded'
    
    def get_benchmark(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a stored benchmark."""
        return self.benchmarks.get(name)
    
    def list_benchmarks(self) -> List[str]:
        """List all stored benchmarks."""
        return list(self.benchmarks.keys())
    
    async def export_benchmark(self, name: str, file_path: Path):
        """Export benchmark to file."""
        if name not in self.benchmarks:
            raise ValueError(f"Benchmark '{name}' not found")
        
        with open(file_path, 'w') as f:
            f.write(json.dumps(self.benchmarks[name], indent=2))


class PerformanceMonitoringSystem:
    """Main performance monitoring system coordinator."""
    
    def __init__(self, 
                 db_path: Path = Path("data/performance_metrics.db"),
                 collection_interval: int = 30):
        self.db_path = db_path
        self.collection_interval = collection_interval
        
        # Initialize components
        self.storage = MetricsStorage(db_path)
        self.collector = MetricsCollector()
        self.regression_detector = RegressionDetector(self.storage)
        self.dashboard = PerformanceDashboard(self.storage)
        self.benchmark = PerformanceBenchmark(self.storage)
        
        # State
        self.running = False
        self.collection_task = None
        self.regression_task = None
        
        logger.info(f"Performance monitoring system initialized: {db_path}")
    
    async def start(self):
        """Start the performance monitoring system."""
        if self.running:
            return
        
        self.running = True
        
        # Start components
        await self.dashboard.start()
        
        # Start collection task
        self.collection_task = asyncio.create_task(self._collection_loop())
        
        # Start regression detection task
        self.regression_task = asyncio.create_task(self._regression_loop())
        
        logger.info("Performance monitoring system started")
    
    async def stop(self):
        """Stop the performance monitoring system."""
        self.running = False
        
        # Stop components
        await self.dashboard.stop()
        
        # Cancel tasks
        if self.collection_task:
            self.collection_task.cancel()
        if self.regression_task:
            self.regression_task.cancel()
        
        # Wait for tasks to complete
        for task in [self.collection_task, self.regression_task]:
            if task:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Performance monitoring system stopped")
    
    async def _collection_loop(self):
        """Main metrics collection loop."""
        while self.running:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _regression_loop(self):
        """Regression detection loop."""
        while self.running:
            try:
                # Run regression detection every 10 minutes
                await asyncio.sleep(600)
                
                regressions = await self.regression_detector.detect_regressions()
                if regressions:
                    logger.warning(f"Detected {len(regressions)} performance regressions")
                    for regression in regressions:
                        logger.warning(f"Regression: {regression.description}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in regression detection: {e}")
    
    async def _collect_all_metrics(self):
        """Collect all types of metrics."""
        all_metrics = []
        
        # Collect system metrics
        try:
            system_metrics = await self.collector.collect_system_metrics()
            all_metrics.extend(system_metrics.to_metrics())
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        # Collect service metrics for known services
        known_services = ['main', 'api', 'auth', 'llm', 'database', 'memory']
        for service_name in known_services:
            try:
                service_metrics = await self.collector.collect_service_metrics(service_name)
                if service_metrics:
                    all_metrics.extend(service_metrics.to_metrics())
            except Exception as e:
                logger.debug(f"Error collecting metrics for {service_name}: {e}")
        
        # Collect custom metrics
        try:
            custom_metrics = await self.collector.collect_custom_metrics()
            all_metrics.extend(custom_metrics)
        except Exception as e:
            logger.error(f"Error collecting custom metrics: {e}")
        
        # Store all metrics
        if all_metrics:
            await self.storage.store_metrics(all_metrics)
            logger.debug(f"Stored {len(all_metrics)} performance metrics")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        return await self.dashboard.get_dashboard_data()
    
    async def create_benchmark(self, name: str, **kwargs) -> Dict[str, Any]:
        """Create a performance benchmark."""
        return await self.benchmark.create_baseline(name, **kwargs)
    
    async def compare_to_benchmark(self, name: str, **kwargs) -> Dict[str, Any]:
        """Compare current performance to a benchmark."""
        return await self.benchmark.compare_to_baseline(name, **kwargs)
    
    def register_custom_collector(self, name: str, collector_func: Callable):
        """Register a custom metrics collector."""
        self.collector.register_collector(name, collector_func)
    
    async def cleanup_old_data(self, retention_days: int = 30):
        """Clean up old performance data."""
        return await self.storage.cleanup_old_metrics(retention_days)


# Global instance
_monitoring_system: Optional[PerformanceMonitoringSystem] = None


def get_performance_monitoring_system() -> PerformanceMonitoringSystem:
    """Get the global performance monitoring system instance."""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = PerformanceMonitoringSystem()
    return _monitoring_system


async def initialize_performance_monitoring():
    """Initialize and start the performance monitoring system."""
    system = get_performance_monitoring_system()
    await system.start()
    return system


async def shutdown_performance_monitoring():
    """Shutdown the performance monitoring system."""
    global _monitoring_system
    if _monitoring_system:
        await _monitoring_system.stop()
        _monitoring_system = None


# ---------------------------------------------------------------------------
# Compatibility wrapper expected by optimized_startup: PerformanceMetrics
# ---------------------------------------------------------------------------

class PerformanceMetrics:
    """Lightweight async wrapper exposing initialize(), record_metric(), start_collection().

    This exists so imports from ai_karen_engine.core.performance_metrics work even
    when only the minimal monitoring stack is used. It logs metrics and, when
    possible, persists them via MetricsStorage.
    """

    def __init__(self, db_path: Optional[Path] = None, service_name: str = "system"):
        self.service_name = service_name
        self.db_path = db_path or Path("data/metrics/metrics.sqlite3")
        self.storage: Optional[MetricsStorage] = None
        self._collecting = False
        self._thread: Optional[threading.Thread] = None

    async def initialize(self) -> None:
        try:
            self.storage = MetricsStorage(self.db_path)
            logger.info(f"PerformanceMetrics initialized at {self.db_path}")
        except Exception as e:
            logger.warning(f"PerformanceMetrics storage disabled: {e}")
            self.storage = None

    async def record_metric(self, name: str, value: float, *, service_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None, unit: str = "") -> None:
        metric = PerformanceMetric(
            name=name,
            value=float(value),
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            service_name=service_name or self.service_name,
            tags=tags or {},
            unit=unit,
        )
        # Always log a structured record
        try:
            logger.info(json.dumps({"metric": metric.to_dict()}))
        except Exception:
            logger.info(f"metric {name}={value}")
        # Persist when storage is available
        if self.storage:
            try:
                await self.storage.store_metric(metric)
            except Exception as e:
                logger.debug(f"Persist metric failed: {e}")

    async def start_collection(self, interval_seconds: int = 0) -> None:
        """Optionally start a simple background system metrics collector."""
        if interval_seconds <= 0 or self._collecting:
            return
        self._collecting = True

        def _loop():
            collector = MetricsCollector()
            while self._collecting:
                try:
                    # Blocking psutil sample ~1s
                    sysm = asyncio.run(collector.collect_system_metrics())
                    if self.storage:
                        # Persist a small batch
                        asyncio.run(self.storage.store_metrics(sysm.to_metrics()))
                except Exception:
                    pass
                time.sleep(interval_seconds)

        self._thread = threading.Thread(target=_loop, name="perf-metrics", daemon=True)
        self._thread.start()
