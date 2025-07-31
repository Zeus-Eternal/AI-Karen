"""
Comprehensive observability and metrics collection for intelligent authentication system.

This module provides advanced metrics collection, real-time alerting, and security insights
for the intelligent authentication system, integrating with existing Karen infrastructure.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from threading import Lock
import threading

try:
    from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create stub classes for when prometheus is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    class CollectorRegistry:
        def __init__(self): pass
    
    def generate_latest(registry=None): return b""

from .models import (
    AuthContext, AuthAnalysisResult, RiskLevel, SecurityActionType,
    ThreatAnalysis, BehavioralAnalysis, NLPFeatures, EmbeddingAnalysis
)

logger = logging.getLogger(__name__)


class AuthEventType(Enum):
    """Types of authentication events for metrics collection."""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGIN_BLOCKED = "login_blocked"
    TWO_FA_REQUIRED = "two_fa_required"
    ANOMALY_DETECTED = "anomaly_detected"
    THREAT_DETECTED = "threat_detected"
    PROFILE_UPDATED = "profile_updated"
    ML_ANALYSIS_COMPLETED = "ml_analysis_completed"
    ML_ANALYSIS_FAILED = "ml_analysis_failed"


class AlertSeverity(Enum):
    """Alert severity levels for security events."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuthEvent:
    """Authentication event for metrics collection."""
    event_type: AuthEventType
    user_id: Optional[str]
    email: Optional[str]
    client_ip: str
    user_agent: str
    timestamp: datetime
    request_id: str
    
    # Analysis results
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    should_block: Optional[bool] = None
    requires_2fa: Optional[bool] = None
    
    # Processing metadata
    processing_time_ms: Optional[float] = None
    nlp_processing_time_ms: Optional[float] = None
    embedding_processing_time_ms: Optional[float] = None
    anomaly_detection_time_ms: Optional[float] = None
    
    # ML analysis flags
    nlp_analysis_success: Optional[bool] = None
    embedding_analysis_success: Optional[bool] = None
    anomaly_detection_success: Optional[bool] = None
    threat_intelligence_success: Optional[bool] = None
    
    # Geolocation and device info
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    is_usual_location: Optional[bool] = None
    is_known_device: Optional[bool] = None
    is_tor_exit_node: Optional[bool] = None
    is_vpn: Optional[bool] = None
    
    # Threat analysis
    threat_intel_score: Optional[float] = None
    attack_patterns: List[str] = field(default_factory=list)
    similar_attacks_detected: Optional[int] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        if self.risk_level:
            data['risk_level'] = self.risk_level.value
        return data

    @classmethod
    def from_auth_context_and_result(
        cls,
        context: AuthContext,
        result: Optional[AuthAnalysisResult] = None,
        event_type: AuthEventType = AuthEventType.LOGIN_ATTEMPT,
        processing_time_ms: Optional[float] = None
    ) -> 'AuthEvent':
        """Create AuthEvent from AuthContext and AuthAnalysisResult."""
        event = cls(
            event_type=event_type,
            user_id=context.email,  # Using email as user_id for now
            email=context.email,
            client_ip=context.client_ip,
            user_agent=context.user_agent,
            timestamp=context.timestamp,
            request_id=context.request_id,
            processing_time_ms=processing_time_ms,
            is_tor_exit_node=context.is_tor_exit_node,
            is_vpn=context.is_vpn,
            threat_intel_score=context.threat_intel_score
        )
        
        # Add geolocation info if available
        if context.geolocation:
            event.country = context.geolocation.country
            event.region = context.geolocation.region
            event.city = context.geolocation.city
            event.is_usual_location = context.geolocation.is_usual_location
        
        # Add analysis results if available
        if result:
            event.risk_score = result.risk_score
            event.risk_level = result.risk_level
            event.should_block = result.should_block
            event.requires_2fa = result.requires_2fa
            event.nlp_processing_time_ms = result.nlp_features.processing_time * 1000
            event.embedding_processing_time_ms = result.embedding_analysis.processing_time * 1000
            event.nlp_analysis_success = not result.nlp_features.used_fallback
            event.embedding_analysis_success = len(result.embedding_analysis.embedding_vector) > 0
            event.is_known_device = result.behavioral_analysis.is_known_device
            event.attack_patterns = result.threat_analysis.known_attack_patterns
            event.similar_attacks_detected = result.threat_analysis.similar_attacks_detected
        
        return event


