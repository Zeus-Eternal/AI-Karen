"""
Error Monitoring and Analytics System

This module provides comprehensive error monitoring, analytics, and pattern detection
for the CoPilot system with intelligent alerting and reporting capabilities.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from threading import Lock

import traceback
from .error_classifier import ErrorClassification, ErrorCategory, ErrorSeverity


class AlertLevel(Enum):
    """Alert levels for error monitoring."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class PatternType(Enum):
    """Types of error patterns to detect."""
    
    SPIKE = "spike"                    # Sudden increase in errors
    TREND = "trend"                    # Gradual increase over time
    CORRELATION = "correlation"          # Errors correlated with events
    RECURRING = "recurring"             # Same error repeats
    CASCADE = "cascade"                  # Errors causing other errors
    THRESHOLD = "threshold"              # Error count exceeds threshold
    ANOMALY = "anomaly"                # Unusual error pattern


@dataclass
class ErrorEvent:
    """Single error event for monitoring."""
    
    timestamp: datetime
    error_type: str
    error_message: str
    classification: ErrorClassification
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorPattern:
    """Detected error pattern."""
    
    pattern_type: PatternType
    description: str
    confidence: float
    first_seen: datetime
    last_seen: datetime
    affected_components: List[str] = field(default_factory=list)
    error_count: int = 0
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorAlert:
    """Error alert for notification."""
    
    alert_level: AlertLevel
    title: str
    message: str
    pattern: Optional[ErrorPattern] = None
    events: List[ErrorEvent] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorMetrics:
    """Metrics for error monitoring."""
    
    total_errors: int = 0
    errors_by_category: Dict[ErrorCategory, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_severity: Dict[ErrorSeverity, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_component: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_operation: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Time-based metrics
    errors_last_hour: int = 0
    errors_last_24h: int = 0
    errors_last_week: int = 0
    
    # Rate metrics
    error_rate_per_minute: float = 0.0
    error_rate_per_hour: float = 0.0
    
    # Pattern metrics
    unique_error_types: int = 0
    recurring_errors: int = 0
    cascading_errors: int = 0


class PatternDetector:
    """Base class for error pattern detection."""
    
    def __init__(self, pattern_type: PatternType):
        self.pattern_type = pattern_type
    
    def detect(self, events: List[ErrorEvent], window_minutes: int = 60) -> List[ErrorPattern]:
        """Detect patterns in error events."""
        raise NotImplementedError
    
    def _get_events_in_window(self, events: List[ErrorEvent], window_minutes: int) -> List[ErrorEvent]:
        """Get events within time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        return [e for e in events if e.timestamp > cutoff_time]


class SpikeDetector(PatternDetector):
    """Detect error spikes (sudden increases)."""
    
    def __init__(self):
        super().__init__(PatternType.SPIKE)
        self.baseline_window = 60  # minutes
        self.spike_threshold = 3.0  # 3x increase
    
    def detect(self, events: List[ErrorEvent], window_minutes: int = 60) -> List[ErrorPattern]:
        """Detect error spikes."""
        patterns = []
        recent_events = self._get_events_in_window(events, window_minutes)
        baseline_events = self._get_events_in_window(events, self.baseline_window)
        
        if not baseline_events:
            return patterns
        
        # Group by component
        component_errors = defaultdict(list)
        for event in recent_events:
            component = event.component or "unknown"
            component_errors[component].append(event)
        
        # Check each component for spikes
        for component, comp_events in component_errors.items():
            recent_count = len(comp_events)
            baseline_count = len([e for e in baseline_events 
                                if (e.component or "unknown") == component])
            
            if baseline_count > 0:
                spike_ratio = recent_count / baseline_count
                if spike_ratio >= self.spike_threshold:
                    patterns.append(ErrorPattern(
                        pattern_type=self.pattern_type,
                        description=f"Error spike detected in {component}: {recent_count} errors (baseline: {baseline_count})",
                        confidence=min(spike_ratio / self.spike_threshold, 1.0),
                        first_seen=min(e.timestamp for e in comp_events),
                        last_seen=max(e.timestamp for e in comp_events),
                        affected_components=[component],
                        error_count=recent_count,
                        severity=ErrorSeverity.HIGH if spike_ratio > 5 else ErrorSeverity.MEDIUM,
                        metadata={
                            "spike_ratio": spike_ratio,
                            "recent_count": recent_count,
                            "baseline_count": baseline_count
                        }
                    ))
        
        return patterns


class RecurringErrorDetector(PatternDetector):
    """Detect recurring errors."""
    
    def __init__(self):
        super().__init__(PatternType.RECURRING)
        self.min_occurrences = 5
        self.time_window = 120  # minutes
    
    def detect(self, events: List[ErrorEvent], window_minutes: int = 60) -> List[ErrorPattern]:
        """Detect recurring errors."""
        patterns = []
        window_events = self._get_events_in_window(events, self.time_window)
        
        # Group by error type and message
        error_groups = defaultdict(list)
        for event in window_events:
            key = (event.error_type, event.error_message[:100])  # First 100 chars
            error_groups[key].append(event)
        
        # Find recurring errors
        for (error_type, error_message), group_events in error_groups.items():
            if len(group_events) >= self.min_occurrences:
                components = list(set(e.component or "unknown" for e in group_events))
                
                patterns.append(ErrorPattern(
                    pattern_type=self.pattern_type,
                    description=f"Recurring error: {error_type} - {error_message[:50]}...",
                    confidence=min(len(group_events) / self.min_occurrences, 1.0),
                    first_seen=min(e.timestamp for e in group_events),
                    last_seen=max(e.timestamp for e in group_events),
                    affected_components=components,
                    error_count=len(group_events),
                    severity=self._calculate_severity(group_events),
                    metadata={
                        "error_type": error_type,
                        "error_message": error_message,
                        "occurrence_count": len(group_events)
                    }
                ))
        
        return patterns
    
    def _calculate_severity(self, events: List[ErrorEvent]) -> ErrorSeverity:
        """Calculate severity based on event severity distribution."""
        if not events:
            return ErrorSeverity.LOW
        
        severity_counts = defaultdict(int)
        for event in events:
            severity_counts[event.classification.severity] += 1
        
        # If any critical errors, mark as critical
        if severity_counts.get(ErrorSeverity.CRITICAL, 0) > 0:
            return ErrorSeverity.CRITICAL
        
        # If many high severity errors, mark as high
        if severity_counts.get(ErrorSeverity.HIGH, 0) >= len(events) * 0.5:
            return ErrorSeverity.HIGH
        
        # Default to medium
        return ErrorSeverity.MEDIUM


class ThresholdDetector(PatternDetector):
    """Detect threshold violations."""
    
    def __init__(self):
        super().__init__(PatternType.THRESHOLD)
        self.thresholds = {
            "total_errors_per_hour": 50,
            "critical_errors_per_hour": 5,
            "component_errors_per_hour": 20,
        }
    
    def detect(self, events: List[ErrorEvent], window_minutes: int = 60) -> List[ErrorPattern]:
        """Detect threshold violations."""
        patterns = []
        window_events = self._get_events_in_window(events, window_minutes)
        
        # Check total error threshold
        if len(window_events) > self.thresholds["total_errors_per_hour"]:
            patterns.append(ErrorPattern(
                pattern_type=self.pattern_type,
                description=f"Total error threshold exceeded: {len(window_events)} errors",
                confidence=1.0,
                first_seen=min(e.timestamp for e in window_events),
                last_seen=max(e.timestamp for e in window_events),
                error_count=len(window_events),
                severity=ErrorSeverity.HIGH,
                metadata={
                    "threshold_type": "total_errors",
                    "threshold": self.thresholds["total_errors_per_hour"],
                    "actual": len(window_events)
                }
            ))
        
        # Check critical error threshold
        critical_errors = [e for e in window_events 
                          if e.classification.severity == ErrorSeverity.CRITICAL]
        if len(critical_errors) > self.thresholds["critical_errors_per_hour"]:
            patterns.append(ErrorPattern(
                pattern_type=self.pattern_type,
                description=f"Critical error threshold exceeded: {len(critical_errors)} critical errors",
                confidence=1.0,
                first_seen=min(e.timestamp for e in critical_errors),
                last_seen=max(e.timestamp for e in critical_errors),
                error_count=len(critical_errors),
                severity=ErrorSeverity.CRITICAL,
                metadata={
                    "threshold_type": "critical_errors",
                    "threshold": self.thresholds["critical_errors_per_hour"],
                    "actual": len(critical_errors)
                }
            ))
        
        # Check component-specific thresholds
        component_errors = defaultdict(list)
        for event in window_events:
            component = event.component or "unknown"
            component_errors[component].append(event)
        
        for component, comp_events in component_errors.items():
            if len(comp_events) > self.thresholds["component_errors_per_hour"]:
                patterns.append(ErrorPattern(
                    pattern_type=self.pattern_type,
                    description=f"Component error threshold exceeded for {component}: {len(comp_events)} errors",
                    confidence=1.0,
                    first_seen=min(e.timestamp for e in comp_events),
                    last_seen=max(e.timestamp for e in comp_events),
                    affected_components=[component],
                    error_count=len(comp_events),
                    severity=ErrorSeverity.HIGH,
                    metadata={
                        "threshold_type": "component_errors",
                        "component": component,
                        "threshold": self.thresholds["component_errors_per_hour"],
                        "actual": len(comp_events)
                    }
                ))
        
        return patterns


class ErrorMonitor:
    """
    Comprehensive error monitoring system with pattern detection and alerting.
    
    Features:
    - Real-time error event collection
    - Multiple pattern detection algorithms
    - Configurable alerting
    - Metrics and analytics
    - Historical analysis
    - Component-based monitoring
    """
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.patterns: List[ErrorPattern] = []
        self.alerts: deque = deque(maxlen=1000)  # Keep last 1k alerts
        self.metrics = ErrorMetrics()
        
        # Pattern detectors
        self.detectors = [
            SpikeDetector(),
            RecurringErrorDetector(),
            ThresholdDetector(),
        ]
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[ErrorAlert], None]] = []
        
        # Threading lock
        self.lock = Lock()
        
        # Background monitoring task
        self.monitoring_task = None
        self.monitoring_interval = 60  # seconds
        self.monitoring_enabled = True
    
    def start_monitoring(self) -> None:
        """Start background monitoring task."""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring task."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
    
    def record_error(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error event for monitoring.
        
        Args:
            error: The exception that occurred
            classification: Error classification result
            context: Additional context
        """
        event = ErrorEvent(
            timestamp=datetime.utcnow(),
            error_type=type(error).__name__,
            error_message=str(error),
            classification=classification,
            context=context or {},
            stack_trace=traceback.format_exc() if hasattr(traceback, 'format_exc') else None,
            request_id=context.get("request_id") if context else None,
            user_id=context.get("user_id") if context else None,
            component=context.get("component") if context else None,
            operation=context.get("operation") if context else None,
            metadata=context.get("metadata", {}) if context else {}
        )
        
        with self.lock:
            self.events.append(event)
            self._update_metrics(event)
    
    def add_alert_callback(self, callback: Callable[[ErrorAlert], None]) -> None:
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[ErrorAlert], None]) -> None:
        """Remove alert callback."""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_recent_events(self, minutes: int = 60) -> List[ErrorEvent]:
        """Get recent error events."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [e for e in self.events if e.timestamp > cutoff_time]
    
    def get_metrics(self) -> ErrorMetrics:
        """Get current error metrics."""
        with self.lock:
            return self.metrics
    
    def get_patterns(self, pattern_type: Optional[PatternType] = None) -> List[ErrorPattern]:
        """Get detected patterns."""
        with self.lock:
            if pattern_type:
                return [p for p in self.patterns if p.pattern_type == pattern_type]
            return list(self.patterns)
    
    def get_alerts(self, alert_level: Optional[AlertLevel] = None) -> List[ErrorAlert]:
        """Get recent alerts."""
        with self.lock:
            if alert_level:
                return [a for a in self.alerts if a.alert_level == alert_level]
            return list(self.alerts)
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring_enabled:
            try:
                await self._detect_patterns()
                await self._generate_alerts()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _detect_patterns(self) -> None:
        """Detect error patterns."""
        recent_events = self.get_recent_events(120)  # Last 2 hours
        
        new_patterns = []
        for detector in self.detectors:
            try:
                detected_patterns = detector.detect(recent_events)
                new_patterns.extend(detected_patterns)
            except Exception as e:
                logging.error(f"Pattern detection failed: {e}")
        
        if new_patterns:
            with self.lock:
                # Remove old patterns of same type
                existing_pattern_types = {p.pattern_type for p in self.patterns}
                for pattern in new_patterns:
                    if pattern.pattern_type in existing_pattern_types:
                        self.patterns = [p for p in self.patterns 
                                       if p.pattern_type != pattern.pattern_type]
                
                self.patterns.extend(new_patterns)
    
    async def _generate_alerts(self) -> None:
        """Generate alerts from patterns and metrics."""
        alerts = []
        
        # Generate alerts from patterns
        for pattern in self.patterns:
            alert = self._create_alert_from_pattern(pattern)
            if alert:
                alerts.append(alert)
        
        # Generate alerts from metrics
        metric_alerts = self._create_alerts_from_metrics()
        alerts.extend(metric_alerts)
        
        if alerts:
            with self.lock:
                self.alerts.extend(alerts)
            
            # Notify callbacks
            for alert in alerts:
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logging.error(f"Alert callback failed: {e}")
    
    def _create_alert_from_pattern(self, pattern: ErrorPattern) -> Optional[ErrorAlert]:
        """Create alert from error pattern."""
        # Determine alert level based on severity
        alert_level_map = {
            ErrorSeverity.LOW: AlertLevel.INFO,
            ErrorSeverity.MEDIUM: AlertLevel.WARNING,
            ErrorSeverity.HIGH: AlertLevel.ERROR,
            ErrorSeverity.CRITICAL: AlertLevel.CRITICAL,
            ErrorSeverity.FATAL: AlertLevel.FATAL,
        }
        
        alert_level = alert_level_map.get(pattern.severity, AlertLevel.WARNING)
        
        return ErrorAlert(
            alert_level=alert_level,
            title=f"Error Pattern Detected: {pattern.pattern_type.value}",
            message=pattern.description,
            pattern=pattern,
            metadata={
                "confidence": pattern.confidence,
                "error_count": pattern.error_count,
                "affected_components": pattern.affected_components
            }
        )
    
    def _create_alerts_from_metrics(self) -> List[ErrorAlert]:
        """Create alerts from metrics."""
        alerts = []
        
        # High error rate alert
        if self.metrics.error_rate_per_minute > 10:  # More than 10 errors per minute
            alerts.append(ErrorAlert(
                alert_level=AlertLevel.ERROR,
                title="High Error Rate",
                message=f"Error rate is {self.metrics.error_rate_per_minute:.1f} errors/minute",
                metadata={
                    "error_rate_per_minute": self.metrics.error_rate_per_minute,
                    "threshold": 10.0
                }
            ))
        
        # Critical error alert
        if self.metrics.errors_by_severity.get(ErrorSeverity.CRITICAL, 0) > 0:
            alerts.append(ErrorAlert(
                alert_level=AlertLevel.CRITICAL,
                title="Critical Errors Detected",
                message=f"{self.metrics.errors_by_severity[ErrorSeverity.CRITICAL]} critical errors detected",
                metadata={
                    "critical_error_count": self.metrics.errors_by_severity[ErrorSeverity.CRITICAL]
                }
            ))
        
        return alerts
    
    def _update_metrics(self, event: ErrorEvent) -> None:
        """Update metrics with new event."""
        self.metrics.total_errors += 1
        self.metrics.errors_by_category[event.classification.category] += 1
        self.metrics.errors_by_severity[event.classification.severity] += 1
        
        if event.component:
            self.metrics.errors_by_component[event.component] += 1
        if event.operation:
            self.metrics.errors_by_operation[event.operation] += 1
        
        # Update time-based metrics
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(weeks=1)
        
        self.metrics.errors_last_hour = len([e for e in self.events if e.timestamp > one_hour_ago])
        self.metrics.errors_last_24h = len([e for e in self.events if e.timestamp > one_day_ago])
        self.metrics.errors_last_week = len([e for e in self.events if e.timestamp > one_week_ago])
        
        # Calculate rates
        self.metrics.error_rate_per_minute = self.metrics.errors_last_hour / 60.0
        self.metrics.error_rate_per_hour = float(self.metrics.errors_last_hour)
        
        # Update pattern metrics
        self.metrics.unique_error_types = len(set(e.error_type for e in self.events))
        # TODO: Calculate recurring_errors and cascading_errors


class ErrorAnalytics:
    """
    Advanced error analytics for pattern analysis and insights.
    
    Features:
    - Historical trend analysis
    - Component correlation analysis
    - Error prediction
    - Performance impact analysis
    - Recovery effectiveness analysis
    """
    
    def __init__(self, monitor: ErrorMonitor):
        self.monitor = monitor
    
    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze error trends over time."""
        events = self.monitor.get_recent_events(days * 24 * 60)  # Convert days to minutes
        
        if not events:
            return {"error": "No events found for analysis"}
        
        # Group by day
        daily_errors = defaultdict(list)
        for event in events:
            day_key = event.timestamp.strftime("%Y-%m-%d")
            daily_errors[day_key].append(event)
        
        # Calculate trends
        trend_data = []
        for day, day_events in sorted(daily_errors.items()):
            trend_data.append({
                "date": day,
                "total_errors": len(day_events),
                "by_category": self._count_by_category(day_events),
                "by_severity": self._count_by_severity(day_events),
                "by_component": self._count_by_component(day_events)
            })
        
        # Calculate trend direction
        if len(trend_data) >= 2:
            recent_avg = sum(d["total_errors"] for d in trend_data[-3:]) / min(3, len(trend_data))
            earlier_avg = sum(d["total_errors"] for d in trend_data[:-3]) / max(1, len(trend_data) - 3)
            trend_direction = "increasing" if recent_avg > earlier_avg else "decreasing"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "trend_direction": trend_direction,
            "daily_data": trend_data,
            "analysis_period_days": days,
            "total_events_analyzed": len(events)
        }
    
    def analyze_components(self, days: int = 7) -> Dict[str, Any]:
        """Analyze error patterns by component."""
        events = self.monitor.get_recent_events(days * 24 * 60)
        
        if not events:
            return {"error": "No events found for analysis"}
        
        component_analysis = {}
        
        # Group by component
        component_events = defaultdict(list)
        for event in events:
            component = event.component or "unknown"
            component_events[component].append(event)
        
        # Analyze each component
        for component, comp_events in component_events.items():
            analysis = {
                "total_errors": len(comp_events),
                "error_rate": len(comp_events) / days,  # errors per day
                "severity_distribution": self._count_by_severity(comp_events),
                "category_distribution": self._count_by_category(comp_events),
                "most_common_errors": self._get_most_common_errors(comp_events),
                "first_error": min(e.timestamp for e in comp_events),
                "last_error": max(e.timestamp for e in comp_events),
                "reliability_score": self._calculate_reliability_score(comp_events, days)
            }
            component_analysis[component] = analysis
        
        # Rank components by error rate
        ranked_components = sorted(
            component_analysis.items(),
            key=lambda x: x[1]["error_rate"],
            reverse=True
        )
        
        return {
            "component_analysis": dict(ranked_components),
            "most_problematic": ranked_components[0][0] if ranked_components else None,
            "total_components": len(component_analysis),
            "analysis_period_days": days
        }
    
    def predict_errors(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """Predict future errors based on historical patterns."""
        events = self.monitor.get_recent_events(7 * 24 * 60)  # Last week
        
        if not events:
            return {"error": "Insufficient data for prediction"}
        
        # Simple linear prediction based on recent trend
        hourly_errors = defaultdict(int)
        for event in events:
            hour = event.timestamp.hour
            hourly_errors[hour] += 1
        
        # Calculate hourly averages
        avg_hourly_errors = sum(hourly_errors.values()) / 24
        
        # Predict for next N hours
        current_hour = datetime.utcnow().hour
        predictions = []
        
        for i in range(hours_ahead):
            future_hour = (current_hour + i) % 24
            predicted_errors = hourly_errors.get(future_hour, avg_hourly_errors)
            predictions.append({
                "hour_offset": i,
                "hour": future_hour,
                "predicted_errors": int(predicted_errors),
                "confidence": 0.7  # Basic confidence score
            })
        
        total_predicted = sum(p["predicted_errors"] for p in predictions)
        
        return {
            "predictions": predictions,
            "total_predicted_errors": total_predicted,
            "prediction_period_hours": hours_ahead,
            "confidence": 0.7,
            "method": "historical_hourly_averages"
        }
    
    def _count_by_category(self, events: List[ErrorEvent]) -> Dict[str, int]:
        """Count events by category."""
        counts = defaultdict(int)
        for event in events:
            counts[event.classification.category.value] += 1
        return dict(counts)
    
    def _count_by_severity(self, events: List[ErrorEvent]) -> Dict[str, int]:
        """Count events by severity."""
        counts = defaultdict(int)
        for event in events:
            counts[event.classification.severity.value] += 1
        return dict(counts)
    
    def _count_by_component(self, events: List[ErrorEvent]) -> Dict[str, int]:
        """Count events by component."""
        counts = defaultdict(int)
        for event in events:
            component = event.component or "unknown"
            counts[component] += 1
        return dict(counts)
    
    def _get_most_common_errors(self, events: List[ErrorEvent], limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common error types."""
        error_counts = defaultdict(int)
        for event in events:
            error_key = (event.error_type, event.error_message[:100])
            error_counts[error_key] += 1
        
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                "error_type": error_type,
                "error_message": error_message[:100],
                "count": count
            }
            for (error_type, error_message), count in sorted_errors[:limit]
        ]
    
    def _calculate_reliability_score(self, events: List[ErrorEvent], days: int) -> float:
        """Calculate reliability score for component (0-100)."""
        if not events:
            return 100.0
        
        # Simple reliability based on error rate and severity
        total_minutes = days * 24 * 60
        error_rate = len(events) / total_minutes
        
        # Penalize for critical errors
        critical_penalty = sum(1 for e in events 
                             if e.classification.severity == ErrorSeverity.CRITICAL) * 10
        
        # Calculate score (inverse of error rate with penalties)
        base_score = max(0, 100 - (error_rate * 100))
        final_score = max(0, base_score - critical_penalty)
        
        return round(final_score, 2)


# Global error monitor instance
error_monitor = ErrorMonitor()
error_analytics = ErrorAnalytics(error_monitor)