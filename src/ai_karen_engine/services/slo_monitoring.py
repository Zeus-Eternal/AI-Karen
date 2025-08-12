"""
SLO Monitoring and Alerting System - Phase 4.1.d
Production-ready SLO monitoring with automated alerting for performance thresholds.
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
import asyncio
import json

logger = logging.getLogger(__name__)

class SLOStatus(Enum):
    """SLO status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class SLOThreshold:
    """SLO threshold configuration"""
    name: str
    metric_name: str
    threshold_value: float
    comparison: str = "less_than"  # less_than, greater_than, equals
    time_window: str = "5m"
    evaluation_period: str = "1m"
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    description: str = ""

@dataclass
class SLOTarget:
    """SLO target definition"""
    name: str
    description: str
    target_value: float
    time_window: str
    thresholds: List[SLOThreshold] = field(default_factory=list)
    enabled: bool = True

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str
    severity: AlertSeverity
    message: str
    cooldown_period: str = "5m"
    escalation_policy: Optional[str] = None
    enabled: bool = True

@dataclass
class SLOViolation:
    """SLO violation record"""
    slo_name: str
    threshold_name: str
    actual_value: float
    threshold_value: float
    severity: AlertSeverity
    timestamp: datetime
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricBuffer:
    """Buffer for storing metric values with time windows"""
    
    def __init__(self, max_age_seconds: int = 3600):
        self.values = deque()
        self.max_age_seconds = max_age_seconds
    
    def add_value(self, value: float, timestamp: Optional[datetime] = None):
        """Add a metric value"""
        timestamp = timestamp or datetime.utcnow()
        self.values.append((timestamp, value))
        self._cleanup_old_values()
    
    def _cleanup_old_values(self):
        """Remove values older than max_age"""
        cutoff = datetime.utcnow() - timedelta(seconds=self.max_age_seconds)
        while self.values and self.values[0][0] < cutoff:
            self.values.popleft()
    
    def get_values_in_window(self, window_seconds: int) -> List[float]:
        """Get values within the specified time window"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        return [value for timestamp, value in self.values if timestamp >= cutoff]
    
    def get_percentile(self, percentile: float, window_seconds: int) -> Optional[float]:
        """Calculate percentile for values in time window"""
        values = self.get_values_in_window(window_seconds)
        if not values:
            return None
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_average(self, window_seconds: int) -> Optional[float]:
        """Calculate average for values in time window"""
        values = self.get_values_in_window(window_seconds)
        return sum(values) / len(values) if values else None
    
    def get_count(self, window_seconds: int) -> int:
        """Get count of values in time window"""
        return len(self.get_values_in_window(window_seconds))

class SLOMonitor:
    """SLO monitoring and alerting system"""
    
    def __init__(self):
        self.slo_targets = {}
        self.alert_rules = {}
        self.metric_buffers = defaultdict(MetricBuffer)
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        self.violation_history = deque(maxlen=10000)
        self.alert_callbacks = []
        self.running = False
        self.evaluation_task = None
        
        # Initialize default SLO targets based on requirements
        self._init_default_slos()
        self._init_default_alert_rules()
    
    def _init_default_slos(self):
        """Initialize default SLO targets based on requirements"""
        
        # Vector query latency SLO: p95 < 50ms
        self.add_slo_target(SLOTarget(
            name="vector_query_latency",
            description="Vector query p95 latency should be under 50ms",
            target_value=0.050,  # 50ms in seconds
            time_window="5m",
            thresholds=[
                SLOThreshold(
                    name="vector_p95_latency",
                    metric_name="vector_latency_seconds",
                    threshold_value=0.050,
                    comparison="less_than",
                    warning_threshold=0.040,
                    critical_threshold=0.050,
                    description="Vector search p95 latency"
                )
            ]
        ))
        
        # First token latency SLO: p95 < 1.2s
        self.add_slo_target(SLOTarget(
            name="first_token_latency",
            description="First token p95 latency should be under 1.2 seconds",
            target_value=1.2,
            time_window="5m",
            thresholds=[
                SLOThreshold(
                    name="first_token_p95_latency",
                    metric_name="llm_latency_seconds",
                    threshold_value=1.2,
                    comparison="less_than",
                    warning_threshold=1.0,
                    critical_threshold=1.2,
                    description="LLM first token p95 latency"
                )
            ]
        ))
        
        # End-to-end turn latency SLO: p95 < 3s
        self.add_slo_target(SLOTarget(
            name="e2e_turn_latency",
            description="End-to-end turn p95 latency should be under 3 seconds",
            target_value=3.0,
            time_window="5m",
            thresholds=[
                SLOThreshold(
                    name="e2e_p95_latency",
                    metric_name="total_turn_time_seconds",
                    threshold_value=3.0,
                    comparison="less_than",
                    warning_threshold=2.5,
                    critical_threshold=3.0,
                    description="End-to-end turn p95 latency"
                )
            ]
        ))
        
        # Success rate SLO: > 99%
        self.add_slo_target(SLOTarget(
            name="success_rate",
            description="Request success rate should be above 99%",
            target_value=0.99,
            time_window="5m",
            thresholds=[
                SLOThreshold(
                    name="success_rate_threshold",
                    metric_name="success_rate",
                    threshold_value=0.99,
                    comparison="greater_than",
                    warning_threshold=0.95,
                    critical_threshold=0.99,
                    description="Request success rate"
                )
            ]
        ))
        
        # Memory quality SLO: context usage rate > 70%
        self.add_slo_target(SLOTarget(
            name="memory_quality",
            description="Memory context usage rate should be above 70%",
            target_value=0.70,
            time_window="10m",
            thresholds=[
                SLOThreshold(
                    name="context_usage_rate",
                    metric_name="memory_context_usage_rate",
                    threshold_value=0.70,
                    comparison="greater_than",
                    warning_threshold=0.60,
                    critical_threshold=0.70,
                    description="Memory context usage rate"
                )
            ]
        ))
    
    def _init_default_alert_rules(self):
        """Initialize default alert rules"""
        
        # Critical latency alerts
        self.add_alert_rule(AlertRule(
            name="vector_latency_critical",
            condition="vector_p95_latency > 0.050",
            severity=AlertSeverity.CRITICAL,
            message="Vector query p95 latency exceeded 50ms threshold",
            cooldown_period="2m"
        ))
        
        self.add_alert_rule(AlertRule(
            name="llm_latency_critical",
            condition="first_token_p95_latency > 1.2",
            severity=AlertSeverity.CRITICAL,
            message="LLM first token p95 latency exceeded 1.2s threshold",
            cooldown_period="2m"
        ))
        
        self.add_alert_rule(AlertRule(
            name="e2e_latency_critical",
            condition="e2e_p95_latency > 3.0",
            severity=AlertSeverity.CRITICAL,
            message="End-to-end turn p95 latency exceeded 3s threshold",
            cooldown_period="2m"
        ))
        
        # Warning latency alerts
        self.add_alert_rule(AlertRule(
            name="vector_latency_warning",
            condition="vector_p95_latency > 0.040",
            severity=AlertSeverity.WARNING,
            message="Vector query p95 latency approaching threshold (>40ms)",
            cooldown_period="5m"
        ))
        
        self.add_alert_rule(AlertRule(
            name="llm_latency_warning",
            condition="first_token_p95_latency > 1.0",
            severity=AlertSeverity.WARNING,
            message="LLM first token p95 latency approaching threshold (>1s)",
            cooldown_period="5m"
        ))
        
        # Success rate alerts
        self.add_alert_rule(AlertRule(
            name="success_rate_critical",
            condition="success_rate < 0.99",
            severity=AlertSeverity.CRITICAL,
            message="Request success rate below 99%",
            cooldown_period="1m"
        ))
        
        self.add_alert_rule(AlertRule(
            name="success_rate_warning",
            condition="success_rate < 0.95",
            severity=AlertSeverity.WARNING,
            message="Request success rate below 95%",
            cooldown_period="3m"
        ))
        
        # Memory quality alerts
        self.add_alert_rule(AlertRule(
            name="memory_quality_warning",
            condition="context_usage_rate < 0.70",
            severity=AlertSeverity.WARNING,
            message="Memory context usage rate below 70%",
            cooldown_period="10m"
        ))
    
    def add_slo_target(self, slo_target: SLOTarget):
        """Add an SLO target"""
        self.slo_targets[slo_target.name] = slo_target
        logger.info(f"Added SLO target: {slo_target.name}")
    
    def add_alert_rule(self, alert_rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[alert_rule.name] = alert_rule
        logger.info(f"Added alert rule: {alert_rule.name}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a metric value"""
        self.metric_buffers[metric_name].add_value(value, timestamp)
    
    def get_metric_percentile(self, metric_name: str, percentile: float, 
                            window_seconds: int = 300) -> Optional[float]:
        """Get percentile for a metric"""
        return self.metric_buffers[metric_name].get_percentile(percentile, window_seconds)
    
    def get_metric_average(self, metric_name: str, window_seconds: int = 300) -> Optional[float]:
        """Get average for a metric"""
        return self.metric_buffers[metric_name].get_average(window_seconds)
    
    def calculate_success_rate(self, window_seconds: int = 300) -> Optional[float]:
        """Calculate success rate from request metrics"""
        success_count = self.metric_buffers["requests_success"].get_count(window_seconds)
        error_count = self.metric_buffers["requests_error"].get_count(window_seconds)
        total_count = success_count + error_count
        
        if total_count == 0:
            return None
        
        return success_count / total_count
    
    def evaluate_slo_targets(self) -> List[SLOViolation]:
        """Evaluate all SLO targets and return violations"""
        violations = []
        
        for slo_name, slo_target in self.slo_targets.items():
            if not slo_target.enabled:
                continue
            
            for threshold in slo_target.thresholds:
                violation = self._evaluate_threshold(slo_target, threshold)
                if violation:
                    violations.append(violation)
        
        return violations
    
    def _evaluate_threshold(self, slo_target: SLOTarget, threshold: SLOThreshold) -> Optional[SLOViolation]:
        """Evaluate a single threshold"""
        window_seconds = self._parse_time_window(threshold.time_window)
        
        # Get metric value based on threshold type
        if "p95" in threshold.name.lower():
            actual_value = self.get_metric_percentile(threshold.metric_name, 95, window_seconds)
        elif "success_rate" in threshold.metric_name:
            actual_value = self.calculate_success_rate(window_seconds)
        else:
            actual_value = self.get_metric_average(threshold.metric_name, window_seconds)
        
        if actual_value is None:
            return None
        
        # Check if threshold is violated
        violated = False
        severity = AlertSeverity.INFO
        
        if threshold.comparison == "less_than":
            if actual_value > threshold.threshold_value:
                violated = True
                severity = AlertSeverity.CRITICAL
            elif threshold.warning_threshold and actual_value > threshold.warning_threshold:
                violated = True
                severity = AlertSeverity.WARNING
        elif threshold.comparison == "greater_than":
            if actual_value < threshold.threshold_value:
                violated = True
                severity = AlertSeverity.CRITICAL
            elif threshold.warning_threshold and actual_value < threshold.warning_threshold:
                violated = True
                severity = AlertSeverity.WARNING
        
        if violated:
            return SLOViolation(
                slo_name=slo_target.name,
                threshold_name=threshold.name,
                actual_value=actual_value,
                threshold_value=threshold.threshold_value,
                severity=severity,
                timestamp=datetime.utcnow(),
                metadata={
                    "metric_name": threshold.metric_name,
                    "comparison": threshold.comparison,
                    "time_window": threshold.time_window
                }
            )
        
        return None
    
    def _parse_time_window(self, time_window: str) -> int:
        """Parse time window string to seconds"""
        if time_window.endswith('s'):
            return int(time_window[:-1])
        elif time_window.endswith('m'):
            return int(time_window[:-1]) * 60
        elif time_window.endswith('h'):
            return int(time_window[:-1]) * 3600
        else:
            return int(time_window)
    
    def trigger_alert(self, violation: SLOViolation):
        """Trigger an alert for an SLO violation"""
        alert_id = f"{violation.slo_name}_{violation.threshold_name}_{int(time.time())}"
        
        # Check if there's a matching alert rule
        matching_rule = None
        for rule_name, rule in self.alert_rules.items():
            if violation.threshold_name in rule.condition or violation.slo_name in rule.condition:
                matching_rule = rule
                break
        
        if not matching_rule:
            # Create a default alert rule
            matching_rule = AlertRule(
                name=f"default_{violation.threshold_name}",
                condition=f"{violation.threshold_name} violated",
                severity=violation.severity,
                message=f"SLO violation: {violation.slo_name} - {violation.threshold_name}"
            )
        
        # Check cooldown period
        if self._is_in_cooldown(matching_rule.name):
            return
        
        alert = Alert(
            id=alert_id,
            rule_name=matching_rule.name,
            severity=violation.severity,
            message=matching_rule.message,
            timestamp=datetime.utcnow(),
            metadata={
                "slo_name": violation.slo_name,
                "threshold_name": violation.threshold_name,
                "actual_value": violation.actual_value,
                "threshold_value": violation.threshold_value,
                "violation_metadata": violation.metadata
            }
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        logger.warning(f"Alert triggered: {alert.message}", extra={
            "alert_id": alert_id,
            "severity": alert.severity.value,
            "slo_name": violation.slo_name,
            "actual_value": violation.actual_value,
            "threshold_value": violation.threshold_value
        })
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if alert rule is in cooldown period"""
        rule = self.alert_rules.get(rule_name)
        if not rule:
            return False
        
        cooldown_seconds = self._parse_time_window(rule.cooldown_period)
        cutoff = datetime.utcnow() - timedelta(seconds=cooldown_seconds)
        
        # Check recent alerts for this rule
        for alert in reversed(self.alert_history):
            if alert.rule_name == rule_name and alert.timestamp > cutoff:
                return True
        
        return False
    
    def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert.message}", extra={
                "alert_id": alert_id,
                "duration": (alert.resolved_at - alert.timestamp).total_seconds()
            })
    
    async def start_monitoring(self, evaluation_interval: int = 60):
        """Start the SLO monitoring loop"""
        self.running = True
        logger.info("Starting SLO monitoring")
        
        while self.running:
            try:
                violations = self.evaluate_slo_targets()
                
                for violation in violations:
                    self.violation_history.append(violation)
                    self.trigger_alert(violation)
                
                await asyncio.sleep(evaluation_interval)
                
            except Exception as e:
                logger.error(f"SLO monitoring error: {e}")
                await asyncio.sleep(evaluation_interval)
    
    def stop_monitoring(self):
        """Stop the SLO monitoring loop"""
        self.running = False
        logger.info("Stopping SLO monitoring")
    
    def get_slo_status(self) -> Dict[str, Any]:
        """Get current SLO status"""
        status = {}
        
        for slo_name, slo_target in self.slo_targets.items():
            if not slo_target.enabled:
                continue
            
            slo_status = {
                "name": slo_name,
                "description": slo_target.description,
                "target_value": slo_target.target_value,
                "status": SLOStatus.HEALTHY.value,
                "thresholds": []
            }
            
            for threshold in slo_target.thresholds:
                window_seconds = self._parse_time_window(threshold.time_window)
                
                if "p95" in threshold.name.lower():
                    current_value = self.get_metric_percentile(threshold.metric_name, 95, window_seconds)
                elif "success_rate" in threshold.metric_name:
                    current_value = self.calculate_success_rate(window_seconds)
                else:
                    current_value = self.get_metric_average(threshold.metric_name, window_seconds)
                
                threshold_status = {
                    "name": threshold.name,
                    "current_value": current_value,
                    "threshold_value": threshold.threshold_value,
                    "status": SLOStatus.HEALTHY.value
                }
                
                if current_value is not None:
                    if threshold.comparison == "less_than":
                        if current_value > threshold.threshold_value:
                            threshold_status["status"] = SLOStatus.CRITICAL.value
                            slo_status["status"] = SLOStatus.CRITICAL.value
                        elif threshold.warning_threshold and current_value > threshold.warning_threshold:
                            threshold_status["status"] = SLOStatus.WARNING.value
                            if slo_status["status"] == SLOStatus.HEALTHY.value:
                                slo_status["status"] = SLOStatus.WARNING.value
                    elif threshold.comparison == "greater_than":
                        if current_value < threshold.threshold_value:
                            threshold_status["status"] = SLOStatus.CRITICAL.value
                            slo_status["status"] = SLOStatus.CRITICAL.value
                        elif threshold.warning_threshold and current_value < threshold.warning_threshold:
                            threshold_status["status"] = SLOStatus.WARNING.value
                            if slo_status["status"] == SLOStatus.HEALTHY.value:
                                slo_status["status"] = SLOStatus.WARNING.value
                else:
                    threshold_status["status"] = SLOStatus.UNKNOWN.value
                
                slo_status["thresholds"].append(threshold_status)
            
            status[slo_name] = slo_status
        
        return status
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for SLO dashboard"""
        return {
            "slo_status": self.get_slo_status(),
            "active_alerts": [
                {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata
                }
                for alert in self.active_alerts.values()
            ],
            "recent_violations": [
                {
                    "slo_name": v.slo_name,
                    "threshold_name": v.threshold_name,
                    "actual_value": v.actual_value,
                    "threshold_value": v.threshold_value,
                    "severity": v.severity.value,
                    "timestamp": v.timestamp.isoformat()
                }
                for v in list(self.violation_history)[-50:]  # Last 50 violations
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

# Global SLO monitor instance
_slo_monitor: Optional[SLOMonitor] = None

def get_slo_monitor() -> SLOMonitor:
    """Get global SLO monitor instance"""
    global _slo_monitor
    if _slo_monitor is None:
        _slo_monitor = SLOMonitor()
    return _slo_monitor

def init_slo_monitor() -> SLOMonitor:
    """Initialize global SLO monitor"""
    global _slo_monitor
    _slo_monitor = SLOMonitor()
    return _slo_monitor

# Default alert callback for logging
def default_alert_callback(alert: Alert):
    """Default alert callback that logs alerts"""
    logger.warning(f"SLO Alert: {alert.message}", extra={
        "alert_id": alert.id,
        "severity": alert.severity.value,
        "rule_name": alert.rule_name,
        "timestamp": alert.timestamp.isoformat(),
        "metadata": alert.metadata
    })

# Export main classes and functions
__all__ = [
    "SLOMonitor",
    "SLOTarget",
    "SLOThreshold", 
    "AlertRule",
    "Alert",
    "SLOViolation",
    "SLOStatus",
    "AlertSeverity",
    "get_slo_monitor",
    "init_slo_monitor",
    "default_alert_callback"
]