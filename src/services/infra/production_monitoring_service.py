"""
Production Monitoring Service

Enhances existing monitoring with production-specific metrics for response formatting,
database consistency, authentication anomalies, and performance degradation.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, deque

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.core.metrics_manager import get_metrics_manager
from src.services.database_health_checker import (
    get_database_health_checker,
    OverallHealthStatus,
)

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Production metric types"""
    RESPONSE_FORMATTING = "response_formatting"
    DATABASE_CONSISTENCY = "database_consistency"
    AUTHENTICATION_ANOMALY = "authentication_anomaly"
    PERFORMANCE_DEGRADATION = "performance_degradation"


@dataclass
class ProductionAlert:
    """Production monitoring alert"""
    timestamp: datetime
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class ResponseFormattingMetrics:
    """Response formatting metrics"""
    total_requests: int = 0
    successful_formats: int = 0
    failed_formats: int = 0
    fallback_used: int = 0
    avg_format_time_ms: float = 0.0
    formatter_usage: Dict[str, int] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)


@dataclass
class DatabaseConsistencyMetrics:
    """Database consistency metrics"""
    last_check_timestamp: Optional[datetime] = None
    consistency_score: float = 100.0
    cross_db_issues: int = 0
    orphaned_records: int = 0
    missing_references: int = 0
    check_duration_ms: float = 0.0
    database_health_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class AuthenticationAnomalyMetrics:
    """Authentication anomaly detection metrics"""
    failed_login_attempts: int = 0
    suspicious_patterns: int = 0
    brute_force_attempts: int = 0
    unusual_access_patterns: int = 0
    blocked_ips: Set[str] = field(default_factory=set)
    anomaly_score: float = 0.0


@dataclass
class PerformanceDegradationMetrics:
    """Performance degradation metrics"""
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    error_rate_percent: float = 0.0
    throughput_rps: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    degradation_score: float = 0.0


