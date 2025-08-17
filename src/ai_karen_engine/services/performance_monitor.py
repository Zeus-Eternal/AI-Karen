"""
Performance Monitoring System - Task 8.1 & 8.4
Monitors vector query performance and tracks SLO compliance.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum
import threading
import json

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    """Types of performance metrics"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RECALL = "recall"
    MRR = "mrr"
    CACHE_HIT_RATE = "cache_hit_rate"

class SLOStatus(str, Enum):
    """SLO compliance status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    correlation_id: Optional[str] = None

@dataclass
class SLOTarget:
    """Service Level Objective target"""
    name: str
    metric_type: MetricType
    target_value: float
    comparison: str  # "lt", "gt", "eq"
    percentile: Optional[float] = None  # For percentile-based SLOs
    window_minutes: int = 5  # Time window for evaluation
    
    def evaluate(self, values: List[float]) -> bool:
        """Evaluate if SLO is met"""
        if not values:
            return False
        
        if self.percentile is not None:
            # Percentile-based evaluation
            sorted_values = sorted(values)
            n = len(sorted_values)
            idx = int(n * self.percentile / 100.0)
            if idx >= n:
                idx = n - 1
            actual_value = sorted_values[idx]
        else:
            # Average-based evaluation
            actual_value = sum(values) / len(values)
        
        if self.comparison == "lt":
            return actual_value < self.target_value
        elif self.comparison == "gt":
            return actual_value > self.target_value
        elif self.comparison == "eq":
            return abs(actual_value - self.target_value) < 0.001
        else:
            return False

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    slo_name: str
    severity: str  # "warning", "critical"
    threshold_violations: int = 3  # Number of consecutive violations to trigger
    cooldown_minutes: int = 15  # Cooldown period after alert
    webhook_url: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)

class PerformanceMonitor:
    """Performance monitoring and SLO tracking system"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.slo_targets: Dict[str, SLOTarget] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_states: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        # Performance tracking
        self.start_time = datetime.utcnow()
        self.total_requests = 0
        self.error_count = 0
        
        # Initialize default SLOs for vector operations
        self._initialize_default_slos()
        
        # Background task for SLO evaluation
        self._slo_check_task = None
        self._running = False
    
    def _initialize_default_slos(self):
        """Initialize default SLO targets for vector operations"""
        # Vector query latency SLO (p95 < 50ms)
        self.add_slo_target(SLOTarget(
            name="vector_query_p95_latency",
            metric_type=MetricType.LATENCY,
            target_value=50.0,  # 50ms
            comparison="lt",
            percentile=95.0,
            window_minutes=5
        ))
        
        # Vector query recall SLO (≥ 0.95)
        self.add_slo_target(SLOTarget(
            name="vector_query_recall",
            metric_type=MetricType.RECALL,
            target_value=0.95,
            comparison="gt",
            window_minutes=5
        ))
        
        # MRR improvement SLO (≥ 15% improvement)
        self.add_slo_target(SLOTarget(
            name="vector_query_mrr_improvement",
            metric_type=MetricType.MRR,
            target_value=0.15,
            comparison="gt",
            window_minutes=5
        ))
        
        # Error rate SLO (< 1%)
        self.add_slo_target(SLOTarget(
            name="vector_query_error_rate",
            metric_type=MetricType.ERROR_RATE,
            target_value=0.01,
            comparison="lt",
            window_minutes=5
        ))
        
        # Cache hit rate SLO (> 80%)
        self.add_slo_target(SLOTarget(
            name="vector_cache_hit_rate",
            metric_type=MetricType.CACHE_HIT_RATE,
            target_value=0.80,
            comparison="gt",
            window_minutes=5
        ))
    
    def start_monitoring(self):
        """Start background monitoring tasks"""
        if self._running:
            return
        
        self._running = True
        self._slo_check_task = asyncio.create_task(self._slo_check_loop())
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks"""
        self._running = False
        
        if self._slo_check_task:
            self._slo_check_task.cancel()
            try:
                await self._slo_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None,
                     correlation_id: Optional[str] = None):
        """Record a performance metric"""
        with self.lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {},
                correlation_id=correlation_id
            )
            
            self.metrics[name].append(metric)
            
            # Update counters
            if name.endswith("_requests"):
                self.total_requests += 1
            elif name.endswith("_errors"):
                self.error_count += 1
    
    def record_vector_search_latency(self, latency_ms: float, status: str = "success",
                                   correlation_id: Optional[str] = None):
        """Record vector search latency metric"""
        self.record_metric(
            "vector_search_latency_ms",
            latency_ms,
            labels={"status": status},
            correlation_id=correlation_id
        )
    
    def record_vector_search_recall(self, recall: float, correlation_id: Optional[str] = None):
        """Record vector search recall metric"""
        self.record_metric(
            "vector_search_recall",
            recall,
            correlation_id=correlation_id
        )
    
    def record_vector_search_mrr(self, mrr: float, baseline_mrr: float = 0.0,
                                correlation_id: Optional[str] = None):
        """Record vector search MRR improvement metric"""
        improvement = (mrr - baseline_mrr) / max(baseline_mrr, 0.001) if baseline_mrr > 0 else mrr
        self.record_metric(
            "vector_search_mrr_improvement",
            improvement,
            correlation_id=correlation_id
        )
    
    def record_cache_hit(self, hit: bool, correlation_id: Optional[str] = None):
        """Record cache hit/miss"""
        self.record_metric(
            "cache_hit",
            1.0 if hit else 0.0,
            correlation_id=correlation_id
        )
    
    def add_slo_target(self, slo: SLOTarget):
        """Add an SLO target"""
        with self.lock:
            self.slo_targets[slo.name] = slo
            logger.info(f"Added SLO target: {slo.name}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        with self.lock:
            self.alert_rules[rule.name] = rule
            self.alert_states[rule.name] = {
                "violations": 0,
                "last_alert": None,
                "status": SLOStatus.UNKNOWN
            }
            logger.info(f"Added alert rule: {rule.name}")
    
    def get_metrics(self, name: str, window_minutes: int = 5) -> List[PerformanceMetric]:
        """Get metrics within a time window"""
        with self.lock:
            if name not in self.metrics:
                return []
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            return [m for m in self.metrics[name] if m.timestamp >= cutoff_time]
    
    def get_metric_values(self, name: str, window_minutes: int = 5) -> List[float]:
        """Get metric values within a time window"""
        metrics = self.get_metrics(name, window_minutes)
        return [m.value for m in metrics]
    
    def calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        idx = int(n * percentile / 100.0)
        if idx >= n:
            idx = n - 1
        
        return sorted_values[idx]
    
    def evaluate_slo(self, slo_name: str) -> Dict[str, Any]:
        """Evaluate a specific SLO"""
        if slo_name not in self.slo_targets:
            return {"error": "SLO not found"}
        
        slo = self.slo_targets[slo_name]
        
        # Map SLO to metric name
        metric_name_map = {
            "vector_query_p95_latency": "vector_search_latency_ms",
            "vector_query_recall": "vector_search_recall",
            "vector_query_mrr_improvement": "vector_search_mrr_improvement",
            "vector_query_error_rate": "vector_search_errors",
            "vector_cache_hit_rate": "cache_hit"
        }
        
        metric_name = metric_name_map.get(slo_name, slo_name)
        values = self.get_metric_values(metric_name, slo.window_minutes)
        
        if not values:
            return {
                "slo_name": slo_name,
                "status": SLOStatus.UNKNOWN,
                "target_value": slo.target_value,
                "actual_value": None,
                "is_met": False,
                "data_points": 0
            }
        
        # Calculate actual value
        if slo.percentile is not None:
            actual_value = self.calculate_percentile(values, slo.percentile)
        else:
            actual_value = sum(values) / len(values)
        
        # Special handling for error rate
        if slo.metric_type == MetricType.ERROR_RATE:
            # Calculate error rate as errors / total requests
            error_values = self.get_metric_values("vector_search_errors", slo.window_minutes)
            request_values = self.get_metric_values("vector_search_requests", slo.window_minutes)
            
            total_errors = sum(error_values) if error_values else 0
            total_requests = sum(request_values) if request_values else 1
            
            actual_value = total_errors / total_requests
        
        # Special handling for cache hit rate
        elif slo.metric_type == MetricType.CACHE_HIT_RATE:
            # Calculate hit rate as hits / total cache accesses
            actual_value = sum(values) / len(values) if values else 0.0
        
        is_met = slo.evaluate([actual_value])
        
        # Determine status
        if is_met:
            status = SLOStatus.HEALTHY
        else:
            # Check how far off we are
            if slo.comparison == "lt":
                ratio = actual_value / slo.target_value
                status = SLOStatus.WARNING if ratio < 1.5 else SLOStatus.CRITICAL
            elif slo.comparison == "gt":
                ratio = slo.target_value / actual_value if actual_value > 0 else float('inf')
                status = SLOStatus.WARNING if ratio < 1.5 else SLOStatus.CRITICAL
            else:
                status = SLOStatus.WARNING
        
        return {
            "slo_name": slo_name,
            "status": status,
            "target_value": slo.target_value,
            "actual_value": actual_value,
            "is_met": is_met,
            "data_points": len(values),
            "comparison": slo.comparison,
            "percentile": slo.percentile,
            "window_minutes": slo.window_minutes
        }
    
    def get_slo_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive SLO dashboard"""
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_minutes": (datetime.utcnow() - self.start_time).total_seconds() / 60,
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.total_requests, 1),
            "slos": {},
            "overall_health": SLOStatus.HEALTHY
        }
        
        critical_count = 0
        warning_count = 0
        
        for slo_name in self.slo_targets:
            slo_result = self.evaluate_slo(slo_name)
            dashboard["slos"][slo_name] = slo_result
            
            if slo_result["status"] == SLOStatus.CRITICAL:
                critical_count += 1
            elif slo_result["status"] == SLOStatus.WARNING:
                warning_count += 1
        
        # Determine overall health
        if critical_count > 0:
            dashboard["overall_health"] = SLOStatus.CRITICAL
        elif warning_count > 0:
            dashboard["overall_health"] = SLOStatus.WARNING
        
        return dashboard
    
    async def _slo_check_loop(self):
        """Background loop for SLO checking and alerting"""
        while self._running:
            try:
                await self._check_slos_and_alert()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SLO check loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_slos_and_alert(self):
        """Check SLOs and trigger alerts if needed"""
        for rule_name, rule in self.alert_rules.items():
            try:
                slo_result = self.evaluate_slo(rule.slo_name)
                alert_state = self.alert_states[rule_name]
                
                if not slo_result["is_met"]:
                    alert_state["violations"] += 1
                    
                    # Check if we should trigger an alert
                    if (alert_state["violations"] >= rule.threshold_violations and
                        self._should_send_alert(rule, alert_state)):
                        
                        await self._send_alert(rule, slo_result)
                        alert_state["last_alert"] = datetime.utcnow()
                        alert_state["status"] = slo_result["status"]
                else:
                    # Reset violations on success
                    alert_state["violations"] = 0
                    alert_state["status"] = SLOStatus.HEALTHY
                    
            except Exception as e:
                logger.error(f"Error checking SLO {rule.slo_name}: {e}")
    
    def _should_send_alert(self, rule: AlertRule, alert_state: Dict[str, Any]) -> bool:
        """Check if we should send an alert based on cooldown"""
        if alert_state["last_alert"] is None:
            return True
        
        cooldown_period = timedelta(minutes=rule.cooldown_minutes)
        return datetime.utcnow() - alert_state["last_alert"] > cooldown_period
    
    async def _send_alert(self, rule: AlertRule, slo_result: Dict[str, Any]):
        """Send alert notification"""
        try:
            alert_message = {
                "alert_name": rule.name,
                "severity": rule.severity,
                "slo_name": rule.slo_name,
                "status": slo_result["status"],
                "target_value": slo_result["target_value"],
                "actual_value": slo_result["actual_value"],
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"SLO violation: {rule.slo_name} - "
                          f"Target: {slo_result['target_value']}, "
                          f"Actual: {slo_result['actual_value']:.4f}"
            }
            
            logger.warning(f"SLO Alert: {alert_message['message']}")
            
            # Send webhook if configured
            if rule.webhook_url:
                await self._send_webhook_alert(rule.webhook_url, alert_message)
            
            # Send email if configured
            if rule.email_recipients:
                await self._send_email_alert(rule.email_recipients, alert_message)
                
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _send_webhook_alert(self, webhook_url: str, alert_message: Dict[str, Any]):
        """Send webhook alert"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=alert_message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent successfully to {webhook_url}")
                    else:
                        logger.error(f"Webhook alert failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def _send_email_alert(self, recipients: List[str], alert_message: Dict[str, Any]):
        """Send email alert"""
        # Placeholder for email implementation
        logger.info(f"Email alert would be sent to {recipients}: {alert_message['message']}")
    
    def get_performance_summary(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for the specified time window"""
        summary = {
            "window_minutes": window_minutes,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {}
        }
        
        # Vector search latency
        latency_values = self.get_metric_values("vector_search_latency_ms", window_minutes)
        if latency_values:
            summary["metrics"]["vector_search_latency"] = {
                "count": len(latency_values),
                "avg_ms": sum(latency_values) / len(latency_values),
                "p50_ms": self.calculate_percentile(latency_values, 50),
                "p95_ms": self.calculate_percentile(latency_values, 95),
                "p99_ms": self.calculate_percentile(latency_values, 99),
                "max_ms": max(latency_values),
                "min_ms": min(latency_values)
            }
        
        # Recall metrics
        recall_values = self.get_metric_values("vector_search_recall", window_minutes)
        if recall_values:
            summary["metrics"]["recall"] = {
                "count": len(recall_values),
                "avg": sum(recall_values) / len(recall_values),
                "min": min(recall_values),
                "max": max(recall_values)
            }
        
        # MRR improvement metrics
        mrr_values = self.get_metric_values("vector_search_mrr_improvement", window_minutes)
        if mrr_values:
            summary["metrics"]["mrr_improvement"] = {
                "count": len(mrr_values),
                "avg": sum(mrr_values) / len(mrr_values),
                "min": min(mrr_values),
                "max": max(mrr_values)
            }
        
        # Cache hit rate
        cache_values = self.get_metric_values("cache_hit", window_minutes)
        if cache_values:
            hit_rate = sum(cache_values) / len(cache_values)
            summary["metrics"]["cache_hit_rate"] = {
                "count": len(cache_values),
                "hit_rate": hit_rate,
                "hits": sum(cache_values),
                "total_accesses": len(cache_values)
            }
        
        return summary

# Global instance
_performance_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor