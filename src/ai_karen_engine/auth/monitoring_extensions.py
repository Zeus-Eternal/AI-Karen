"""
Enhanced monitoring extensions for the authentication service.

This module provides additional monitoring capabilities including:
- Advanced security event correlation
- Performance trend analysis
- Anomaly pattern detection
- Enhanced alerting with context
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .config import AuthConfig
from .models import AuthEvent, AuthEventType


@dataclass
class SecurityPattern:
    """Represents a detected security pattern or threat."""
    
    pattern_id: str
    pattern_type: str  # "brute_force", "credential_stuffing", "anomalous_behavior"
    severity: str  # "low", "medium", "high", "critical"
    confidence: float  # 0.0 to 1.0
    first_seen: datetime
    last_seen: datetime
    event_count: int
    affected_users: Set[str] = field(default_factory=set)
    source_ips: Set[str] = field(default_factory=set)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "event_count": self.event_count,
            "affected_users": list(self.affected_users),
            "source_ips": list(self.source_ips),
            "details": self.details,
        }


@dataclass
class PerformanceTrend:
    """Represents a performance trend analysis."""
    
    metric_name: str
    trend_direction: str  # "improving", "degrading", "stable"
    trend_strength: float  # 0.0 to 1.0
    current_value: float
    previous_value: float
    change_percentage: float
    analysis_period_minutes: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metric_name": self.metric_name,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_percentage": self.change_percentage,
            "analysis_period_minutes": self.analysis_period_minutes,
            "timestamp": self.timestamp.isoformat(),
        }


class SecurityEventCorrelator:
    """
    Correlates security events to detect patterns and threats.
    
    Analyzes authentication events to identify:
    - Brute force attacks
    - Credential stuffing attempts
    - Anomalous user behavior
    - Coordinated attacks
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SecurityEventCorrelator")
        
        # Event storage for correlation
        self._recent_events: deque = deque(maxlen=10000)
        self._failed_attempts_by_ip: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._failed_attempts_by_user: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Detected patterns
        self._active_patterns: Dict[str, SecurityPattern] = {}
        self._pattern_history: deque = deque(maxlen=1000)
        
        # Configuration thresholds
        self.brute_force_threshold = 10  # Failed attempts per IP in 5 minutes
        self.credential_stuffing_threshold = 5  # Failed attempts across multiple users from same IP
        self.anomaly_threshold = 0.7  # Risk score threshold for anomaly detection
        
    async def analyze_event(self, event: AuthEvent) -> List[SecurityPattern]:
        """
        Analyze an authentication event for security patterns.
        
        Returns:
            List of detected security patterns
        """
        self._recent_events.append(event)
        detected_patterns = []
        
        # Store failed attempts for correlation
        if not event.success and event.ip_address != "unknown":
            self._failed_attempts_by_ip[event.ip_address].append(event)
            if event.email:
                self._failed_attempts_by_user[event.email].append(event)
        
        # Check for brute force attacks
        brute_force_pattern = await self._detect_brute_force(event)
        if brute_force_pattern:
            detected_patterns.append(brute_force_pattern)
        
        # Check for credential stuffing
        credential_stuffing_pattern = await self._detect_credential_stuffing(event)
        if credential_stuffing_pattern:
            detected_patterns.append(credential_stuffing_pattern)
        
        # Check for anomalous behavior
        anomaly_pattern = await self._detect_anomalous_behavior(event)
        if anomaly_pattern:
            detected_patterns.append(anomaly_pattern)
        
        # Store detected patterns
        for pattern in detected_patterns:
            self._active_patterns[pattern.pattern_id] = pattern
            self._pattern_history.append(pattern)
        
        return detected_patterns
    
    async def _detect_brute_force(self, event: AuthEvent) -> Optional[SecurityPattern]:
        """Detect brute force attacks from a single IP."""
        if event.success or event.ip_address == "unknown":
            return None
        
        # Get recent failed attempts from this IP
        recent_failures = self._failed_attempts_by_ip[event.ip_address]
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        # Count recent failures
        recent_count = sum(
            1 for attempt in recent_failures
            if attempt.timestamp > cutoff_time
        )
        
        if recent_count >= self.brute_force_threshold:
            # Check if we already have an active pattern for this IP
            existing_pattern = None
            for pattern in self._active_patterns.values():
                if (pattern.pattern_type == "brute_force" and 
                    event.ip_address in pattern.source_ips):
                    existing_pattern = pattern
                    break
            
            if existing_pattern:
                # Update existing pattern
                existing_pattern.last_seen = event.timestamp
                existing_pattern.event_count += 1
                if event.email:
                    existing_pattern.affected_users.add(event.email)
                return None
            else:
                # Create new pattern
                return SecurityPattern(
                    pattern_id=str(uuid4()),
                    pattern_type="brute_force",
                    severity="high",
                    confidence=min(1.0, recent_count / self.brute_force_threshold),
                    first_seen=recent_failures[0].timestamp,
                    last_seen=event.timestamp,
                    event_count=recent_count,
                    affected_users={event.email} if event.email else set(),
                    source_ips={event.ip_address},
                    details={
                        "failed_attempts": recent_count,
                        "time_window_minutes": 5,
                        "threshold": self.brute_force_threshold,
                    }
                )
        
        return None
    
    async def _detect_credential_stuffing(self, event: AuthEvent) -> Optional[SecurityPattern]:
        """Detect credential stuffing attacks (same IP, multiple users)."""
        if event.success or event.ip_address == "unknown":
            return None
        
        # Get recent failed attempts from this IP
        recent_failures = self._failed_attempts_by_ip[event.ip_address]
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        
        # Count unique users targeted from this IP
        targeted_users = set()
        recent_attempts = []
        
        for attempt in recent_failures:
            if attempt.timestamp > cutoff_time and attempt.email:
                targeted_users.add(attempt.email)
                recent_attempts.append(attempt)
        
        if len(targeted_users) >= self.credential_stuffing_threshold:
            # Check for existing pattern
            existing_pattern = None
            for pattern in self._active_patterns.values():
                if (pattern.pattern_type == "credential_stuffing" and 
                    event.ip_address in pattern.source_ips):
                    existing_pattern = pattern
                    break
            
            if existing_pattern:
                # Update existing pattern
                existing_pattern.last_seen = event.timestamp
                existing_pattern.event_count += 1
                existing_pattern.affected_users.update(targeted_users)
                return None
            else:
                # Create new pattern
                return SecurityPattern(
                    pattern_id=str(uuid4()),
                    pattern_type="credential_stuffing",
                    severity="high",
                    confidence=min(1.0, len(targeted_users) / (self.credential_stuffing_threshold * 2)),
                    first_seen=recent_attempts[0].timestamp,
                    last_seen=event.timestamp,
                    event_count=len(recent_attempts),
                    affected_users=targeted_users,
                    source_ips={event.ip_address},
                    details={
                        "unique_users_targeted": len(targeted_users),
                        "time_window_minutes": 10,
                        "threshold": self.credential_stuffing_threshold,
                    }
                )
        
        return None
    
    async def _detect_anomalous_behavior(self, event: AuthEvent) -> Optional[SecurityPattern]:
        """Detect anomalous authentication behavior."""
        if event.risk_score < self.anomaly_threshold:
            return None
        
        # Check for existing anomaly pattern for this user/IP combination
        pattern_key = f"{event.user_id or 'unknown'}_{event.ip_address}"
        existing_pattern = None
        
        for pattern in self._active_patterns.values():
            if (pattern.pattern_type == "anomalous_behavior" and 
                pattern_key in pattern.details.get("pattern_keys", [])):
                existing_pattern = pattern
                break
        
        if existing_pattern:
            # Update existing pattern
            existing_pattern.last_seen = event.timestamp
            existing_pattern.event_count += 1
            existing_pattern.confidence = max(existing_pattern.confidence, event.risk_score)
            if event.user_id:
                existing_pattern.affected_users.add(event.user_id)
            existing_pattern.source_ips.add(event.ip_address)
            return None
        else:
            # Create new anomaly pattern
            severity = "critical" if event.risk_score > 0.9 else "high"
            
            return SecurityPattern(
                pattern_id=str(uuid4()),
                pattern_type="anomalous_behavior",
                severity=severity,
                confidence=event.risk_score,
                first_seen=event.timestamp,
                last_seen=event.timestamp,
                event_count=1,
                affected_users={event.user_id} if event.user_id else set(),
                source_ips={event.ip_address},
                details={
                    "risk_score": event.risk_score,
                    "security_flags": event.security_flags,
                    "pattern_keys": [pattern_key],
                    "event_type": event.event_type.value,
                }
            )
    
    def get_active_patterns(self) -> List[SecurityPattern]:
        """Get all currently active security patterns."""
        # Clean up old patterns (older than 1 hour)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_patterns = [
            pattern_id for pattern_id, pattern in self._active_patterns.items()
            if pattern.last_seen < cutoff_time
        ]
        
        for pattern_id in expired_patterns:
            del self._active_patterns[pattern_id]
        
        return list(self._active_patterns.values())
    
    def get_pattern_history(self, limit: int = 100) -> List[SecurityPattern]:
        """Get recent security pattern history."""
        return list(self._pattern_history)[-limit:]
    
    def get_correlation_stats(self) -> Dict[str, Any]:
        """Get correlation statistics."""
        active_patterns = self.get_active_patterns()
        
        pattern_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for pattern in active_patterns:
            pattern_counts[pattern.pattern_type] += 1
            severity_counts[pattern.severity] += 1
        
        return {
            "active_patterns": len(active_patterns),
            "pattern_types": dict(pattern_counts),
            "severity_distribution": dict(severity_counts),
            "recent_events_analyzed": len(self._recent_events),
            "ips_with_failed_attempts": len(self._failed_attempts_by_ip),
            "users_with_failed_attempts": len(self._failed_attempts_by_user),
        }