@dataclass
class SecurityAlert:
    """Security alert for real-time notifications."""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    timestamp: datetime
    
    # Context information
    user_id: Optional[str] = None
    client_ip: Optional[str] = None
    request_id: Optional[str] = None
    
    # Alert metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Alert lifecycle
    acknowledged: bool = False
    resolved: bool = False
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


@dataclass
class SecurityInsight:
    """Security insight generated from authentication data analysis."""
    insight_id: str
    title: str
    description: str
    severity: AlertSeverity
    category: str  # e.g., "anomaly_detection", "threat_intelligence", "behavioral_analysis"
    timestamp: datetime
    
    # Data supporting the insight
    affected_users: List[str] = field(default_factory=list)
    affected_ips: List[str] = field(default_factory=list)
    time_range: Optional[Dict[str, datetime]] = None
    
    # Metrics and statistics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        if self.time_range:
            data['time_range'] = {
                k: v.isoformat() for k, v in self.time_range.items()
            }
        return data


class PrometheusMetrics:
    """Prometheus metrics for intelligent authentication system."""
    
    def __init__(self, registry=None):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available, metrics will be stubbed")
        
        # Use custom registry if provided, otherwise use default
        self.registry = registry
        registry_kwargs = {'registry': registry} if registry and PROMETHEUS_AVAILABLE else {}
        
        # Authentication event counters
        self.auth_attempts_total = Counter(
            'intelligent_auth_attempts_total',
            'Total number of authentication attempts',
            ['event_type', 'risk_level', 'country', 'outcome'],
            **registry_kwargs
        )
        
        self.auth_blocks_total = Counter(
            'intelligent_auth_blocks_total',
            'Total number of blocked authentication attempts',
            ['reason', 'risk_level', 'country'],
            **registry_kwargs
        )
        
        self.auth_2fa_required_total = Counter(
            'intelligent_auth_2fa_required_total',
            'Total number of 2FA requirements triggered',
            ['risk_level', 'country'],
            **registry_kwargs
        )
        
        # ML processing metrics
        self.ml_processing_duration = Histogram(
            'intelligent_auth_ml_processing_duration_seconds',
            'Time spent on ML processing for authentication',
            ['component', 'success'],
            **registry_kwargs
        )
        
        self.ml_analysis_success_total = Counter(
            'intelligent_auth_ml_analysis_success_total',
            'Total successful ML analyses',
            ['component'],
            **registry_kwargs
        )
        
        self.ml_analysis_failure_total = Counter(
            'intelligent_auth_ml_analysis_failure_total',
            'Total failed ML analyses',
            ['component', 'error_type'],
            **registry_kwargs
        )
        
        # Risk scoring metrics
        self.risk_score_distribution = Histogram(
            'intelligent_auth_risk_score_distribution',
            'Distribution of risk scores',
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            **registry_kwargs
        )
        
        self.risk_level_total = Counter(
            'intelligent_auth_risk_level_total',
            'Total authentication attempts by risk level',
            ['risk_level', 'outcome'],
            **registry_kwargs
        )
        
        # Threat intelligence metrics
        self.threat_detections_total = Counter(
            'intelligent_auth_threat_detections_total',
            'Total threat detections',
            ['threat_type', 'severity', 'source'],
            **registry_kwargs
        )
        
        self.ip_reputation_checks_total = Counter(
            'intelligent_auth_ip_reputation_checks_total',
            'Total IP reputation checks',
            ['result', 'source'],
            **registry_kwargs
        )
        
        # Behavioral analysis metrics
        self.behavioral_anomalies_total = Counter(
            'intelligent_auth_behavioral_anomalies_total',
            'Total behavioral anomalies detected',
            ['anomaly_type', 'severity'],
            **registry_kwargs
        )
        
        self.user_profile_updates_total = Counter(
            'intelligent_auth_user_profile_updates_total',
            'Total user profile updates',
            ['update_type'],
            **registry_kwargs
        )
        
        # System health metrics
        self.component_health = Gauge(
            'intelligent_auth_component_health',
            'Health status of authentication components (1=healthy, 0=unhealthy)',
            ['component'],
            **registry_kwargs
        )
        
        self.cache_hit_rate = Gauge(
            'intelligent_auth_cache_hit_rate',
            'Cache hit rate for various components',
            ['cache_type'],
            **registry_kwargs
        )
        
        # Performance metrics
        self.request_duration = Histogram(
            'intelligent_auth_request_duration_seconds',
            'Total request processing time',
            ['endpoint', 'status'],
            **registry_kwargs
        )
        
        # Alert metrics
        self.security_alerts_total = Counter(
            'intelligent_auth_security_alerts_total',
            'Total security alerts generated',
            ['severity', 'category', 'source'],
            **registry_kwargs
        )
        
        # System info
        self.system_info = Info(
            'intelligent_auth_system_info',
            'System information for intelligent authentication',
            **registry_kwargs
        )