class ProductionMonitoringService:
    """
    Production monitoring service that enhances existing monitoring with
    production-specific metrics and alerting.
    """

    def __init__(self):
        self.metrics_manager = get_metrics_manager()
        self.db_health_checker = get_database_health_checker()
        
        # Metrics storage
        self.response_formatting_metrics = ResponseFormattingMetrics()
        self.database_consistency_metrics = DatabaseConsistencyMetrics()
        self.auth_anomaly_metrics = AuthenticationAnomalyMetrics()
        self.performance_metrics = PerformanceDegradationMetrics()
        
        # Alert management
        self.active_alerts: List[ProductionAlert] = []
        self.alert_history: deque = deque(maxlen=1000)
        
        # Monitoring state
        self._monitoring_active = False
        self._last_metrics_update = datetime.utcnow()
        
        # Performance tracking
        self._response_times: deque = deque(maxlen=1000)
        self._error_counts: deque = deque(maxlen=100)
        self._auth_failures: deque = deque(maxlen=100)
        
        # Initialize Prometheus metrics
        self._init_prometheus_metrics()

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics for production monitoring"""
        with self.metrics_manager.safe_metrics_context():
            # Response formatting metrics
            self.response_format_success_counter = self.metrics_manager.register_counter(
                "kari_response_formatting_success_total",
                "Total successful response formatting operations",
                ["formatter_type", "content_type"]
            )
            
            self.response_format_failure_counter = self.metrics_manager.register_counter(
                "kari_response_formatting_failures_total",
                "Total failed response formatting operations",
                ["formatter_type", "error_type"]
            )
            
            self.response_format_duration_histogram = self.metrics_manager.register_histogram(
                "kari_response_formatting_duration_seconds",
                "Response formatting duration in seconds",
                ["formatter_type"]
            )
            
            self.response_format_fallback_counter = self.metrics_manager.register_counter(
                "kari_response_formatting_fallback_total",
                "Total response formatting fallback usage",
                ["original_formatter", "fallback_reason"]
            )
            
            # Database consistency metrics
            self.db_consistency_score_gauge = self.metrics_manager.register_gauge(
                "kari_database_consistency_score",
                "Database consistency score (0-100)",
                ["database_type"]
            )
            
            self.db_consistency_issues_gauge = self.metrics_manager.register_gauge(
                "kari_database_consistency_issues_total",
                "Total database consistency issues",
                ["issue_type", "severity"]
            )
            
            self.db_consistency_check_duration_histogram = self.metrics_manager.register_histogram(
                "kari_database_consistency_check_duration_seconds",
                "Database consistency check duration in seconds"
            )
            
            # Authentication anomaly metrics
            self.auth_anomaly_score_gauge = self.metrics_manager.register_gauge(
                "kari_authentication_anomaly_score",
                "Authentication anomaly score (0-100)"
            )
            
            self.auth_failed_attempts_counter = self.metrics_manager.register_counter(
                "kari_authentication_failed_attempts_total",
                "Total failed authentication attempts",
                ["failure_reason", "source_ip"]
            )
            
            self.auth_suspicious_patterns_counter = self.metrics_manager.register_counter(
                "kari_authentication_suspicious_patterns_total",
                "Total suspicious authentication patterns detected",
                ["pattern_type"]
            )
            
            # Performance degradation metrics
            self.performance_degradation_score_gauge = self.metrics_manager.register_gauge(
                "kari_performance_degradation_score",
                "Performance degradation score (0-100)"
            )
            
            self.api_response_time_histogram = self.metrics_manager.register_histogram(
                "kari_api_response_time_seconds",
                "API response time in seconds",
                ["endpoint", "method"]
            )
            
            self.system_error_rate_gauge = self.metrics_manager.register_gauge(
                "kari_system_error_rate_percent",
                "System error rate percentage"
            )
            
            # Production alerts
            self.production_alerts_counter = self.metrics_manager.register_counter(
                "kari_production_alerts_total",
                "Total production alerts generated",
                ["alert_type", "severity"]
            )

    async def start_monitoring(self):
        """Start production monitoring"""
        if self._monitoring_active:
            logger.warning("Production monitoring already active")
            return
        
        self._monitoring_active = True
        logger.info("Starting production monitoring service")
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_response_formatting())
        asyncio.create_task(self._monitor_database_consistency())
        asyncio.create_task(self._monitor_authentication_anomalies())
        asyncio.create_task(self._monitor_performance_degradation())
        asyncio.create_task(self._process_alerts())

    async def stop_monitoring(self):
        """Stop production monitoring"""
        self._monitoring_active = False
        logger.info("Stopped production monitoring service")

    # Response Formatting Monitoring
    
    def record_response_formatting_success(
        self,
        formatter_type: str,
        content_type: str,
        duration_ms: float
    ):
        """Record successful response formatting"""
        self.response_formatting_metrics.total_requests += 1
        self.response_formatting_metrics.successful_formats += 1
        self.response_formatting_metrics.formatter_usage[formatter_type] = (
            self.response_formatting_metrics.formatter_usage.get(formatter_type, 0) + 1
        )
        
        # Update average format time
        current_avg = self.response_formatting_metrics.avg_format_time_ms
        total_successful = self.response_formatting_metrics.successful_formats
        self.response_formatting_metrics.avg_format_time_ms = (
            (current_avg * (total_successful - 1) + duration_ms) / total_successful
        )
        
        # Update Prometheus metrics
        self.response_format_success_counter.labels(
            formatter_type=formatter_type,
            content_type=content_type
        ).inc()
        
        self.response_format_duration_histogram.labels(
            formatter_type=formatter_type
        ).observe(duration_ms / 1000.0)

    def record_response_formatting_failure(
        self,
        formatter_type: str,
        error_type: str,
        error_message: str
    ):
        """Record failed response formatting"""
        self.response_formatting_metrics.total_requests += 1
        self.response_formatting_metrics.failed_formats += 1
        self.response_formatting_metrics.error_types[error_type] = (
            self.response_formatting_metrics.error_types.get(error_type, 0) + 1
        )
        
        # Update Prometheus metrics
        self.response_format_failure_counter.labels(
            formatter_type=formatter_type,
            error_type=error_type
        ).inc()
        
        # Check for alert conditions
        failure_rate = (
            self.response_formatting_metrics.failed_formats /
            self.response_formatting_metrics.total_requests * 100
        )
        
        if failure_rate > 10:  # > 10% failure rate
            self._create_alert(
                MetricType.RESPONSE_FORMATTING,
                AlertSeverity.WARNING,
                f"High response formatting failure rate: {failure_rate:.1f}%",
                {
                    "failure_rate": failure_rate,
                    "error_type": error_type,
                    "error_message": error_message,
                }
            )

    def record_response_formatting_fallback(
        self,
        original_formatter: str,
        fallback_reason: str
    ):
        """Record response formatting fallback usage"""
        self.response_formatting_metrics.fallback_used += 1
        
        # Update Prometheus metrics
        self.response_format_fallback_counter.labels(
            original_formatter=original_formatter,
            fallback_reason=fallback_reason
        ).inc()

    async def _monitor_response_formatting(self):
        """Monitor response formatting metrics"""
        while self._monitoring_active:
            try:
                # Calculate success rate
                total = self.response_formatting_metrics.total_requests
                if total > 0:
                    success_rate = (
                        self.response_formatting_metrics.successful_formats / total * 100
                    )
                    
                    # Alert on low success rate
                    if success_rate < 90:  # < 90% success rate
                        self._create_alert(
                            MetricType.RESPONSE_FORMATTING,
                            AlertSeverity.CRITICAL,
                            f"Low response formatting success rate: {success_rate:.1f}%",
                            {"success_rate": success_rate, "total_requests": total}
                        )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring response formatting: {e}")
                await asyncio.sleep(60)

    # Database Consistency Monitoring
    
    async def update_database_consistency_metrics(self):
        """Update database consistency metrics"""
        try:
            start_time = time.time()
            
            # Get database health
            health_result = await self.db_health_checker.check_health(
                include_detailed_validation=True
            )
            
            check_duration = (time.time() - start_time) * 1000
            
            # Update metrics
            self.database_consistency_metrics.last_check_timestamp = datetime.utcnow()
            self.database_consistency_metrics.check_duration_ms = check_duration
            self.database_consistency_metrics.cross_db_issues = health_result.consistency_issues
            self.database_consistency_metrics.orphaned_records = health_result.critical_issues
            self.database_consistency_metrics.missing_references = health_result.warning_issues
            
            # Calculate consistency score
            total_issues = (
                health_result.consistency_issues +
                health_result.critical_issues +
                health_result.warning_issues
            )
            
            if total_issues == 0:
                consistency_score = 100.0
            else:
                # Deduct points based on issue severity
                deduction = (
                    health_result.critical_issues * 10 +
                    health_result.consistency_issues * 5 +
                    health_result.warning_issues * 2
                )
                consistency_score = max(0.0, 100.0 - deduction)
            
            self.database_consistency_metrics.consistency_score = consistency_score
            
            # Update database health scores
            for db_conn in health_result.database_connections:
                if db_conn.is_connected:
                    if db_conn.status.value == "healthy":
                        score = 100.0
                    elif db_conn.status.value == "warning":
                        score = 70.0
                    else:  # critical
                        score = 30.0
                else:
                    score = 0.0
                
                self.database_consistency_metrics.database_health_scores[
                    db_conn.database.value
                ] = score
            
            # Update Prometheus metrics
            self.db_consistency_score_gauge.set(consistency_score)
            
            self.db_consistency_issues_gauge.labels(
                issue_type="consistency",
                severity="all"
            ).set(total_issues)
            
            self.db_consistency_check_duration_histogram.observe(check_duration / 1000.0)
            
            # Check for alerts
            if consistency_score < 80:
                severity = AlertSeverity.CRITICAL if consistency_score < 50 else AlertSeverity.WARNING
                self._create_alert(
                    MetricType.DATABASE_CONSISTENCY,
                    severity,
                    f"Database consistency score low: {consistency_score:.1f}%",
                    {
                        "consistency_score": consistency_score,
                        "total_issues": total_issues,
                        "critical_issues": health_result.critical_issues,
                    }
                )
            
        except Exception as e:
            logger.error(f"Error updating database consistency metrics: {e}")
            self._create_alert(
                MetricType.DATABASE_CONSISTENCY,
                AlertSeverity.CRITICAL,
                f"Database consistency check failed: {str(e)}",
                {"error": str(e)}
            )

    async def _monitor_database_consistency(self):
        """Monitor database consistency"""
        while self._monitoring_active:
            try:
                await self.update_database_consistency_metrics()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in database consistency monitoring: {e}")
                await asyncio.sleep(300)

    # Authentication Anomaly Monitoring
    
    def record_authentication_failure(
        self,
        failure_reason: str,
        source_ip: str,
        user_agent: Optional[str] = None
    ):
        """Record authentication failure for anomaly detection"""
        self.auth_anomaly_metrics.failed_login_attempts += 1
        self._auth_failures.append({
            "timestamp": datetime.utcnow(),
            "reason": failure_reason,
            "source_ip": source_ip,
            "user_agent": user_agent,
        })
        
        # Update Prometheus metrics
        self.auth_failed_attempts_counter.labels(
            failure_reason=failure_reason,
            source_ip=source_ip
        ).inc()
        
        # Check for brute force patterns
        self._detect_brute_force_attempts(source_ip)

    def _detect_brute_force_attempts(self, source_ip: str):
        """Detect brute force authentication attempts"""
        now = datetime.utcnow()
        recent_failures = [
            f for f in self._auth_failures
            if f["source_ip"] == source_ip and
            (now - f["timestamp"]).total_seconds() < 300  # Last 5 minutes
        ]
        
        if len(recent_failures) >= 5:  # 5 failures in 5 minutes
            self.auth_anomaly_metrics.brute_force_attempts += 1
            self.auth_anomaly_metrics.blocked_ips.add(source_ip)
            
            self._create_alert(
                MetricType.AUTHENTICATION_ANOMALY,
                AlertSeverity.CRITICAL,
                f"Brute force attack detected from IP: {source_ip}",
                {
                    "source_ip": source_ip,
                    "failure_count": len(recent_failures),
                    "time_window": "5 minutes",
                }
            )

    async def _monitor_authentication_anomalies(self):
        """Monitor authentication anomalies"""
        while self._monitoring_active:
            try:
                # Calculate anomaly score
                now = datetime.utcnow()
                recent_failures = [
                    f for f in self._auth_failures
                    if (now - f["timestamp"]).total_seconds() < 3600  # Last hour
                ]
                
                # Base anomaly score on failure rate
                anomaly_score = min(100.0, len(recent_failures) * 2)
                
                # Increase score for brute force attempts
                if self.auth_anomaly_metrics.brute_force_attempts > 0:
                    anomaly_score = min(100.0, anomaly_score + 50)
                
                self.auth_anomaly_metrics.anomaly_score = anomaly_score
                
                # Update Prometheus metrics
                self.auth_anomaly_score_gauge.set(anomaly_score)
                
                # Alert on high anomaly score
                if anomaly_score > 70:
                    self._create_alert(
                        MetricType.AUTHENTICATION_ANOMALY,
                        AlertSeverity.WARNING,
                        f"High authentication anomaly score: {anomaly_score:.1f}",
                        {
                            "anomaly_score": anomaly_score,
                            "recent_failures": len(recent_failures),
                            "brute_force_attempts": self.auth_anomaly_metrics.brute_force_attempts,
                        }
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring authentication anomalies: {e}")
                await asyncio.sleep(60)

    # Performance Degradation Monitoring
    
    def record_api_response_time(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int
    ):
        """Record API response time for performance monitoring"""
        self._response_times.append({
            "timestamp": datetime.utcnow(),
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
        })
        
        # Update Prometheus metrics
        self.api_response_time_histogram.labels(
            endpoint=endpoint,
            method=method
        ).observe(response_time_ms / 1000.0)
        
        # Track errors
        if status_code >= 400:
            self._error_counts.append({
                "timestamp": datetime.utcnow(),
                "endpoint": endpoint,
                "status_code": status_code,
            })

    async def _monitor_performance_degradation(self):
        """Monitor performance degradation"""
        while self._monitoring_active:
            try:
                now = datetime.utcnow()
                
                # Get recent response times (last 5 minutes)
                recent_responses = [
                    r for r in self._response_times
                    if (now - r["timestamp"]).total_seconds() < 300
                ]
                
                if recent_responses:
                    # Calculate performance metrics
                    response_times = [r["response_time_ms"] for r in recent_responses]
                    response_times.sort()
                    
                    self.performance_metrics.avg_response_time_ms = sum(response_times) / len(response_times)
                    
                    # Calculate percentiles
                    p95_idx = int(len(response_times) * 0.95)
                    p99_idx = int(len(response_times) * 0.99)
                    
                    self.performance_metrics.p95_response_time_ms = response_times[p95_idx]
                    self.performance_metrics.p99_response_time_ms = response_times[p99_idx]
                    
                    # Calculate throughput
                    self.performance_metrics.throughput_rps = len(recent_responses) / 300.0
                    
                    # Calculate error rate
                    recent_errors = [
                        e for e in self._error_counts
                        if (now - e["timestamp"]).total_seconds() < 300
                    ]
                    
                    if recent_responses:
                        error_rate = len(recent_errors) / len(recent_responses) * 100
                        self.performance_metrics.error_rate_percent = error_rate
                    
                    # Calculate degradation score
                    degradation_score = 0.0
                    
                    # High response time penalty
                    if self.performance_metrics.avg_response_time_ms > 1000:
                        degradation_score += 30
                    elif self.performance_metrics.avg_response_time_ms > 500:
                        degradation_score += 15
                    
                    # High error rate penalty
                    if error_rate > 5:
                        degradation_score += 40
                    elif error_rate > 1:
                        degradation_score += 20
                    
                    # Low throughput penalty
                    if self.performance_metrics.throughput_rps < 1:
                        degradation_score += 20
                    
                    self.performance_metrics.degradation_score = min(100.0, degradation_score)
                    
                    # Update Prometheus metrics
                    self.performance_degradation_score_gauge.set(degradation_score)
                    self.system_error_rate_gauge.set(error_rate)
                    
                    # Alert on performance degradation
                    if degradation_score > 50:
                        severity = AlertSeverity.CRITICAL if degradation_score > 80 else AlertSeverity.WARNING
                        self._create_alert(
                            MetricType.PERFORMANCE_DEGRADATION,
                            severity,
                            f"Performance degradation detected: {degradation_score:.1f}% score",
                            {
                                "degradation_score": degradation_score,
                                "avg_response_time_ms": self.performance_metrics.avg_response_time_ms,
                                "error_rate_percent": error_rate,
                                "throughput_rps": self.performance_metrics.throughput_rps,
                            }
                        )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring performance degradation: {e}")
                await asyncio.sleep(30)

    # Alert Management
    
    def _create_alert(
        self,
        metric_type: MetricType,
        severity: AlertSeverity,
        message: str,
        details: Dict[str, Any]
    ):
        """Create a production alert"""
        # Check if similar alert already exists
        existing_alert = next(
            (
                alert for alert in self.active_alerts
                if alert.metric_type == metric_type and
                alert.message == message and
                not alert.resolved
            ),
            None
        )
        
        if existing_alert:
            # Update existing alert details
            existing_alert.details.update(details)
            return
        
        # Create new alert
        alert = ProductionAlert(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            severity=severity,
            message=message,
            details=details,
        )
        
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # Update Prometheus metrics
        self.production_alerts_counter.labels(
            alert_type=metric_type.value,
            severity=severity.value
        ).inc()
        
        logger.warning(f"Production alert created: {severity.value.upper()} - {message}")

    async def _process_alerts(self):
        """Process and manage production alerts"""
        while self._monitoring_active:
            try:
                # Auto-resolve old alerts
                now = datetime.utcnow()
                for alert in self.active_alerts:
                    if not alert.resolved:
                        # Auto-resolve alerts older than 1 hour
                        if (now - alert.timestamp).total_seconds() > 3600:
                            alert.resolved = True
                            alert.resolution_time = now
                            logger.info(f"Auto-resolved alert: {alert.message}")
                
                # Clean up resolved alerts
                self.active_alerts = [
                    alert for alert in self.active_alerts
                    if not alert.resolved or
                    (now - alert.resolution_time).total_seconds() < 86400  # Keep for 24 hours
                ]
                
                await asyncio.sleep(300)  # Process every 5 minutes
                
            except Exception as e:
                logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(300)

    # Public API Methods
    
    def get_production_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all production metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_active": self._monitoring_active,
            "response_formatting": {
                "total_requests": self.response_formatting_metrics.total_requests,
                "success_rate": (
                    self.response_formatting_metrics.successful_formats /
                    max(1, self.response_formatting_metrics.total_requests) * 100
                ),
                "avg_format_time_ms": self.response_formatting_metrics.avg_format_time_ms,
                "fallback_usage": self.response_formatting_metrics.fallback_used,
            },
            "database_consistency": {
                "consistency_score": self.database_consistency_metrics.consistency_score,
                "last_check": (
                    self.database_consistency_metrics.last_check_timestamp.isoformat()
                    if self.database_consistency_metrics.last_check_timestamp else None
                ),
                "total_issues": (
                    self.database_consistency_metrics.cross_db_issues +
                    self.database_consistency_metrics.orphaned_records +
                    self.database_consistency_metrics.missing_references
                ),
            },
            "authentication_anomalies": {
                "anomaly_score": self.auth_anomaly_metrics.anomaly_score,
                "failed_attempts": self.auth_anomaly_metrics.failed_login_attempts,
                "brute_force_attempts": self.auth_anomaly_metrics.brute_force_attempts,
                "blocked_ips": len(self.auth_anomaly_metrics.blocked_ips),
            },
            "performance": {
                "degradation_score": self.performance_metrics.degradation_score,
                "avg_response_time_ms": self.performance_metrics.avg_response_time_ms,
                "error_rate_percent": self.performance_metrics.error_rate_percent,
                "throughput_rps": self.performance_metrics.throughput_rps,
            },
            "alerts": {
                "active_count": len([a for a in self.active_alerts if not a.resolved]),
                "total_count": len(self.active_alerts),
                "critical_count": len([
                    a for a in self.active_alerts
                    if not a.resolved and a.severity == AlertSeverity.CRITICAL
                ]),
            },
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active production alerts"""
        return [
            {
                "timestamp": alert.timestamp.isoformat(),
                "metric_type": alert.metric_type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "details": alert.details,
                "resolved": alert.resolved,
            }
            for alert in self.active_alerts
            if not alert.resolved
        ]

    async def resolve_alert(self, alert_message: str) -> bool:
        """Manually resolve an alert"""
        for alert in self.active_alerts:
            if alert.message == alert_message and not alert.resolved:
                alert.resolved = True
                alert.resolution_time = datetime.utcnow()
                logger.info(f"Manually resolved alert: {alert_message}")
                return True
        return False


# Global instance
_production_monitoring_service: Optional[ProductionMonitoringService] = None


def get_production_monitoring_service() -> ProductionMonitoringService:
    """Get global production monitoring service instance"""
    global _production_monitoring_service
    if _production_monitoring_service is None:
        _production_monitoring_service = ProductionMonitoringService()
    return _production_monitoring_service