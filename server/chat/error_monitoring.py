"""
Error Monitoring for AI-Karen Production Chat System
Provides real-time error tracking, pattern detection, and analytics.
"""

import logging
import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
import statistics

logger = logging.getLogger(__name__)


class ErrorPatternType(Enum):
    """Types of error patterns that can be detected."""
    SPIKE = "spike"
    TREND = "trend"
    CORRELATION = "correlation"
    RECURRING = "recurring"
    CASCADE = "cascade"
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class ErrorPattern:
    """Error pattern information."""
    id: str
    type: ErrorPatternType
    description: str
    confidence: float  # 0-1
    first_seen: datetime
    last_seen: datetime
    affected_components: List[str]
    error_count: int
    severity: ErrorSeverity
    metadata: Dict[str, Any] = field(default_factory=dict)
    detection_rules: List[str] = field(default_factory=list)


@dataclass
class ErrorMetrics:
    """Error metrics for a time period."""
    time_window: timedelta
    total_errors: int
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    errors_by_severity: Dict[str, int] = field(default_factory=dict)
    errors_by_component: Dict[str, int] = field(default_factory=dict)
    error_rate: float  # errors per minute
    average_resolution_time: float  # seconds
    unique_error_types: int
    recurring_errors: int
    cascading_errors: int
    user_impacted_count: int
    top_errors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ErrorAlert:
    """Error alert information."""
    id: str
    pattern: ErrorPattern
    severity: ErrorSeverity
    title: str
    description: str
    affected_components: List[str]
    user_impact: int
    recommended_actions: List[str]
    created_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorMonitoringConfig:
    """Configuration for error monitoring system."""
    
    def __init__(
        self,
        analysis_window_minutes: int = 60,
        pattern_detection_threshold: int = 5,
        spike_threshold_multiplier: float = 2.0,
        trend_window_minutes: int = 30,
        correlation_window_minutes: int = 10,
        recurring_threshold: int = 3,
        cascade_threshold: int = 3,
        anomaly_detection_enabled: bool = True,
        alert_cooldown_minutes: int = 15
    ):
        self.analysis_window = timedelta(minutes=analysis_window_minutes)
        self.pattern_detection_threshold = pattern_detection_threshold
        self.spike_threshold_multiplier = spike_threshold_multiplier
        self.trend_window = timedelta(minutes=trend_window_minutes)
        self.correlation_window = timedelta(minutes=correlation_window_minutes)
        self.recurring_threshold = recurring_threshold
        self.cascade_threshold = cascade_threshold
        self.anomaly_detection_enabled = anomaly_detection_enabled
        self.alert_cooldown = timedelta(minutes=alert_cooldown_minutes)