class MetricsAggregator:
    """Aggregates and processes authentication metrics for analysis."""
    
    def __init__(self, retention_hours: int = 168):  # 7 days default
        self.retention_hours = retention_hours
        self.events: deque = deque()
        self.alerts: deque = deque()
        self.insights: deque = deque()
        self._lock = Lock()
        
        # Aggregated statistics
        self.hourly_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(int))
        self.daily_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(int))
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def add_event(self, event: AuthEvent):
        """Add authentication event for aggregation."""
        with self._lock:
            self.events.append(event)
            self._update_statistics(event)
    
    def add_alert(self, alert: SecurityAlert):
        """Add security alert."""
        with self._lock:
            self.alerts.append(alert)
    
    def add_insight(self, insight: SecurityInsight):
        """Add security insight."""
        with self._lock:
            self.insights.append(insight)
    
    def _update_statistics(self, event: AuthEvent):
        """Update aggregated statistics with new event."""
        hour_key = event.timestamp.strftime('%Y-%m-%d-%H')
        day_key = event.timestamp.strftime('%Y-%m-%d')
        
        # Update hourly stats
        self.hourly_stats[hour_key]['total_events'] += 1
        self.hourly_stats[hour_key][f'event_type_{event.event_type.value}'] += 1
        
        if event.risk_level:
            self.hourly_stats[hour_key][f'risk_level_{event.risk_level.value}'] += 1
        
        if event.country:
            self.hourly_stats[hour_key][f'country_{event.country}'] += 1
        
        # Update daily stats
        self.daily_stats[day_key]['total_events'] += 1
        self.daily_stats[day_key][f'event_type_{event.event_type.value}'] += 1
        
        if event.risk_level:
            self.daily_stats[day_key][f'risk_level_{event.risk_level.value}'] += 1
    
    def get_events_in_timerange(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[AuthEvent]:
        """Get events within specified time range."""
        with self._lock:
            return [
                event for event in self.events
                if start_time <= event.timestamp <= end_time
            ]
    
    def get_hourly_stats(self, hours_back: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get hourly statistics for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self._lock:
            return {
                hour_key: stats for hour_key, stats in self.hourly_stats.items()
                if datetime.strptime(hour_key, '%Y-%m-%d-%H') >= cutoff_time
            }
    
    def get_daily_stats(self, days_back: int = 7) -> Dict[str, Dict[str, Any]]:
        """Get daily statistics for the last N days."""
        cutoff_time = datetime.now() - timedelta(days=days_back)
        
        with self._lock:
            return {
                day_key: stats for day_key, stats in self.daily_stats.items()
                if datetime.strptime(day_key, '%Y-%m-%d') >= cutoff_time
            }
    
    def get_recent_alerts(self, hours_back: int = 24) -> List[SecurityAlert]:
        """Get recent security alerts."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self._lock:
            return [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]
    
    def get_recent_insights(self, hours_back: int = 24) -> List[SecurityInsight]:
        """Get recent security insights."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self._lock:
            return [
                insight for insight in self.insights
                if insight.timestamp >= cutoff_time
            ]
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_old_data()
                    time.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error(f"Error in metrics cleanup: {e}")
                    time.sleep(3600)
        
        self._cleanup_task = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_task.start()
    
    def _cleanup_old_data(self):
        """Clean up old data beyond retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self._lock:
            # Clean up events
            while self.events and self.events[0].timestamp < cutoff_time:
                self.events.popleft()
            
            # Clean up alerts
            while self.alerts and self.alerts[0].timestamp < cutoff_time:
                self.alerts.popleft()
            
            # Clean up insights
            while self.insights and self.insights[0].timestamp < cutoff_time:
                self.insights.popleft()
            
            # Clean up hourly stats
            old_hour_keys = [
                key for key in self.hourly_stats.keys()
                if datetime.strptime(key, '%Y-%m-%d-%H') < cutoff_time
            ]
            for key in old_hour_keys:
                del self.hourly_stats[key]
            
            # Clean up daily stats (keep longer)
            daily_cutoff = datetime.now() - timedelta(days=30)
            old_day_keys = [
                key for key in self.daily_stats.keys()
                if datetime.strptime(key, '%Y-%m-%d') < daily_cutoff
            ]
            for key in old_day_keys:
                del self.daily_stats[key]


class AlertingEngine:
    """Real-time alerting engine for security events."""
    
    def __init__(self):
        self.alert_handlers: List[Callable[[SecurityAlert], None]] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self.alert_history: deque = deque(maxlen=10000)
        self._lock = Lock()
        
        # Setup default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alerting rules."""
        self.alert_rules = [
            {
                'name': 'high_risk_login_attempt',
                'condition': lambda event: (
                    event.event_type == AuthEventType.LOGIN_ATTEMPT and
                    event.risk_score and event.risk_score > 0.8
                ),
                'severity': AlertSeverity.HIGH,
                'title': 'High Risk Login Attempt Detected',
                'description': 'A login attempt with high risk score was detected'
            },
            {
                'name': 'multiple_failed_attempts',
                'condition': lambda events: len([
                    e for e in events[-10:] 
                    if e.event_type == AuthEventType.LOGIN_FAILURE
                ]) >= 5,
                'severity': AlertSeverity.MEDIUM,
                'title': 'Multiple Failed Login Attempts',
                'description': 'Multiple failed login attempts detected from same source'
            },
            {
                'name': 'threat_intelligence_hit',
                'condition': lambda event: (
                    event.threat_intel_score and event.threat_intel_score > 0.7
                ),
                'severity': AlertSeverity.HIGH,
                'title': 'Threat Intelligence Hit',
                'description': 'Login attempt from known malicious IP address'
            },
            {
                'name': 'ml_analysis_failure',
                'condition': lambda event: (
                    event.event_type == AuthEventType.ML_ANALYSIS_FAILED
                ),
                'severity': AlertSeverity.MEDIUM,
                'title': 'ML Analysis Failure',
                'description': 'Machine learning analysis failed for authentication request'
            }
        ]
    
    def add_alert_handler(self, handler: Callable[[SecurityAlert], None]):
        """Add alert handler function."""
        self.alert_handlers.append(handler)
    
    def add_alert_rule(self, rule: Dict[str, Any]):
        """Add custom alert rule."""
        required_fields = ['name', 'condition', 'severity', 'title', 'description']
        if not all(field in rule for field in required_fields):
            raise ValueError(f"Alert rule must contain: {required_fields}")
        
        self.alert_rules.append(rule)
    
    def process_event(self, event: AuthEvent, recent_events: List[AuthEvent] = None):
        """Process event and generate alerts if rules match."""
        recent_events = recent_events or []
        
        for rule in self.alert_rules:
            try:
                # Check if rule condition is met
                condition_met = False
                if 'events' in rule['condition'].__code__.co_varnames:
                    # Rule requires multiple events
                    condition_met = rule['condition'](recent_events + [event])
                else:
                    # Rule requires single event
                    condition_met = rule['condition'](event)
                
                if condition_met:
                    alert = self._create_alert(rule, event)
                    self._send_alert(alert)
                    
            except Exception as e:
                logger.error(f"Error processing alert rule '{rule['name']}': {e}")
    
    def _create_alert(self, rule: Dict[str, Any], event: AuthEvent) -> SecurityAlert:
        """Create security alert from rule and event."""
        alert_id = f"{rule['name']}_{event.request_id}_{int(time.time())}"
        
        alert = SecurityAlert(
            alert_id=alert_id,
            severity=rule['severity'],
            title=rule['title'],
            description=rule['description'],
            source='intelligent_auth_alerting',
            timestamp=datetime.now(),
            user_id=event.user_id,
            client_ip=event.client_ip,
            request_id=event.request_id,
            tags=[rule['name']],
            metadata={
                'rule_name': rule['name'],
                'event_type': event.event_type.value,
                'risk_score': event.risk_score,
                'risk_level': event.risk_level.value if event.risk_level else None
            }
        )
        
        return alert
    
    def _send_alert(self, alert: SecurityAlert):
        """Send alert to all registered handlers."""
        with self._lock:
            self.alert_history.append(alert)
        
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(alert))
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        logger.warning(f"Security alert: {alert.severity.value} - {alert.title}")


class SecurityInsightsGenerator:
    """Generates automated security insights from authentication data."""
    
    def __init__(self, metrics_aggregator: MetricsAggregator):
        self.metrics_aggregator = metrics_aggregator
        self.insight_generators = [
            self._generate_anomaly_insights,
            self._generate_threat_intelligence_insights,
            self._generate_behavioral_insights,
            self._generate_performance_insights
        ]
    
    async def generate_insights(self, hours_back: int = 24) -> List[SecurityInsight]:
        """Generate security insights for the specified time period."""
        insights = []
        
        for generator in self.insight_generators:
            try:
                generator_insights = await generator(hours_back)
                insights.extend(generator_insights)
            except Exception as e:
                logger.error(f"Error generating insights: {e}")
        
        return insights
    
    async def _generate_anomaly_insights(self, hours_back: int) -> List[SecurityInsight]:
        """Generate insights from anomaly detection data."""
        insights = []
        
        # Get recent events
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        # Analyze high-risk events
        high_risk_events = [
            e for e in events 
            if e.risk_score and e.risk_score > 0.8
        ]
        
        if len(high_risk_events) > 10:  # Threshold for generating insight
            insight = SecurityInsight(
                insight_id=f"high_risk_anomaly_{int(time.time())}",
                title="Elevated High-Risk Authentication Attempts",
                description=f"Detected {len(high_risk_events)} high-risk authentication attempts in the last {hours_back} hours",
                severity=AlertSeverity.HIGH,
                category="anomaly_detection",
                timestamp=datetime.now(),
                affected_users=list(set(e.user_id for e in high_risk_events if e.user_id)),
                affected_ips=list(set(e.client_ip for e in high_risk_events)),
                time_range={'start': start_time, 'end': end_time},
                metrics={
                    'high_risk_count': len(high_risk_events),
                    'avg_risk_score': sum(e.risk_score for e in high_risk_events) / len(high_risk_events),
                    'unique_users': len(set(e.user_id for e in high_risk_events if e.user_id)),
                    'unique_ips': len(set(e.client_ip for e in high_risk_events))
                },
                recommendations=[
                    "Review and investigate high-risk authentication attempts",
                    "Consider implementing additional security measures for affected users",
                    "Analyze patterns in high-risk events for potential coordinated attacks"
                ]
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_threat_intelligence_insights(self, hours_back: int) -> List[SecurityInsight]:
        """Generate insights from threat intelligence data."""
        insights = []
        
        # Get recent events with threat intelligence hits
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        threat_events = [
            e for e in events 
            if e.threat_intel_score and e.threat_intel_score > 0.5
        ]
        
        if len(threat_events) > 5:
            insight = SecurityInsight(
                insight_id=f"threat_intel_hits_{int(time.time())}",
                title="Multiple Threat Intelligence Hits",
                description=f"Detected {len(threat_events)} authentication attempts from known malicious sources",
                severity=AlertSeverity.HIGH,
                category="threat_intelligence",
                timestamp=datetime.now(),
                affected_ips=list(set(e.client_ip for e in threat_events)),
                time_range={'start': start_time, 'end': end_time},
                metrics={
                    'threat_events_count': len(threat_events),
                    'avg_threat_score': sum(e.threat_intel_score for e in threat_events) / len(threat_events),
                    'unique_ips': len(set(e.client_ip for e in threat_events))
                },
                recommendations=[
                    "Block or monitor IP addresses with high threat intelligence scores",
                    "Investigate potential coordinated attack campaigns",
                    "Update threat intelligence feeds and indicators"
                ]
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_behavioral_insights(self, hours_back: int) -> List[SecurityInsight]:
        """Generate insights from behavioral analysis data."""
        insights = []
        
        # Get recent events
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        # Analyze unusual location patterns
        unusual_location_events = [
            e for e in events 
            if e.is_usual_location is False
        ]
        
        if len(unusual_location_events) > 20:
            insight = SecurityInsight(
                insight_id=f"unusual_locations_{int(time.time())}",
                title="Increased Unusual Location Activity",
                description=f"Detected {len(unusual_location_events)} authentication attempts from unusual locations",
                severity=AlertSeverity.MEDIUM,
                category="behavioral_analysis",
                timestamp=datetime.now(),
                affected_users=list(set(e.user_id for e in unusual_location_events if e.user_id)),
                time_range={'start': start_time, 'end': end_time},
                metrics={
                    'unusual_location_count': len(unusual_location_events),
                    'unique_users': len(set(e.user_id for e in unusual_location_events if e.user_id)),
                    'countries': list(set(e.country for e in unusual_location_events if e.country))
                },
                recommendations=[
                    "Review authentication attempts from unusual locations",
                    "Consider implementing location-based security policies",
                    "Notify users of login attempts from new locations"
                ]
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_performance_insights(self, hours_back: int) -> List[SecurityInsight]:
        """Generate insights from ML performance data."""
        insights = []
        
        # Get recent events
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        # Analyze ML analysis failures
        ml_failures = [
            e for e in events 
            if (e.nlp_analysis_success is False or 
                e.embedding_analysis_success is False or 
                e.anomaly_detection_success is False)
        ]
        
        if len(ml_failures) > len(events) * 0.1:  # More than 10% failure rate
            insight = SecurityInsight(
                insight_id=f"ml_performance_degradation_{int(time.time())}",
                title="ML Analysis Performance Degradation",
                description=f"ML analysis failure rate is {len(ml_failures)/len(events)*100:.1f}% ({len(ml_failures)} failures out of {len(events)} attempts)",
                severity=AlertSeverity.MEDIUM,
                category="performance",
                timestamp=datetime.now(),
                time_range={'start': start_time, 'end': end_time},
                metrics={
                    'total_events': len(events),
                    'ml_failures': len(ml_failures),
                    'failure_rate': len(ml_failures) / len(events) if events else 0,
                    'nlp_failures': len([e for e in ml_failures if e.nlp_analysis_success is False]),
                    'embedding_failures': len([e for e in ml_failures if e.embedding_analysis_success is False])
                },
                recommendations=[
                    "Investigate ML service health and performance",
                    "Check resource availability for ML processing",
                    "Review ML service logs for error patterns"
                ]
            )
            insights.append(insight)
        
        return insights


class AuthObservabilityService:
    """
    Comprehensive observability service for intelligent authentication system.
    
    Provides advanced metrics collection, real-time alerting, security insights generation,
    and performance analytics for the intelligent authentication system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        
        # Create custom registry for testing to avoid conflicts
        self.prometheus_registry = None
        if PROMETHEUS_AVAILABLE:
            self.prometheus_registry = CollectorRegistry()
        
        # Initialize components
        self.prometheus_metrics = PrometheusMetrics(registry=self.prometheus_registry)
        self.metrics_aggregator = MetricsAggregator(
            retention_hours=self.config.get('retention_hours', 168)
        )
        self.alerting_engine = AlertingEngine()
        self.insights_generator = SecurityInsightsGenerator(self.metrics_aggregator)
        
        # Setup default alert handlers
        self._setup_default_alert_handlers()
        
        self.logger.info("AuthObservabilityService initialized")
    
    def _setup_default_alert_handlers(self):
        """Setup default alert handlers."""
        def log_alert_handler(alert: SecurityAlert):
            self.logger.warning(
                f"SECURITY ALERT [{alert.severity.value.upper()}]: {alert.title} - {alert.description}",
                extra={
                    'alert_id': alert.alert_id,
                    'severity': alert.severity.value,
                    'source': alert.source,
                    'user_id': alert.user_id,
                    'client_ip': alert.client_ip,
                    'metadata': alert.metadata
                }
            )
        
        self.alerting_engine.add_alert_handler(log_alert_handler)
    
    # Event Recording Methods
    
    def record_auth_event(
        self,
        context: AuthContext,
        result: Optional[AuthAnalysisResult] = None,
        event_type: AuthEventType = AuthEventType.LOGIN_ATTEMPT,
        processing_time_ms: Optional[float] = None
    ):
        """Record authentication event with comprehensive metrics."""
        # Create event from context and result
        event = AuthEvent.from_auth_context_and_result(
            context, result, event_type, processing_time_ms
        )
        
        # Add to aggregator
        self.metrics_aggregator.add_event(event)
        
        # Update Prometheus metrics
        self._update_prometheus_metrics(event)
        
        # Process for alerts
        recent_events = self.metrics_aggregator.get_events_in_timerange(
            datetime.now() - timedelta(minutes=10),
            datetime.now()
        )
        self.alerting_engine.process_event(event, recent_events)
        
        self.logger.debug(f"Recorded auth event: {event_type.value} for {context.email}")
    
    def record_ml_processing_metrics(
        self,
        component: str,
        duration_ms: float,
        success: bool,
        error_type: Optional[str] = None
    ):
        """Record ML processing performance metrics."""
        # Update Prometheus metrics
        self.prometheus_metrics.ml_processing_duration.labels(
            component=component,
            success=str(success).lower()
        ).observe(duration_ms / 1000.0)
        
        if success:
            self.prometheus_metrics.ml_analysis_success_total.labels(
                component=component
            ).inc()
        else:
            self.prometheus_metrics.ml_analysis_failure_total.labels(
                component=component,
                error_type=error_type or 'unknown'
            ).inc()
    
    def record_threat_detection(
        self,
        threat_type: str,
        severity: str,
        source: str,
        context: Optional[AuthContext] = None
    ):
        """Record threat detection event."""
        self.prometheus_metrics.threat_detections_total.labels(
            threat_type=threat_type,
            severity=severity,
            source=source
        ).inc()
        
        # Create alert if high severity
        if severity in ['high', 'critical']:
            alert = SecurityAlert(
                alert_id=f"threat_{threat_type}_{int(time.time())}",
                severity=AlertSeverity.HIGH if severity == 'high' else AlertSeverity.CRITICAL,
                title=f"Threat Detected: {threat_type}",
                description=f"Threat of type '{threat_type}' detected from source '{source}'",
                source='threat_detection',
                timestamp=datetime.now(),
                user_id=context.email if context else None,
                client_ip=context.client_ip if context else None,
                tags=[threat_type, severity],
                metadata={'threat_type': threat_type, 'source': source}
            )
            self.metrics_aggregator.add_alert(alert)
            self.alerting_engine._send_alert(alert)
    
    def record_component_health(self, component: str, is_healthy: bool):
        """Record component health status."""
        self.prometheus_metrics.component_health.labels(
            component=component
        ).set(1.0 if is_healthy else 0.0)
    
    def record_cache_metrics(self, cache_type: str, hit_rate: float):
        """Record cache performance metrics."""
        self.prometheus_metrics.cache_hit_rate.labels(
            cache_type=cache_type
        ).set(hit_rate)
    
    def _update_prometheus_metrics(self, event: AuthEvent):
        """Update Prometheus metrics based on auth event."""
        # Authentication attempts
        outcome = 'success' if event.event_type == AuthEventType.LOGIN_SUCCESS else 'failure'
        if event.event_type == AuthEventType.LOGIN_BLOCKED:
            outcome = 'blocked'
        
        self.prometheus_metrics.auth_attempts_total.labels(
            event_type=event.event_type.value,
            risk_level=event.risk_level.value if event.risk_level else 'unknown',
            country=event.country or 'unknown',
            outcome=outcome
        ).inc()
        
        # Risk score distribution
        if event.risk_score is not None:
            self.prometheus_metrics.risk_score_distribution.observe(event.risk_score)
            
            if event.risk_level:
                self.prometheus_metrics.risk_level_total.labels(
                    risk_level=event.risk_level.value,
                    outcome=outcome
                ).inc()
        
        # Blocked attempts
        if event.should_block:
            reason = 'high_risk' if event.risk_score and event.risk_score > 0.8 else 'other'
            self.prometheus_metrics.auth_blocks_total.labels(
                reason=reason,
                risk_level=event.risk_level.value if event.risk_level else 'unknown',
                country=event.country or 'unknown'
            ).inc()
        
        # 2FA requirements
        if event.requires_2fa:
            self.prometheus_metrics.auth_2fa_required_total.labels(
                risk_level=event.risk_level.value if event.risk_level else 'unknown',
                country=event.country or 'unknown'
            ).inc()
        
        # Request duration
        if event.processing_time_ms:
            self.prometheus_metrics.request_duration.labels(
                endpoint='auth_login',
                status='success' if outcome == 'success' else 'error'
            ).observe(event.processing_time_ms / 1000.0)
    
    # Analytics and Insights Methods
    
    async def generate_security_insights(self, hours_back: int = 24) -> List[SecurityInsight]:
        """Generate comprehensive security insights."""
        insights = await self.insights_generator.generate_insights(hours_back)
        
        # Add insights to aggregator
        for insight in insights:
            self.metrics_aggregator.add_insight(insight)
        
        return insights
    
    def get_authentication_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get comprehensive authentication statistics."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        if not events:
            return {'total_events': 0, 'time_range': {'start': start_time, 'end': end_time}}
        
        # Calculate statistics
        total_events = len(events)
        success_events = len([e for e in events if e.event_type == AuthEventType.LOGIN_SUCCESS])
        failure_events = len([e for e in events if e.event_type == AuthEventType.LOGIN_FAILURE])
        blocked_events = len([e for e in events if e.event_type == AuthEventType.LOGIN_BLOCKED])
        
        risk_scores = [e.risk_score for e in events if e.risk_score is not None]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        unique_users = len(set(e.user_id for e in events if e.user_id))
        unique_ips = len(set(e.client_ip for e in events))
        unique_countries = len(set(e.country for e in events if e.country))
        
        # Processing time statistics
        processing_times = [e.processing_time_ms for e in events if e.processing_time_ms]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'total_events': total_events,
            'success_rate': success_events / total_events if total_events > 0 else 0,
            'failure_rate': failure_events / total_events if total_events > 0 else 0,
            'block_rate': blocked_events / total_events if total_events > 0 else 0,
            'avg_risk_score': avg_risk_score,
            'unique_users': unique_users,
            'unique_ips': unique_ips,
            'unique_countries': unique_countries,
            'avg_processing_time_ms': avg_processing_time,
            'time_range': {'start': start_time, 'end': end_time},
            'events_by_type': {
                'login_success': success_events,
                'login_failure': failure_events,
                'login_blocked': blocked_events,
                'login_attempt': len([e for e in events if e.event_type == AuthEventType.LOGIN_ATTEMPT])
            }
        }
    
    def get_threat_intelligence_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get threat intelligence statistics."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        threat_events = [e for e in events if e.threat_intel_score and e.threat_intel_score > 0.5]
        high_threat_events = [e for e in events if e.threat_intel_score and e.threat_intel_score > 0.8]
        
        return {
            'total_threat_hits': len(threat_events),
            'high_threat_hits': len(high_threat_events),
            'threat_hit_rate': len(threat_events) / len(events) if events else 0,
            'avg_threat_score': sum(e.threat_intel_score for e in threat_events) / len(threat_events) if threat_events else 0,
            'malicious_ips': list(set(e.client_ip for e in threat_events)),
            'attack_patterns': list(set(pattern for e in threat_events for pattern in e.attack_patterns)),
            'time_range': {'start': start_time, 'end': end_time}
        }
    
    def get_ml_performance_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get ML processing performance statistics."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        if not events:
            return {'total_events': 0}
        
        nlp_success_rate = len([e for e in events if e.nlp_analysis_success]) / len(events)
        embedding_success_rate = len([e for e in events if e.embedding_analysis_success]) / len(events)
        
        nlp_times = [e.nlp_processing_time_ms for e in events if e.nlp_processing_time_ms]
        embedding_times = [e.embedding_processing_time_ms for e in events if e.embedding_processing_time_ms]
        
        return {
            'total_events': len(events),
            'nlp_success_rate': nlp_success_rate,
            'embedding_success_rate': embedding_success_rate,
            'avg_nlp_processing_time_ms': sum(nlp_times) / len(nlp_times) if nlp_times else 0,
            'avg_embedding_processing_time_ms': sum(embedding_times) / len(embedding_times) if embedding_times else 0,
            'time_range': {'start': start_time, 'end': end_time}
        }
    
    # Alert Management Methods
    
    def add_alert_handler(self, handler: Callable[[SecurityAlert], None]):
        """Add custom alert handler."""
        self.alerting_engine.add_alert_handler(handler)
    
    def add_alert_rule(self, rule: Dict[str, Any]):
        """Add custom alert rule."""
        self.alerting_engine.add_alert_rule(rule)
    
    def get_recent_alerts(self, hours_back: int = 24) -> List[SecurityAlert]:
        """Get recent security alerts."""
        return self.metrics_aggregator.get_recent_alerts(hours_back)
    
    def get_recent_insights(self, hours_back: int = 24) -> List[SecurityInsight]:
        """Get recent security insights."""
        return self.metrics_aggregator.get_recent_insights(hours_back)
    
    # Export Methods
    
    def export_prometheus_metrics(self) -> bytes:
        """Export Prometheus metrics."""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.prometheus_registry)
        else:
            return b"# Prometheus client not available\n"
    
    def export_events_json(self, hours_back: int = 24) -> str:
        """Export events as JSON."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        return json.dumps([event.to_dict() for event in events], indent=2)
    
    def export_alerts_json(self, hours_back: int = 24) -> str:
        """Export alerts as JSON."""
        alerts = self.get_recent_alerts(hours_back)
        return json.dumps([alert.to_dict() for alert in alerts], indent=2)
    
    def export_insights_json(self, hours_back: int = 24) -> str:
        """Export insights as JSON."""
        insights = self.get_recent_insights(hours_back)
        return json.dumps([insight.to_dict() for insight in insights], indent=2)
    
    # Cleanup Methods
    
    def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up AuthObservabilityService...")
        # Cleanup is handled by background threads in components
        self.logger.info("AuthObservabilityService cleanup completed")


# Convenience function for creating observability service
def create_observability_service(config: Optional[Dict[str, Any]] = None) -> AuthObservabilityService:
    """Create and configure observability service."""
    return AuthObservabilityService(config)