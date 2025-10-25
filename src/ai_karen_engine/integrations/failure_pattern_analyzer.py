"""
Failure Pattern Analyzer for LLM Provider Management

This module implements failure pattern detection and analysis to identify
recurring provider issues, track failure history, and provide intelligent
recommendations for provider management and recovery optimization.

Key Features:
- Failure pattern detection for recurring provider issues
- Provider failure history tracking with timestamps and reasons
- Automatic provider disabling for consistently failing providers
- Recovery success rate tracking and optimization
- Intelligent failure analysis and recommendations
"""

import logging
import statistics
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ai_karen_engine.integrations.registry import get_registry


class FailurePattern(Enum):
    """Types of failure patterns that can be detected."""
    CONSISTENT_FAILURES = "consistent_failures"
    INTERMITTENT_FAILURES = "intermittent_failures"
    TIME_BASED_FAILURES = "time_based_failures"
    CASCADING_FAILURES = "cascading_failures"
    AUTHENTICATION_FAILURES = "authentication_failures"
    RATE_LIMIT_FAILURES = "rate_limit_failures"
    NETWORK_FAILURES = "network_failures"
    MODEL_UNAVAILABLE = "model_unavailable"
    CAPABILITY_FAILURES = "capability_failures"


class FailureSeverity(Enum):
    """Severity levels for failure patterns."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FailureRecord:
    """Record of a single provider failure."""
    timestamp: datetime
    provider: str
    model: Optional[str]
    runtime: Optional[str]
    error_type: str
    error_message: str
    request_type: str
    recovery_time: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailurePatternDetection:
    """Result of failure pattern detection."""
    pattern_type: FailurePattern
    severity: FailureSeverity
    affected_providers: List[str]
    failure_count: int
    time_span: timedelta
    confidence: float
    description: str
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderHealthMetrics:
    """Health metrics for a provider."""
    provider: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time: float
    last_failure: Optional[datetime]
    consecutive_failures: int
    failure_streak_duration: Optional[timedelta]
    recovery_success_rate: float
    is_disabled: bool
    disable_reason: Optional[str] = None
    disable_timestamp: Optional[datetime] = None


@dataclass
class FailureAnalysis:
    """Comprehensive failure analysis result."""
    analysis_timestamp: datetime
    time_window: timedelta
    total_failures: int
    unique_providers_affected: int
    detected_patterns: List[FailurePatternDetection]
    provider_metrics: Dict[str, ProviderHealthMetrics]
    most_failed_providers: List[Tuple[str, int]]
    common_failure_reasons: List[Tuple[str, int]]
    failure_time_patterns: Dict[str, List[datetime]]
    recovery_success_rate: Dict[str, float]
    recommendations: List[str]
    disabled_providers: List[str]


class FailurePatternAnalyzer:
    """
    Analyzer for detecting and analyzing LLM provider failure patterns.
    
    This analyzer tracks provider failures, detects patterns, and provides
    intelligent recommendations for provider management and recovery optimization.
    """
    
    def __init__(self, registry=None):
        self.registry = registry or get_registry()
        self.logger = logging.getLogger("kari.failure_analyzer")
        
        # Failure tracking
        self.failure_history: List[FailureRecord] = []
        self.provider_metrics: Dict[str, ProviderHealthMetrics] = {}
        self.disabled_providers: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.max_history_days = 7
        self.failure_threshold_count = 5
        self.failure_threshold_rate = 0.8  # 80% failure rate
        self.consecutive_failure_threshold = 3
        self.pattern_detection_window_hours = 24
        self.auto_disable_enabled = True
        
        self.logger.info("Failure pattern analyzer initialized")
    
    def record_failure(self, provider: str, error_type: str, error_message: str,
                      request_type: str, model: Optional[str] = None,
                      runtime: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a provider failure for analysis.
        
        Args:
            provider: Name of the failed provider
            error_type: Type/category of the error
            error_message: Detailed error message
            request_type: Type of request that failed
            model: Model that was being used (if applicable)
            runtime: Runtime that was being used (if applicable)
            context: Additional context information
        """
        failure_record = FailureRecord(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            runtime=runtime,
            error_type=error_type,
            error_message=error_message,
            request_type=request_type,
            context=context or {}
        )
        
        self.failure_history.append(failure_record)
        self._update_provider_metrics(provider, success=False)
        
        self.logger.debug(f"Recorded failure for {provider}: {error_type}")
        
        # Check if provider should be auto-disabled
        if self.auto_disable_enabled:
            self._check_auto_disable_provider(provider)
        
        # Clean up old history
        self._cleanup_old_history()
    
    def record_success(self, provider: str, response_time: float,
                      request_type: str, model: Optional[str] = None,
                      runtime: Optional[str] = None) -> None:
        """
        Record a successful provider request.
        
        Args:
            provider: Name of the successful provider
            response_time: Response time in seconds
            request_type: Type of request that succeeded
            model: Model that was used (if applicable)
            runtime: Runtime that was used (if applicable)
        """
        self._update_provider_metrics(provider, success=True, response_time=response_time)
        
        # Check if provider should be re-enabled
        if provider in self.disabled_providers:
            self._check_re_enable_provider(provider)
    
    def analyze_failure_patterns(self, time_window_hours: int = 24) -> FailureAnalysis:
        """
        Analyze failure patterns within the specified time window.
        
        Args:
            time_window_hours: Time window for analysis in hours
            
        Returns:
            Comprehensive failure analysis
        """
        analysis_start = datetime.now()
        time_window = timedelta(hours=time_window_hours)
        cutoff_time = analysis_start - time_window
        
        # Filter failures within time window
        recent_failures = [
            failure for failure in self.failure_history
            if failure.timestamp > cutoff_time
        ]
        
        self.logger.info(f"Analyzing {len(recent_failures)} failures in the last {time_window_hours} hours")
        
        # Detect patterns
        detected_patterns = self._detect_patterns(recent_failures, time_window)
        
        # Calculate provider metrics
        provider_metrics = self._calculate_provider_metrics(recent_failures)
        
        # Analyze failure statistics
        most_failed_providers = self._get_most_failed_providers(recent_failures)
        common_failure_reasons = self._get_common_failure_reasons(recent_failures)
        failure_time_patterns = self._analyze_time_patterns(recent_failures)
        recovery_success_rates = self._calculate_recovery_success_rates()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(detected_patterns, provider_metrics)
        
        # Get currently disabled providers
        disabled_providers = list(self.disabled_providers.keys())
        
        analysis = FailureAnalysis(
            analysis_timestamp=analysis_start,
            time_window=time_window,
            total_failures=len(recent_failures),
            unique_providers_affected=len(set(f.provider for f in recent_failures)),
            detected_patterns=detected_patterns,
            provider_metrics=provider_metrics,
            most_failed_providers=most_failed_providers,
            common_failure_reasons=common_failure_reasons,
            failure_time_patterns=failure_time_patterns,
            recovery_success_rate=recovery_success_rates,
            recommendations=recommendations,
            disabled_providers=disabled_providers
        )
        
        self.logger.info(f"Failure analysis completed: {len(detected_patterns)} patterns detected")
        return analysis
    
    def get_provider_health_status(self, provider: str) -> Optional[ProviderHealthMetrics]:
        """Get current health metrics for a provider."""
        return self.provider_metrics.get(provider)
    
    def is_provider_disabled(self, provider: str) -> bool:
        """Check if a provider is currently disabled."""
        return provider in self.disabled_providers
    
    def disable_provider(self, provider: str, reason: str, manual: bool = False) -> bool:
        """
        Manually disable a provider.
        
        Args:
            provider: Provider to disable
            reason: Reason for disabling
            manual: Whether this is a manual disable (vs automatic)
            
        Returns:
            True if provider was disabled, False if already disabled
        """
        if provider in self.disabled_providers:
            return False
        
        self.disabled_providers[provider] = {
            "reason": reason,
            "timestamp": datetime.now(),
            "manual": manual,
            "failure_count": self.provider_metrics.get(provider, {}).get("failed_requests", 0)
        }
        
        # Update provider metrics
        if provider in self.provider_metrics:
            self.provider_metrics[provider].is_disabled = True
            self.provider_metrics[provider].disable_reason = reason
            self.provider_metrics[provider].disable_timestamp = datetime.now()
        
        self.logger.warning(f"Provider {provider} disabled: {reason}")
        return True
    
    def enable_provider(self, provider: str) -> bool:
        """
        Manually enable a previously disabled provider.
        
        Args:
            provider: Provider to enable
            
        Returns:
            True if provider was enabled, False if not disabled
        """
        if provider not in self.disabled_providers:
            return False
        
        disable_info = self.disabled_providers.pop(provider)
        
        # Update provider metrics
        if provider in self.provider_metrics:
            self.provider_metrics[provider].is_disabled = False
            self.provider_metrics[provider].disable_reason = None
            self.provider_metrics[provider].disable_timestamp = None
            # Reset consecutive failures on manual enable
            self.provider_metrics[provider].consecutive_failures = 0
        
        self.logger.info(f"Provider {provider} re-enabled (was disabled: {disable_info['reason']})")
        return True
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get comprehensive failure statistics."""
        total_failures = len(self.failure_history)
        if total_failures == 0:
            return {"total_failures": 0, "message": "No failure data available"}
        
        # Recent failures (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_failures = [f for f in self.failure_history if f.timestamp > recent_cutoff]
        
        # Provider statistics
        provider_failure_counts = Counter(f.provider for f in self.failure_history)
        provider_recent_counts = Counter(f.provider for f in recent_failures)
        
        # Error type statistics
        error_type_counts = Counter(f.error_type for f in self.failure_history)
        
        # Time-based statistics
        hourly_failures = defaultdict(int)
        for failure in recent_failures:
            hour = failure.timestamp.hour
            hourly_failures[hour] += 1
        
        return {
            "total_failures": total_failures,
            "recent_failures_24h": len(recent_failures),
            "unique_providers_affected": len(provider_failure_counts),
            "most_failed_providers": provider_failure_counts.most_common(5),
            "recent_most_failed_providers": provider_recent_counts.most_common(5),
            "common_error_types": error_type_counts.most_common(5),
            "hourly_failure_distribution": dict(hourly_failures),
            "disabled_providers": len(self.disabled_providers),
            "disabled_provider_list": list(self.disabled_providers.keys()),
            "average_failures_per_provider": total_failures / len(provider_failure_counts) if provider_failure_counts else 0
        }
    
    def clear_failure_history(self, older_than_hours: int = 168) -> int:  # Default 7 days
        """Clear old failure history entries."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        original_count = len(self.failure_history)
        
        self.failure_history = [
            failure for failure in self.failure_history
            if failure.timestamp > cutoff_time
        ]
        
        cleared_count = original_count - len(self.failure_history)
        self.logger.info(f"Cleared {cleared_count} failure records older than {older_than_hours} hours")
        return cleared_count
    
    # Private helper methods
    
    def _update_provider_metrics(self, provider: str, success: bool, response_time: Optional[float] = None) -> None:
        """Update metrics for a provider."""
        if provider not in self.provider_metrics:
            self.provider_metrics[provider] = ProviderHealthMetrics(
                provider=provider,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                success_rate=0.0,
                average_response_time=0.0,
                last_failure=None,
                consecutive_failures=0,
                failure_streak_duration=None,
                recovery_success_rate=0.0,
                is_disabled=provider in self.disabled_providers
            )
        
        metrics = self.provider_metrics[provider]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
            metrics.consecutive_failures = 0
            if response_time is not None:
                # Update average response time
                total_response_time = metrics.average_response_time * (metrics.successful_requests - 1)
                metrics.average_response_time = (total_response_time + response_time) / metrics.successful_requests
        else:
            metrics.failed_requests += 1
            metrics.last_failure = datetime.now()
            metrics.consecutive_failures += 1
        
        # Update success rate
        metrics.success_rate = metrics.successful_requests / metrics.total_requests
    
    def _check_auto_disable_provider(self, provider: str) -> None:
        """Check if provider should be automatically disabled."""
        if provider in self.disabled_providers:
            return
        
        metrics = self.provider_metrics.get(provider)
        if not metrics:
            return
        
        # Check consecutive failures
        if metrics.consecutive_failures >= self.consecutive_failure_threshold:
            self.disable_provider(
                provider,
                f"Consecutive failures: {metrics.consecutive_failures}",
                manual=False
            )
            return
        
        # Check failure rate (only if we have enough data)
        if metrics.total_requests >= self.failure_threshold_count:
            if metrics.success_rate < (1 - self.failure_threshold_rate):
                self.disable_provider(
                    provider,
                    f"High failure rate: {(1-metrics.success_rate)*100:.1f}%",
                    manual=False
                )
    
    def _check_re_enable_provider(self, provider: str) -> None:
        """Check if a disabled provider should be re-enabled."""
        if provider not in self.disabled_providers:
            return
        
        disable_info = self.disabled_providers[provider]
        
        # Don't auto-enable manually disabled providers
        if disable_info.get("manual", False):
            return
        
        # Check if enough time has passed (at least 5 minutes)
        time_since_disable = datetime.now() - disable_info["timestamp"]
        if time_since_disable.total_seconds() < 300:  # 5 minutes
            return
        
        # Re-enable the provider
        self.enable_provider(provider)
    
    def _detect_patterns(self, failures: List[FailureRecord], time_window: timedelta) -> List[FailurePatternDetection]:
        """Detect failure patterns in the given failures."""
        patterns = []
        
        # Group failures by provider
        provider_failures = defaultdict(list)
        for failure in failures:
            provider_failures[failure.provider].append(failure)
        
        # Detect consistent failures
        for provider, provider_failure_list in provider_failures.items():
            if len(provider_failure_list) >= self.failure_threshold_count:
                # Check if failures are consistent (high frequency)
                time_span = provider_failure_list[-1].timestamp - provider_failure_list[0].timestamp
                if time_span.total_seconds() > 0:
                    failure_rate = len(provider_failure_list) / (time_span.total_seconds() / 3600)  # failures per hour
                    
                    if failure_rate > 2:  # More than 2 failures per hour
                        patterns.append(FailurePatternDetection(
                            pattern_type=FailurePattern.CONSISTENT_FAILURES,
                            severity=FailureSeverity.HIGH if failure_rate > 5 else FailureSeverity.MEDIUM,
                            affected_providers=[provider],
                            failure_count=len(provider_failure_list),
                            time_span=time_span,
                            confidence=min(0.9, failure_rate / 10),
                            description=f"Provider {provider} has {len(provider_failure_list)} failures in {time_span}",
                            recommendations=[
                                f"Investigate {provider} configuration and health",
                                f"Consider temporarily disabling {provider}",
                                "Check network connectivity and API keys"
                            ]
                        ))
        
        # Detect authentication failures
        auth_failures = [f for f in failures if "auth" in f.error_type.lower() or "unauthorized" in f.error_message.lower()]
        if len(auth_failures) >= 3:
            auth_providers = list(set(f.provider for f in auth_failures))
            patterns.append(FailurePatternDetection(
                pattern_type=FailurePattern.AUTHENTICATION_FAILURES,
                severity=FailureSeverity.HIGH,
                affected_providers=auth_providers,
                failure_count=len(auth_failures),
                time_span=time_window,
                confidence=0.9,
                description=f"Multiple authentication failures detected across {len(auth_providers)} providers",
                recommendations=[
                    "Check API keys and authentication credentials",
                    "Verify account status and quotas",
                    "Review authentication configuration"
                ]
            ))
        
        # Detect rate limit failures
        rate_limit_failures = [f for f in failures if "rate" in f.error_type.lower() or "limit" in f.error_message.lower()]
        if len(rate_limit_failures) >= 2:
            rate_limit_providers = list(set(f.provider for f in rate_limit_failures))
            patterns.append(FailurePatternDetection(
                pattern_type=FailurePattern.RATE_LIMIT_FAILURES,
                severity=FailureSeverity.MEDIUM,
                affected_providers=rate_limit_providers,
                failure_count=len(rate_limit_failures),
                time_span=time_window,
                confidence=0.8,
                description=f"Rate limiting detected for {len(rate_limit_providers)} providers",
                recommendations=[
                    "Review API usage and quotas",
                    "Implement request throttling",
                    "Consider upgrading API plans"
                ]
            ))
        
        # Detect network failures
        network_failures = [f for f in failures if any(term in f.error_message.lower() 
                           for term in ["network", "connection", "timeout", "dns"])]
        if len(network_failures) >= 3:
            network_providers = list(set(f.provider for f in network_failures))
            patterns.append(FailurePatternDetection(
                pattern_type=FailurePattern.NETWORK_FAILURES,
                severity=FailureSeverity.MEDIUM,
                affected_providers=network_providers,
                failure_count=len(network_failures),
                time_span=time_window,
                confidence=0.7,
                description=f"Network connectivity issues affecting {len(network_providers)} providers",
                recommendations=[
                    "Check network connectivity",
                    "Verify DNS resolution",
                    "Review firewall and proxy settings"
                ]
            ))
        
        return patterns
    
    def _calculate_provider_metrics(self, failures: List[FailureRecord]) -> Dict[str, ProviderHealthMetrics]:
        """Calculate provider metrics from recent failures."""
        # Return current metrics (already maintained)
        return self.provider_metrics.copy()
    
    def _get_most_failed_providers(self, failures: List[FailureRecord]) -> List[Tuple[str, int]]:
        """Get providers with most failures."""
        provider_counts = Counter(f.provider for f in failures)
        return provider_counts.most_common(10)
    
    def _get_common_failure_reasons(self, failures: List[FailureRecord]) -> List[Tuple[str, int]]:
        """Get most common failure reasons."""
        reason_counts = Counter(f.error_type for f in failures)
        return reason_counts.most_common(10)
    
    def _analyze_time_patterns(self, failures: List[FailureRecord]) -> Dict[str, List[datetime]]:
        """Analyze time-based failure patterns."""
        time_patterns = defaultdict(list)
        
        for failure in failures:
            # Group by hour of day
            hour = failure.timestamp.hour
            time_patterns[f"hour_{hour}"].append(failure.timestamp)
            
            # Group by day of week
            day = failure.timestamp.strftime("%A")
            time_patterns[f"day_{day}"].append(failure.timestamp)
        
        return dict(time_patterns)
    
    def _calculate_recovery_success_rates(self) -> Dict[str, float]:
        """Calculate recovery success rates for providers."""
        recovery_rates = {}
        
        for provider, metrics in self.provider_metrics.items():
            if metrics.total_requests > 0:
                recovery_rates[provider] = metrics.success_rate
        
        return recovery_rates
    
    def _generate_recommendations(self, patterns: List[FailurePatternDetection], 
                                 metrics: Dict[str, ProviderHealthMetrics]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Add pattern-specific recommendations
        for pattern in patterns:
            recommendations.extend(pattern.recommendations)
        
        # Add provider-specific recommendations
        for provider, provider_metrics in metrics.items():
            if provider_metrics.success_rate < 0.5 and provider_metrics.total_requests >= 5:
                recommendations.append(f"Provider {provider} has low success rate ({provider_metrics.success_rate:.1%}) - investigate configuration")
            
            if provider_metrics.consecutive_failures >= 3:
                recommendations.append(f"Provider {provider} has {provider_metrics.consecutive_failures} consecutive failures - consider disabling temporarily")
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _cleanup_old_history(self) -> None:
        """Clean up old failure history entries."""
        cutoff_time = datetime.now() - timedelta(days=self.max_history_days)
        original_count = len(self.failure_history)
        
        self.failure_history = [
            failure for failure in self.failure_history
            if failure.timestamp > cutoff_time
        ]
        
        if len(self.failure_history) < original_count:
            self.logger.debug(f"Cleaned up {original_count - len(self.failure_history)} old failure records")


# Convenience functions
def get_failure_analyzer(registry=None) -> FailurePatternAnalyzer:
    """Get a failure pattern analyzer instance."""
    return FailurePatternAnalyzer(registry=registry)


# Export classes and functions
__all__ = [
    "FailurePattern",
    "FailureSeverity",
    "FailureRecord",
    "FailurePatternDetection",
    "ProviderHealthMetrics",
    "FailureAnalysis",
    "FailurePatternAnalyzer",
    "get_failure_analyzer",
]