class PerformanceTrendAnalyzer:
    """
    Analyzes performance trends in authentication metrics.
    
    Provides insights into:
    - Authentication response time trends
    - Success rate trends
    - Error rate patterns
    - System health indicators
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PerformanceTrendAnalyzer")
        
        # Historical data storage
        self._metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._trend_cache: Dict[str, PerformanceTrend] = {}
        
        # Analysis configuration
        self.trend_analysis_periods = [5, 15, 30, 60]  # minutes
        self.significant_change_threshold = 0.1  # 10% change
        
    async def record_metric_point(self, metric_name: str, value: float, timestamp: Optional[datetime] = None) -> None:
        """Record a metric data point for trend analysis."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        self._metric_history[metric_name].append((timestamp, value))
    
    async def analyze_trends(self) -> List[PerformanceTrend]:
        """Analyze performance trends for all tracked metrics."""
        trends = []
        
        for metric_name, history in self._metric_history.items():
            if len(history) < 10:  # Need minimum data points
                continue
            
            for period_minutes in self.trend_analysis_periods:
                trend = await self._analyze_metric_trend(metric_name, period_minutes)
                if trend:
                    trends.append(trend)
                    self._trend_cache[f"{metric_name}_{period_minutes}m"] = trend
        
        return trends
    
    async def _analyze_metric_trend(self, metric_name: str, period_minutes: int) -> Optional[PerformanceTrend]:
        """Analyze trend for a specific metric over a time period."""
        history = self._metric_history[metric_name]
        if len(history) < 2:
            return None
        
        # Get data points within the analysis period
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=period_minutes)
        recent_points = [(ts, val) for ts, val in history if ts > cutoff_time]
        
        if len(recent_points) < 2:
            return None
        
        # Calculate trend
        current_value = recent_points[-1][1]
        
        # Get comparison value (from half the period ago)
        comparison_cutoff = datetime.now(timezone.utc) - timedelta(minutes=period_minutes // 2)
        comparison_points = [(ts, val) for ts, val in recent_points if ts <= comparison_cutoff]
        
        if not comparison_points:
            return None
        
        previous_value = comparison_points[-1][1]
        
        # Calculate change
        if previous_value == 0:
            change_percentage = 0.0
        else:
            change_percentage = ((current_value - previous_value) / previous_value) * 100
        
        # Determine trend direction and strength
        abs_change = abs(change_percentage)
        
        if abs_change < self.significant_change_threshold * 100:
            trend_direction = "stable"
            trend_strength = 0.0
        elif change_percentage > 0:
            trend_direction = "improving" if "success" in metric_name.lower() else "degrading"
            trend_strength = min(1.0, abs_change / 50.0)  # Normalize to 0-1
        else:
            trend_direction = "degrading" if "success" in metric_name.lower() else "improving"
            trend_strength = min(1.0, abs_change / 50.0)
        
        return PerformanceTrend(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            current_value=current_value,
            previous_value=previous_value,
            change_percentage=change_percentage,
            analysis_period_minutes=period_minutes,
        )
    
    def get_current_trends(self, metric_name: Optional[str] = None) -> List[PerformanceTrend]:
        """Get current performance trends."""
        if metric_name:
            return [trend for key, trend in self._trend_cache.items() if metric_name in key]
        return list(self._trend_cache.values())
    
    def get_trend_summary(self) -> Dict[str, Any]:
        """Get a summary of performance trends."""
        trends = list(self._trend_cache.values())
        
        if not trends:
            return {"status": "no_data", "trends_analyzed": 0}
        
        # Categorize trends
        improving_count = sum(1 for t in trends if t.trend_direction == "improving")
        degrading_count = sum(1 for t in trends if t.trend_direction == "degrading")
        stable_count = sum(1 for t in trends if t.trend_direction == "stable")
        
        # Identify concerning trends
        concerning_trends = [
            t for t in trends 
            if t.trend_direction == "degrading" and t.trend_strength > 0.5
        ]
        
        # Overall health assessment
        if concerning_trends:
            overall_status = "concerning"
        elif degrading_count > improving_count:
            overall_status = "declining"
        elif improving_count > degrading_count:
            overall_status = "improving"
        else:
            overall_status = "stable"
        
        return {
            "status": overall_status,
            "trends_analyzed": len(trends),
            "improving": improving_count,
            "degrading": degrading_count,
            "stable": stable_count,
            "concerning_trends": len(concerning_trends),
            "metrics_tracked": len(self._metric_history),
        }


class EnhancedAuthMonitor:
    """
    Enhanced authentication monitoring with advanced analytics.
    
    Extends the base AuthMonitor with:
    - Security event correlation
    - Performance trend analysis
    - Advanced alerting with context
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.EnhancedAuthMonitor")
        
        # Initialize components
        self.security_correlator = SecurityEventCorrelator(config)
        self.performance_analyzer = PerformanceTrendAnalyzer(config)
        
        # Background tasks
        self._analysis_task: Optional[asyncio.Task] = None
        self._start_background_analysis()
        
    def _start_background_analysis(self) -> None:
        """Start background analysis tasks."""
        async def analysis_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    await self._run_periodic_analysis()
                except Exception as e:
                    self.logger.error(f"Error in background analysis: {e}")
        
        self._analysis_task = asyncio.create_task(analysis_loop())
    
    async def _run_periodic_analysis(self) -> None:
        """Run periodic analysis tasks."""
        try:
            # Analyze performance trends
            trends = await self.performance_analyzer.analyze_trends()
            
            # Log significant trends
            for trend in trends:
                if trend.trend_strength > 0.5:
                    self.logger.info(
                        f"Performance trend detected: {trend.metric_name} is {trend.trend_direction} "
                        f"({trend.change_percentage:.1f}% change over {trend.analysis_period_minutes}m)",
                        extra={
                            "trend_data": trend.to_dict(),
                            "metric_name": trend.metric_name,
                            "trend_direction": trend.trend_direction,
                            "change_percentage": trend.change_percentage,
                        }
                    )
            
            # Get security correlation stats
            correlation_stats = self.security_correlator.get_correlation_stats()
            if correlation_stats["active_patterns"] > 0:
                self.logger.warning(
                    f"Active security patterns detected: {correlation_stats['active_patterns']}",
                    extra={"correlation_stats": correlation_stats}
                )
                
        except Exception as e:
            self.logger.error(f"Error in periodic analysis: {e}")
    
    async def analyze_auth_event(self, event: AuthEvent) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of an authentication event.
        
        Returns:
            Analysis results including security patterns and performance metrics
        """
        analysis_results = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "security_patterns": [],
            "performance_impact": None,
            "recommendations": [],
        }
        
        try:
            # Security correlation analysis
            security_patterns = await self.security_correlator.analyze_event(event)
            analysis_results["security_patterns"] = [p.to_dict() for p in security_patterns]
            
            # Record performance metrics
            if event.processing_time_ms > 0:
                await self.performance_analyzer.record_metric_point(
                    f"auth.processing_time.{event.event_type.value}",
                    event.processing_time_ms,
                    event.timestamp
                )
            
            # Record success/failure rates
            success_metric = f"auth.success_rate.{event.tenant_id or 'default'}"
            await self.performance_analyzer.record_metric_point(
                success_metric,
                1.0 if event.success else 0.0,
                event.timestamp
            )
            
            # Generate recommendations based on analysis
            recommendations = self._generate_recommendations(event, security_patterns)
            analysis_results["recommendations"] = recommendations
            
        except Exception as e:
            self.logger.error(f"Error analyzing auth event {event.event_id}: {e}")
            analysis_results["error"] = str(e)
        
        return analysis_results
    
    def _generate_recommendations(self, event: AuthEvent, security_patterns: List[SecurityPattern]) -> List[str]:
        """Generate actionable recommendations based on event analysis."""
        recommendations = []
        
        # Security-based recommendations
        if security_patterns:
            for pattern in security_patterns:
                if pattern.pattern_type == "brute_force":
                    recommendations.append(
                        f"Consider implementing IP-based rate limiting for {', '.join(pattern.source_ips)}"
                    )
                elif pattern.pattern_type == "credential_stuffing":
                    recommendations.append(
                        "Enable CAPTCHA or additional verification for suspicious login patterns"
                    )
                elif pattern.pattern_type == "anomalous_behavior":
                    recommendations.append(
                        "Review user behavior patterns and consider additional authentication factors"
                    )
        
        # Performance-based recommendations
        if event.processing_time_ms > 2000:  # Slow authentication
            recommendations.append(
                "Authentication response time is slow - consider optimizing database queries or caching"
            )
        
        # Risk-based recommendations
        if event.risk_score > 0.8:
            recommendations.append(
                "High risk score detected - consider requiring additional verification"
            )
        
        if event.security_flags:
            recommendations.append(
                f"Security flags present: {', '.join(event.security_flags)} - review security policies"
            )
        
        return recommendations
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        return {
            "security_correlation": self.security_correlator.get_correlation_stats(),
            "performance_trends": self.performance_analyzer.get_trend_summary(),
            "active_security_patterns": len(self.security_correlator.get_active_patterns()),
            "monitoring_health": "active",
            "last_analysis": datetime.now(timezone.utc).isoformat(),
        }
    
    async def shutdown(self) -> None:
        """Shutdown enhanced monitoring components."""
        if self._analysis_task:
            self._analysis_task.cancel()
        
        self.logger.info("EnhancedAuthMonitor shutdown completed")