class ErrorMonitoringService:
    """
    Error monitoring service for real-time error tracking and analysis.
    
    Features:
    - Real-time error collection
    - Pattern detection and analysis
    - Automatic alerting
    - Metrics calculation
    - Trend analysis
    - Performance impact assessment
    """
    
    def __init__(self, config: Optional[ErrorMonitoringConfig] = None):
        self.config = config or ErrorMonitoringConfig()
        self.error_history: List[Dict[str, Any]] = []
        self.patterns: List[ErrorPattern] = []
        self.alerts: List[ErrorAlert] = []
        self.handlers: Dict[str, List[Callable]] = {}
        self.metrics_cache: Dict[str, ErrorMetrics] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        self.lock = asyncio.Lock()
        
        # Background tasks
        self._analysis_task = None
        self._cleanup_task = None
        
        logger.info("Error monitoring service initialized")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for error monitoring events."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Registered error monitoring handler for event: {event_type}")
    
    async def record_error(
        self,
        error_id: str,
        error_type: str,
        category: str,
        severity: str,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        message: str,
        technical_details: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Record an error for monitoring and analysis.
        
        Args:
            error_id: Unique error identifier
            error_type: Type of error
            category: Error category
            severity: Error severity
            component: Component where error occurred
            user_id: User ID
            session_id: Session ID
            request_id: Request ID
            message: Error message
            technical_details: Technical details
            stack_trace: Stack trace
            metadata: Additional metadata
            timestamp: When error occurred
        """
        async with self.lock:
            error_record = {
                "id": error_id,
                "type": error_type,
                "category": category,
                "severity": severity,
                "component": component,
                "user_id": user_id,
                "session_id": session_id,
                "request_id": request_id,
                "message": message,
                "technical_details": technical_details,
                "stack_trace": stack_trace,
                "metadata": metadata or {},
                "timestamp": timestamp or datetime.now(timezone.utc)
            }
            
            self.error_history.append(error_record)
            
            # Keep only recent errors (based on analysis window)
            cutoff_time = datetime.now(timezone.utc) - self.config.analysis_window
            self.error_history = [
                error for error in self.error_history
                if error["timestamp"] > cutoff_time
            ]
            
            # Update metrics cache
            self._invalidate_metrics_cache()
            
            logger.debug(f"Recorded error: {error_id} - {message}")
        
        # Notify handlers
        await self._notify_handlers("error_recorded", {
            "error_id": error_id,
            "error_type": error_type,
            "category": category,
            "severity": severity,
            "component": component
        })
    
    async def detect_patterns(self) -> List[ErrorPattern]:
        """Detect error patterns in the recent error history."""
        if len(self.error_history) < self.config.pattern_detection_threshold:
            return []
        
        patterns = []
        
        # Detect spikes
        spike_patterns = await self._detect_spike_patterns()
        patterns.extend(spike_patterns)
        
        # Detect trends
        trend_patterns = await self._detect_trend_patterns()
        patterns.extend(trend_patterns)
        
        # Detect correlations
        correlation_patterns = await self._detect_correlation_patterns()
        patterns.extend(correlation_patterns)
        
        # Detect recurring errors
        recurring_patterns = await self._detect_recurring_errors()
        patterns.extend(recurring_patterns)
        
        # Detect cascades
        cascade_patterns = await self._detect_cascade_patterns()
        patterns.extend(cascade_patterns)
        
        # Detect anomalies
        if self.config.anomaly_detection_enabled:
            anomaly_patterns = await self._detect_anomalies()
            patterns.extend(anomaly_patterns)
        
        # Update stored patterns
        self.patterns = patterns
        
        logger.info(f"Detected {len(patterns)} error patterns")
        
        return patterns
    
    async def _detect_spike_patterns(self) -> List[ErrorPattern]:
        """Detect error count spikes."""
        patterns = []
        
        # Group errors by minute
        errors_by_minute = {}
        for error in self.error_history:
            minute_key = error["timestamp"].strftime("%Y-%m-%d %H:%M")
            if minute_key not in errors_by_minute:
                errors_by_minute[minute_key] = []
            errors_by_minute[minute_key].append(error)
        
        # Calculate baseline and detect spikes
        error_counts = [len(errors) for errors in errors_by_minute.values()]
        if len(error_counts) < 3:
            return patterns  # Need at least 3 data points
        
        baseline = statistics.median(error_counts)
        threshold = baseline * self.config.spike_threshold_multiplier
        
        for minute, errors in errors_by_minute.items():
            if len(errors) > threshold:
                patterns.append(ErrorPattern(
                    id=f"spike_{minute}_{int(time.time())}",
                    type=ErrorPatternType.SPIKE,
                    description=f"Error spike detected: {len(errors)} errors in {minute} (baseline: {baseline:.1f})",
                    confidence=min(1.0, (len(errors) / threshold) - 1.0),
                    first_seen=min(error["timestamp"] for error in errors),
                    last_seen=max(error["timestamp"] for error in errors),
                    affected_components=list(set(error.get("component") for error in errors if error.get("component"))),
                    error_count=len(errors),
                    severity=ErrorSeverity.HIGH,
                    metadata={
                        "minute": minute,
                        "error_count": len(errors),
                        "baseline": baseline,
                        "threshold": threshold
                    },
                    detection_rules=["spike_threshold"]
                ))
        
        return patterns
    
    async def _detect_trend_patterns(self) -> List[ErrorPattern]:
        """Detect increasing or decreasing error trends."""
        patterns = []
        
        # Group errors by time windows
        current_time = datetime.now(timezone.utc)
        windows = []
        
        for i in range(5):  # Last 5 windows
            window_end = current_time - timedelta(minutes=i * self.config.trend_window.total_seconds() / 60)
            window_start = window_end - self.config.trend_window
            
            window_errors = [
                error for error in self.error_history
                if window_start <= error["timestamp"] < window_end
            ]
            
            if window_errors:
                windows.append({
                    "start": window_start,
                    "end": window_end,
                    "count": len(window_errors),
                    "errors": window_errors
                })
        
        if len(windows) < 3:
            return patterns  # Need at least 3 windows for trend analysis
        
        # Calculate trend
        counts = [w["count"] for w in windows]
        if len(set(counts)) == 1:  # No trend if all counts are the same
            return patterns
        
        # Simple linear trend detection
        is_increasing = all(counts[i] <= counts[i+1] for i in range(len(counts)-1))
        is_decreasing = all(counts[i] >= counts[i+1] for i in range(len(counts)-1))
        
        if is_increasing or is_decreasing:
            trend_direction = "increasing" if is_increasing else "decreasing"
            trend_strength = abs(counts[-1] - counts[0]) / len(counts)
            
            patterns.append(ErrorPattern(
                id=f"trend_{trend_direction}_{int(time.time())}",
                type=ErrorPatternType.TREND,
                description=f"Error trend detected: {trend_direction} trend with strength {trend_strength:.2f}",
                confidence=min(1.0, trend_strength * 2),
                first_seen=windows[0]["start"],
                last_seen=windows[-1]["end"],
                affected_components=list(set(
                    error.get("component") 
                    for window in windows 
                    for error in window["errors"]
                    if error.get("component")
                )),
                error_count=sum(w["count"] for w in windows),
                severity=ErrorSeverity.MEDIUM if trend_strength < 0.5 else ErrorSeverity.HIGH,
                metadata={
                    "trend_direction": trend_direction,
                    "trend_strength": trend_strength,
                    "windows": len(windows)
                },
                detection_rules=["trend_analysis"]
            ))
        
        return patterns
    
    async def _detect_correlation_patterns(self) -> List[ErrorPattern]:
        """Detect correlated errors across components."""
        patterns = []
        
        # Group errors by time windows
        current_time = datetime.now(timezone.utc)
        correlation_window_start = current_time - self.config.correlation_window
        
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] > correlation_window_start
        ]
        
        if len(recent_errors) < 10:
            return patterns  # Need minimum errors for correlation
        
        # Find correlated errors (errors that occur close together in time)
        time_sorted_errors = sorted(recent_errors, key=lambda e: e["timestamp"])
        
        for i in range(len(time_sorted_errors)):
            current_error = time_sorted_errors[i]
            
            # Look for errors that occurred within 1 minute
            correlated_errors = [
                error for error in time_sorted_errors[i+1:i+10]
                if (error["timestamp"] - current_error["timestamp"]).total_seconds() <= 60
            ]
            
            if len(correlated_errors) >= 3:  # At least 3 correlated errors
                components = list(set(
                    [current_error.get("component")] + 
                    [error.get("component") for error in correlated_errors if error.get("component")]
                ))
                
                if len(components) >= 2:  # At least 2 different components
                    patterns.append(ErrorPattern(
                        id=f"correlation_{int(current_error['timestamp'].timestamp())}_{i}",
                        type=ErrorPatternType.CORRELATION,
                        description=f"Correlated errors detected across {len(components)} components",
                        confidence=min(1.0, len(correlated_errors) / 5.0),
                        first_seen=current_error["timestamp"],
                        last_seen=max(error["timestamp"] for error in correlated_errors),
                        affected_components=components,
                        error_count=len(correlated_errors) + 1,
                        severity=ErrorSeverity.MEDIUM,
                        metadata={
                            "primary_error": current_error["id"],
                            "correlated_errors": [error["id"] for error in correlated_errors],
                            "time_window_seconds": 60
                        },
                        detection_rules=["temporal_correlation"]
                    ))
        
        return patterns
    
    async def _detect_recurring_errors(self) -> List[ErrorPattern]:
        """Detect recurring error types."""
        patterns = []
        
        # Group errors by type and component
        error_groups = {}
        for error in self.error_history:
            key = f"{error['type']}_{error.get('component', 'unknown')}"
            if key not in error_groups:
                error_groups[key] = []
            error_groups[key].append(error)
        
        # Find recurring errors
        for key, errors in error_groups.items():
            if len(errors) >= self.config.recurring_threshold:
                first_seen = min(error["timestamp"] for error in errors)
                last_seen = max(error["timestamp"] for error in errors)
                frequency = len(errors)
                
                patterns.append(ErrorPattern(
                    id=f"recurring_{key}_{int(time.time())}",
                    type=ErrorPatternType.RECURRING,
                    description=f"Recurring error detected: {errors[0]['type']} occurred {frequency} times",
                    confidence=min(1.0, frequency / 10.0),
                    first_seen=first_seen,
                    last_seen=last_seen,
                    affected_components=[errors[0].get("component")],
                    error_count=frequency,
                    severity=ErrorSeverity.MEDIUM,
                    metadata={
                        "error_type": errors[0]["type"],
                        "component": errors[0].get("component"),
                        "frequency": frequency,
                        "time_span_days": (last_seen - first_seen).days
                    },
                    detection_rules=["frequency_threshold"]
                ))
        
        return patterns
    
    async def _detect_cascade_patterns(self) -> List[ErrorPattern]:
        """Detect cascading errors (one error causing others)."""
        patterns = []
        
        # Look for error chains
        time_sorted_errors = sorted(self.error_history, key=lambda e: e["timestamp"])
        
        for i in range(len(time_sorted_errors) - self.config.cascade_threshold + 1):
            window = time_sorted_errors[i:i+self.config.cascade_threshold+1]
            
            # Check if errors occurred in rapid succession
            time_diffs = [
                (window[j+1]["timestamp"] - window[j]["timestamp"]).total_seconds()
                for j in range(len(window) - 1)
            ]
            
            if all(diff < 30 for diff in time_diffs):  # All within 30 seconds
                components = list(set(error.get("component") for error in window if error.get("component")))
                
                if len(components) >= 2:  # At least 2 different components
                    patterns.append(ErrorPattern(
                        id=f"cascade_{int(window[0]['timestamp'].timestamp())}_{i}",
                        type=ErrorPatternType.CASCADE,
                        description=f"Cascade detected: {len(window)} errors across {len(components)} components in {time_diffs[0]:.1f}s",
                        confidence=0.8,
                        first_seen=window[0]["timestamp"],
                        last_seen=window[-1]["timestamp"],
                        affected_components=components,
                        error_count=len(window),
                        severity=ErrorSeverity.HIGH,
                        metadata={
                            "cascade_length": len(window),
                            "components": components,
                            "time_span_seconds": time_diffs[-1],
                            "error_chain": [error["id"] for error in window]
                        },
                        detection_rules=["rapid_succession"]
                    ))
        
        return patterns
    
    async def _detect_anomalies(self) -> List[ErrorPattern]:
        """Detect anomalous error patterns using statistical analysis."""
        patterns = []
        
        if len(self.error_history) < 20:
            return patterns  # Need sufficient data for anomaly detection
        
        # Analyze error intervals
        time_sorted_errors = sorted(self.error_history, key=lambda e: e["timestamp"])
        
        if len(time_sorted_errors) < 2:
            return patterns
        
        intervals = [
            (time_sorted_errors[i+1]["timestamp"] - time_sorted_errors[i]["timestamp"]).total_seconds()
            for i in range(len(time_sorted_errors) - 1)
        ]
        
        if len(intervals) < 5:
            return patterns
        
        # Calculate statistics
        mean_interval = statistics.mean(intervals)
        stdev_interval = statistics.stdev(intervals)
        
        # Find anomalies (intervals > 2 standard deviations from mean)
        threshold = mean_interval + (2 * stdev_interval)
        
        for i in range(len(intervals)):
            if intervals[i] > threshold:
                patterns.append(ErrorPattern(
                    id=f"anomaly_{int(time_sorted_errors[i]['timestamp'].timestamp())}_{i}",
                    type=ErrorPatternType.ANOMALY,
                    description=f"Anomalous error interval detected: {intervals[i]:.1f}s (normal: {mean_interval:.1f}±{stdev_interval:.1f}s)",
                    confidence=min(1.0, (intervals[i] - mean_interval) / stdev_interval / 2),
                    first_seen=time_sorted_errors[i]["timestamp"],
                    last_seen=time_sorted_errors[i+1]["timestamp"],
                    affected_components=[time_sorted_errors[i].get("component")],
                    error_count=2,
                    severity=ErrorSeverity.MEDIUM,
                    metadata={
                        "interval": intervals[i],
                        "mean_interval": mean_interval,
                        "stdev_interval": stdev_interval,
                        "threshold": threshold,
                        "z_score": (intervals[i] - mean_interval) / stdev_interval
                    },
                    detection_rules=["statistical_anomaly"]
                ))
        
        return patterns
    
    async def create_alert(self, pattern: ErrorPattern) -> ErrorAlert:
        """Create an alert from a detected pattern."""
        # Check cooldown
        alert_key = f"{pattern.type.value}_{pattern.affected_components[0] if pattern.affected_components else 'unknown'}"
        current_time = datetime.now(timezone.utc)
        
        if (alert_key in self.last_alert_times and 
            (current_time - self.last_alert_times[alert_key]).total_seconds() < self.config.alert_cooldown.total_seconds()):
            logger.info(f"Alert suppressed due to cooldown: {alert_key}")
            return None
        
        alert = ErrorAlert(
            id=f"alert_{int(time.time())}_{pattern.id}",
            pattern=pattern,
            severity=pattern.severity,
            title=self._generate_alert_title(pattern),
            description=pattern.description,
            affected_components=pattern.affected_components,
            user_impact=self._calculate_user_impact(pattern),
            recommended_actions=self._generate_recommended_actions(pattern),
            created_at=current_time
        )
        
        self.last_alert_times[alert_key] = current_time
        self.alerts.append(alert)
        
        # Keep only recent alerts (last 1000)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        return alert
    
    def _generate_alert_title(self, pattern: ErrorPattern) -> str:
        """Generate appropriate alert title based on pattern type."""
        title_map = {
            ErrorPatternType.SPIKE: "Error Spike Detected",
            ErrorPatternType.TREND: "Error Trend Detected",
            ErrorPatternType.CORRELATION: "Correlated Errors Detected",
            ErrorPatternType.RECURRING: "Recurring Error Detected",
            ErrorPatternType.CASCADE: "Error Cascade Detected",
            ErrorPatternType.ANOMALY: "Anomalous Error Pattern Detected"
        }
        
        return title_map.get(pattern.type, "Error Pattern Detected")
    
    def _calculate_user_impact(self, pattern: ErrorPattern) -> int:
        """Calculate the number of users impacted by a pattern."""
        # In a real implementation, this would analyze user sessions
        # For now, estimate based on error count and severity
        base_impact = pattern.error_count
        
        if pattern.severity == ErrorSeverity.CRITICAL:
            return base_impact * 10
        elif pattern.severity == ErrorSeverity.HIGH:
            return base_impact * 5
        elif pattern.severity == ErrorSeverity.MEDIUM:
            return base_impact * 2
        else:
            return max(1, base_impact)
    
    def _generate_recommended_actions(self, pattern: ErrorPattern) -> List[str]:
        """Generate recommended actions based on pattern type."""
        actions_map = {
            ErrorPatternType.SPIKE: [
                "Investigate the cause of the error spike",
                "Check system resources and performance",
                "Consider scaling up resources if spike persists"
            ],
            ErrorPatternType.TREND: [
                "Analyze the root cause of the trend",
                "Review recent changes to the affected components",
                "Implement preventive measures if trend is increasing"
            ],
            ErrorPatternType.CORRELATION: [
                "Investigate the relationship between affected components",
                "Check for shared dependencies or resources",
                "Review system architecture for potential single points of failure"
            ],
            ErrorPatternType.RECURRING: [
                "Identify and fix the root cause of the recurring error",
                "Implement additional monitoring for the specific error type",
                "Consider adding automated recovery mechanisms"
            ],
            ErrorPatternType.CASCADE: [
                "Implement circuit breakers to prevent cascades",
                "Review error handling and isolation mechanisms",
                "Add more robust error boundaries between components"
            ],
            ErrorPatternType.ANOMALY: [
                "Investigate the unusual error pattern",
                "Review system logs for additional context",
                "Monitor for related anomalous behavior"
            ]
        }
        
        return actions_map.get(pattern.type, [
            "Investigate the detected error pattern",
            "Review system logs and metrics",
            "Implement appropriate remediation measures"
        ])
    
    async def calculate_metrics(self, time_window: Optional[timedelta] = None) -> ErrorMetrics:
        """Calculate error metrics for a time window."""
        window = time_window or self.config.analysis_window
        cutoff_time = datetime.now(timezone.utc) - window
        
        # Filter errors in time window
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] > cutoff_time
        ]
        
        if not recent_errors:
            return ErrorMetrics(
                time_window=window,
                total_errors=0,
                errors_by_category={},
                errors_by_severity={},
                errors_by_component={},
                error_rate=0.0,
                average_resolution_time=0.0,
                unique_error_types=0,
                recurring_errors=0,
                cascading_errors=0,
                user_impacted_count=0,
                top_errors=[]
            )
        
        # Calculate basic metrics
        total_errors = len(recent_errors)
        errors_by_category = {}
        errors_by_severity = {}
        errors_by_component = {}
        
        for error in recent_errors:
            category = error["category"]
            severity = error["severity"]
            component = error.get("component", "unknown")
            
            errors_by_category[category] = errors_by_category.get(category, 0) + 1
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + 1
            errors_by_component[component] = errors_by_component.get(component, 0) + 1
        
        # Calculate error rate (errors per minute)
        error_rate = total_errors / max(1, window.total_seconds() / 60)
        
        # Calculate unique error types
        unique_error_types = len(set(error["type"] for error in recent_errors))
        
        # Identify recurring errors (same type occurring 3+ times)
        error_type_counts = {}
        for error in recent_errors:
            error_type = error["type"]
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        recurring_errors = len([count for count in error_type_counts.values() if count >= 3])
        
        # Estimate cascading errors (simplified detection)
        cascading_errors = sum(1 for error in recent_errors if "cascade" in error.get("message", "").lower())
        
        # Estimate user impact (simplified)
        user_impacted_count = len(set(error.get("user_id") for error in recent_errors if error.get("user_id")))
        
        # Get top errors
        error_counts = {}
        for error in recent_errors:
            key = f"{error['type']}_{error.get('component', 'unknown')}"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        top_errors = [
            {
                "type": error["type"],
                "component": error.get("component"),
                "count": count,
                "severity": error["severity"],
                "last_seen": max(error["timestamp"] for error in recent_errors if error["type"] == error["type"])
            }
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for error in recent_errors if f"{error['type']}_{error.get('component', 'unknown')}" == error_type
        ]
        
        return ErrorMetrics(
            time_window=window,
            total_errors=total_errors,
            errors_by_category=errors_by_category,
            errors_by_severity=errors_by_severity,
            errors_by_component=errors_by_component,
            error_rate=error_rate,
            average_resolution_time=0.0,  # Would need resolution time data
            unique_error_types=unique_error_types,
            recurring_errors=recurring_errors,
            cascading_errors=cascading_errors,
            user_impacted_count=user_impacted_count,
            top_errors=top_errors
        )
    
    def _invalidate_metrics_cache(self):
        """Clear the metrics cache."""
        self.metrics_cache.clear()
    
    async def _notify_handlers(self, event_type: str, data: Dict[str, Any]):
        """Notify all registered handlers for an event."""
        handlers = self.handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logger.error(f"Error monitoring handler error for {event_type}: {e}")
    
    async def start_monitoring(self):
        """Start the error monitoring background tasks."""
        if self._analysis_task:
            return  # Already running
        
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Error monitoring background tasks started")
    
    async def stop_monitoring(self):
        """Stop the error monitoring background tasks."""
        if self._analysis_task:
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass
            self._analysis_task = None
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("Error monitoring background tasks stopped")
    
    async def _analysis_loop(self):
        """Background task to continuously analyze errors and detect patterns."""
        while True:
            try:
                # Detect patterns
                patterns = await self.detect_patterns()
                
                # Create alerts for new patterns
                for pattern in patterns:
                    # Check if we already have a similar recent pattern
                    existing_similar = [
                        p for p in self.patterns
                        if (p.type == pattern.type and 
                            p.affected_components == pattern.affected_components and
                            (datetime.now(timezone.utc) - p.last_seen).total_seconds() < 300)  # 5 minutes
                    ]
                    
                    if not existing_similar:
                        alert = await self.create_alert(pattern)
                        if alert:
                            await self._notify_handlers("alert_created", {
                                "alert_id": alert.id,
                                "pattern_type": pattern.type.value,
                                "severity": alert.severity.value
                            })
                
                # Update patterns list
                self.patterns = patterns
                
                # Wait before next analysis
                await asyncio.sleep(60)  # Analyze every minute
                
            except Exception as e:
                logger.error(f"Error analysis loop error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Background task to clean up old data."""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Clean up old error history (keep for 7 days)
                cutoff_time = current_time - timedelta(days=7)
                original_count = len(self.error_history)
                self.error_history = [
                    error for error in self.error_history
                    if error["timestamp"] > cutoff_time
                ]
                
                if len(self.error_history) < original_count:
                    logger.debug(f"Cleaned up {original_count - len(self.error_history)} old error records")
                
                # Clean up old patterns (keep for 24 hours)
                pattern_cutoff = current_time - timedelta(hours=24)
                original_pattern_count = len(self.patterns)
                self.patterns = [
                    pattern for pattern in self.patterns
                    if pattern.last_seen > pattern_cutoff
                ]
                
                if len(self.patterns) < original_pattern_count:
                    logger.debug(f"Cleaned up {original_pattern_count - len(self.patterns)} old patterns")
                
                # Clean up old alerts (keep for 7 days)
                alert_cutoff = current_time - timedelta(days=7)
                original_alert_count = len(self.alerts)
                self.alerts = [
                    alert for alert in self.alerts
                    if alert.created_at > alert_cutoff
                ]
                
                if len(self.alerts) < original_alert_count:
                    logger.debug(f"Cleaned up {original_alert_count - len(self.alerts)} old alerts")
                
                # Clean up old alert times
                old_alert_times = [
                    key for key, time in self.last_alert_times.items()
                    if time < current_time - timedelta(days=1)
                ]
                
                for key in old_alert_times:
                    del self.last_alert_times[key]
                
                # Wait before next cleanup
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error cleanup loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def get_recent_alerts(self, limit: int = 50) -> List[ErrorAlert]:
        """Get recent error alerts."""
        return sorted(self.alerts, key=lambda a: a.created_at, reverse=True)[:limit]
    
    def get_active_patterns(self) -> List[ErrorPattern]:
        """Get currently active error patterns."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        return [
            pattern for pattern in self.patterns
            if pattern.last_seen > cutoff_time
        ]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive error summary for the specified time period."""
        time_window = timedelta(hours=hours)
        metrics = asyncio.run(self.calculate_metrics(time_window))
        
        return {
            "time_window_hours": hours,
            "total_errors": metrics.total_errors,
            "error_rate_per_minute": metrics.error_rate,
            "unique_error_types": metrics.unique_error_types,
            "recurring_errors": metrics.recurring_errors,
            "cascading_errors": metrics.cascading_errors,
            "user_impacted_count": metrics.user_impacted_count,
            "top_error_categories": dict(sorted(metrics.errors_by_category.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_error_components": dict(sorted(metrics.errors_by_component.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_error_severities": dict(sorted(metrics.errors_by_severity.items(), key=lambda x: x[1], reverse=True)[:5]),
            "active_patterns_count": len(self.get_active_patterns()),
            "recent_alerts_count": len(self.get_recent_alerts(10))
        }


# Global error monitoring service instance
error_monitoring_service = ErrorMonitoringService()


def get_error_monitoring_service() -> ErrorMonitoringService:
    """Get the global error monitoring service instance."""
    return error_monitoring_service