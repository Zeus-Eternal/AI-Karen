"""
Intelligence layer for advanced authentication features.

This module provides the IntelligenceEngine class that integrates anomaly detection,
behavioral analysis, and risk scoring for the consolidated authentication service.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .config import AuthConfig
from .models import AuthEvent, AuthEventType, UserData

logger = logging.getLogger(__name__)


@dataclass
class LoginAttempt:
    """Data structure for login attempt analysis."""

    user_id: Optional[str]
    email: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    device_fingerprint: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    session_context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
            "device_fingerprint": self.device_fingerprint,
            "geolocation": self.geolocation,
            "session_context": self.session_context,
        }


@dataclass
class BehavioralPattern:
    """User behavioral pattern data."""

    user_id: str
    typical_login_hours: List[int] = field(default_factory=list)
    typical_locations: List[Dict[str, Any]] = field(default_factory=list)
    typical_devices: List[str] = field(default_factory=list)
    login_frequency: Dict[str, int] = field(
        default_factory=dict
    )  # day_of_week -> count
    average_session_duration: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "typical_login_hours": self.typical_login_hours,
            "typical_locations": self.typical_locations,
            "typical_devices": self.typical_devices,
            "login_frequency": self.login_frequency,
            "average_session_duration": self.average_session_duration,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class AnomalyResult:
    """Result of anomaly detection analysis."""

    is_anomaly: bool
    anomaly_score: float  # 0.0 to 1.0
    anomaly_types: List[str] = field(default_factory=list)
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score,
            "anomaly_types": self.anomaly_types,
            "confidence": self.confidence,
            "details": self.details,
        }


@dataclass
class IntelligenceResult:
    """Result of intelligence analysis for authentication attempt."""

    risk_score: float  # 0.0 to 1.0
    risk_level: str  # "low", "medium", "high"
    should_block: bool
    anomaly_result: Optional[AnomalyResult] = None
    behavioral_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "should_block": self.should_block,
            "anomaly_result": self.anomaly_result.to_dict()
            if self.anomaly_result
            else None,
            "behavioral_analysis": self.behavioral_analysis,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms,
        }


class AnomalyDetector:
    """Anomaly detection component for authentication attempts."""

    def __init__(self, config: AuthConfig) -> None:
        """Initialize anomaly detector with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AnomalyDetector")

    async def detect_anomalies(
        self, attempt: LoginAttempt, user_pattern: Optional[BehavioralPattern] = None
    ) -> AnomalyResult:
        """Detect anomalies in a login attempt."""
        start_time = datetime.utcnow()
        anomaly_types = []
        anomaly_score = 0.0
        details = {}

        try:
            # Time-based anomaly detection
            time_anomaly = self._detect_time_anomaly(attempt, user_pattern)
            if time_anomaly[0]:
                anomaly_types.append("unusual_time")
                anomaly_score = max(anomaly_score, time_anomaly[1])
                details["time_analysis"] = time_anomaly[2]

            # Location-based anomaly detection
            location_anomaly = self._detect_location_anomaly(attempt, user_pattern)
            if location_anomaly[0]:
                anomaly_types.append("unusual_location")
                anomaly_score = max(anomaly_score, location_anomaly[1])
                details["location_analysis"] = location_anomaly[2]

            # Device-based anomaly detection
            device_anomaly = self._detect_device_anomaly(attempt, user_pattern)
            if device_anomaly[0]:
                anomaly_types.append("unusual_device")
                anomaly_score = max(anomaly_score, device_anomaly[1])
                details["device_analysis"] = device_anomaly[2]

            # Frequency-based anomaly detection
            frequency_anomaly = self._detect_frequency_anomaly(attempt, user_pattern)
            if frequency_anomaly[0]:
                anomaly_types.append("unusual_frequency")
                anomaly_score = max(anomaly_score, frequency_anomaly[1])
                details["frequency_analysis"] = frequency_anomaly[2]

            is_anomaly = len(anomaly_types) > 0
            confidence = min(
                1.0, anomaly_score * len(anomaly_types) / 4.0
            )  # Normalize by max possible anomaly types

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            details["processing_time_ms"] = processing_time

            return AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_types=anomaly_types,
                confidence=confidence,
                details=details,
            )

        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            return AnomalyResult(
                is_anomaly=False, anomaly_score=0.0, details={"error": str(e)}
            )

    def _detect_time_anomaly(
        self, attempt: LoginAttempt, user_pattern: Optional[BehavioralPattern]
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """Detect time-based anomalies."""
        if not user_pattern or not user_pattern.typical_login_hours:
            return False, 0.0, {"reason": "no_historical_data"}

        current_hour = attempt.timestamp.hour
        typical_hours = set(user_pattern.typical_login_hours)

        if current_hour in typical_hours:
            return False, 0.0, {"current_hour": current_hour, "is_typical": True}

        # Calculate distance to nearest typical hour
        distances = [
            min(abs(current_hour - h), 24 - abs(current_hour - h))
            for h in typical_hours
        ]
        min_distance = min(distances)

        # Score based on distance (further = higher anomaly score)
        anomaly_score = min(1.0, min_distance / 12.0)  # Max distance is 12 hours

        return (
            anomaly_score > self.config.intelligence.time_sensitivity,
            anomaly_score,
            {
                "current_hour": current_hour,
                "typical_hours": list(typical_hours),
                "min_distance_hours": min_distance,
                "anomaly_score": anomaly_score,
            },
        )

    def _detect_location_anomaly(
        self, attempt: LoginAttempt, user_pattern: Optional[BehavioralPattern]
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """Detect location-based anomalies."""
        if (
            not attempt.geolocation
            or not user_pattern
            or not user_pattern.typical_locations
        ):
            return False, 0.0, {"reason": "no_location_data"}

        current_location = attempt.geolocation
        if not current_location.get("latitude") or not current_location.get(
            "longitude"
        ):
            return False, 0.0, {"reason": "incomplete_location_data"}

        # Calculate distance to typical locations
        min_distance = float("inf")
        for typical_loc in user_pattern.typical_locations:
            if typical_loc.get("latitude") and typical_loc.get("longitude"):
                distance = self._calculate_distance(
                    current_location["latitude"],
                    current_location["longitude"],
                    typical_loc["latitude"],
                    typical_loc["longitude"],
                )
                min_distance = min(min_distance, distance)

        if min_distance == float("inf"):
            return False, 0.0, {"reason": "no_valid_typical_locations"}

        # Score based on distance (further = higher anomaly score)
        # Assume 100km as threshold for "normal" distance
        anomaly_score = min(1.0, min_distance / 100.0)

        return (
            anomaly_score > self.config.intelligence.location_sensitivity,
            anomaly_score,
            {
                "current_location": current_location,
                "min_distance_km": min_distance,
                "anomaly_score": anomaly_score,
            },
        )

    def _detect_device_anomaly(
        self, attempt: LoginAttempt, user_pattern: Optional[BehavioralPattern]
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """Detect device-based anomalies."""
        if (
            not attempt.device_fingerprint
            or not user_pattern
            or not user_pattern.typical_devices
        ):
            return False, 0.0, {"reason": "no_device_data"}

        current_device = attempt.device_fingerprint
        is_known_device = current_device in user_pattern.typical_devices

        if is_known_device:
            return False, 0.0, {"device_fingerprint": current_device, "is_known": True}

        # New device - score based on device sensitivity setting
        anomaly_score = self.config.intelligence.device_sensitivity

        return (
            True,
            anomaly_score,
            {
                "device_fingerprint": current_device,
                "is_known": False,
                "known_devices_count": len(user_pattern.typical_devices),
                "anomaly_score": anomaly_score,
            },
        )

    def _detect_frequency_anomaly(
        self, attempt: LoginAttempt, user_pattern: Optional[BehavioralPattern]
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """Detect frequency-based anomalies."""
        if not user_pattern or not user_pattern.login_frequency:
            return False, 0.0, {"reason": "no_frequency_data"}

        day_of_week = attempt.timestamp.strftime("%A").lower()
        typical_frequency = user_pattern.login_frequency.get(day_of_week, 0)

        # For now, just check if user typically logs in on this day
        if typical_frequency > 0:
            return False, 0.0, {"day_of_week": day_of_week, "is_typical_day": True}

        # User doesn't typically log in on this day
        anomaly_score = 0.3  # Moderate anomaly score for unusual day

        return (
            True,
            anomaly_score,
            {
                "day_of_week": day_of_week,
                "typical_frequency": typical_frequency,
                "is_typical_day": False,
                "anomaly_score": anomaly_score,
            },
        )

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        import math

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in kilometers
        r = 6371

        return c * r


class BehavioralAnalyzer:
    """Behavioral analysis component for user pattern recognition."""

    def __init__(self, config: AuthConfig) -> None:
        """Initialize behavioral analyzer with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.BehavioralAnalyzer")

    async def analyze_behavior(
        self,
        attempt: LoginAttempt,
        user_data: Optional[UserData] = None,
        historical_events: Optional[List[AuthEvent]] = None,
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        try:
            if not user_data or not historical_events:
                return {"status": "insufficient_data", "analysis": {}}

            # Build behavioral pattern from historical data
            pattern = await self._build_behavioral_pattern(
                user_data.user_id, historical_events
            )

            # Analyze current attempt against pattern
            analysis = {
                "pattern_established": len(historical_events)
                >= self.config.intelligence.min_training_samples,
                "time_analysis": self._analyze_time_pattern(attempt, pattern),
                "location_analysis": self._analyze_location_pattern(attempt, pattern),
                "device_analysis": self._analyze_device_pattern(attempt, pattern),
                "frequency_analysis": self._analyze_frequency_pattern(attempt, pattern),
                "pattern_summary": {
                    "typical_hours": pattern.typical_login_hours,
                    "location_count": len(pattern.typical_locations),
                    "device_count": len(pattern.typical_devices),
                    "total_logins": len(historical_events),
                },
            }

            return {"status": "success", "analysis": analysis, "pattern": pattern}

        except Exception as e:
            self.logger.error(f"Error in behavioral analysis: {e}")
            return {"status": "error", "error": str(e)}

    async def _build_behavioral_pattern(
        self, user_id: str, historical_events: List[AuthEvent]
    ) -> BehavioralPattern:
        """Build behavioral pattern from historical authentication events."""
        pattern = BehavioralPattern(user_id=user_id)

        # Filter successful login events
        login_events = [
            event
            for event in historical_events
            if event.event_type == AuthEventType.LOGIN_SUCCESS
        ]

        if not login_events:
            return pattern

        # Analyze time patterns
        login_hours = [event.timestamp.hour for event in login_events]
        pattern.typical_login_hours = list(set(login_hours))

        # Analyze frequency patterns
        frequency = {}
        for event in login_events:
            day = event.timestamp.strftime("%A").lower()
            frequency[day] = frequency.get(day, 0) + 1
        pattern.login_frequency = frequency

        # Analyze location patterns (if available)
        locations = []
        for event in login_events:
            if event.details.get("geolocation"):
                locations.append(event.details["geolocation"])
        pattern.typical_locations = self._cluster_locations(locations)

        # Analyze device patterns (if available)
        devices = []
        for event in login_events:
            if event.details.get("device_fingerprint"):
                devices.append(event.details["device_fingerprint"])
        pattern.typical_devices = list(set(devices))

        pattern.last_updated = datetime.utcnow()
        return pattern

    def _analyze_time_pattern(
        self, attempt: LoginAttempt, pattern: BehavioralPattern
    ) -> Dict[str, Any]:
        """Analyze time-based behavior patterns."""
        current_hour = attempt.timestamp.hour
        is_typical_hour = current_hour in pattern.typical_login_hours

        return {
            "current_hour": current_hour,
            "is_typical_hour": is_typical_hour,
            "typical_hours": pattern.typical_login_hours,
            "hour_deviation": self._calculate_hour_deviation(
                current_hour, pattern.typical_login_hours
            ),
        }

    def _analyze_location_pattern(
        self, attempt: LoginAttempt, pattern: BehavioralPattern
    ) -> Dict[str, Any]:
        """Analyze location-based behavior patterns."""
        if not attempt.geolocation:
            return {"status": "no_location_data"}

        is_typical_location = False
        min_distance = float("inf")

        for typical_loc in pattern.typical_locations:
            if typical_loc.get("latitude") and typical_loc.get("longitude"):
                distance = self._calculate_distance(
                    attempt.geolocation["latitude"],
                    attempt.geolocation["longitude"],
                    typical_loc["latitude"],
                    typical_loc["longitude"],
                )
                min_distance = min(min_distance, distance)
                if distance < 50:  # Within 50km considered typical
                    is_typical_location = True
                    break

        return {
            "current_location": attempt.geolocation,
            "is_typical_location": is_typical_location,
            "min_distance_km": min_distance if min_distance != float("inf") else None,
            "typical_locations_count": len(pattern.typical_locations),
        }

    def _analyze_device_pattern(
        self, attempt: LoginAttempt, pattern: BehavioralPattern
    ) -> Dict[str, Any]:
        """Analyze device-based behavior patterns."""
        if not attempt.device_fingerprint:
            return {"status": "no_device_data"}

        is_known_device = attempt.device_fingerprint in pattern.typical_devices

        return {
            "device_fingerprint": attempt.device_fingerprint,
            "is_known_device": is_known_device,
            "known_devices_count": len(pattern.typical_devices),
        }

    def _analyze_frequency_pattern(
        self, attempt: LoginAttempt, pattern: BehavioralPattern
    ) -> Dict[str, Any]:
        """Analyze frequency-based behavior patterns."""
        day_of_week = attempt.timestamp.strftime("%A").lower()
        typical_frequency = pattern.login_frequency.get(day_of_week, 0)
        total_logins = sum(pattern.login_frequency.values())
        frequency_ratio = typical_frequency / total_logins if total_logins > 0 else 0

        return {
            "day_of_week": day_of_week,
            "typical_frequency": typical_frequency,
            "frequency_ratio": frequency_ratio,
            "is_typical_day": typical_frequency > 0,
        }

    def _cluster_locations(
        self, locations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simple location clustering to identify typical locations."""
        if not locations:
            return []

        # Simple clustering: group locations within 10km of each other
        clusters = []
        for location in locations:
            if not location.get("latitude") or not location.get("longitude"):
                continue

            added_to_cluster = False
            for cluster in clusters:
                distance = self._calculate_distance(
                    location["latitude"],
                    location["longitude"],
                    cluster["latitude"],
                    cluster["longitude"],
                )
                if distance < 10:  # 10km threshold
                    added_to_cluster = True
                    break

            if not added_to_cluster:
                clusters.append(location)

        return clusters

    def _calculate_hour_deviation(
        self, current_hour: int, typical_hours: List[int]
    ) -> float:
        """Calculate deviation from typical hours."""
        if not typical_hours:
            return 12.0  # Maximum deviation

        distances = [
            min(abs(current_hour - h), 24 - abs(current_hour - h))
            for h in typical_hours
        ]
        return min(distances)

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        import math

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in kilometers
        r = 6371

        return c * r


class RiskScorer:
    """Risk scoring component for authentication attempts."""

    def __init__(self, config: AuthConfig) -> None:
        """Initialize risk scorer with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RiskScorer")

    def calculate_risk_score(
        self,
        attempt: LoginAttempt,
        anomaly_result: Optional[AnomalyResult] = None,
        behavioral_analysis: Optional[Dict[str, Any]] = None,
        user_data: Optional[UserData] = None,
    ) -> Tuple[float, str]:
        """Calculate overall risk score and level."""
        try:
            base_score = 0.0

            # Anomaly-based risk
            if anomaly_result and anomaly_result.is_anomaly:
                anomaly_weight = 0.4
                base_score += anomaly_result.anomaly_score * anomaly_weight

            # Behavioral analysis risk
            if behavioral_analysis and behavioral_analysis.get("status") == "success":
                behavioral_weight = 0.3
                behavioral_risk = self._calculate_behavioral_risk(
                    behavioral_analysis["analysis"]
                )
                base_score += behavioral_risk * behavioral_weight

            # User history risk
            if user_data:
                history_weight = 0.2
                history_risk = self._calculate_history_risk(user_data)
                base_score += history_risk * history_weight

            # Context-based risk
            context_weight = 0.1
            context_risk = self._calculate_context_risk(attempt)
            base_score += context_risk * context_weight

            # Ensure score is between 0 and 1
            risk_score = max(0.0, min(1.0, base_score))

            # Determine risk level
            if risk_score < self.config.intelligence.risk_threshold_low:
                risk_level = "low"
            elif risk_score < self.config.intelligence.risk_threshold_medium:
                risk_level = "medium"
            elif risk_score < self.config.intelligence.risk_threshold_high:
                risk_level = "high"
            else:
                risk_level = "critical"

            return risk_score, risk_level

        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 0.5, "medium"  # Default to medium risk on error

    def _calculate_behavioral_risk(self, analysis: Dict[str, Any]) -> float:
        """Calculate risk based on behavioral analysis."""
        risk_factors = []

        # Time-based risk
        time_analysis = analysis.get("time_analysis", {})
        if not time_analysis.get("is_typical_hour", True):
            hour_deviation = time_analysis.get("hour_deviation", 0)
            risk_factors.append(min(1.0, hour_deviation / 12.0))

        # Location-based risk
        location_analysis = analysis.get("location_analysis", {})
        if location_analysis.get("status") != "no_location_data":
            if not location_analysis.get("is_typical_location", True):
                min_distance = location_analysis.get("min_distance_km", 0)
                if min_distance:
                    risk_factors.append(
                        min(1.0, min_distance / 1000.0)
                    )  # Normalize by 1000km

        # Device-based risk
        device_analysis = analysis.get("device_analysis", {})
        if device_analysis.get("status") != "no_device_data":
            if not device_analysis.get("is_known_device", True):
                risk_factors.append(0.5)  # Moderate risk for unknown device

        # Frequency-based risk
        frequency_analysis = analysis.get("frequency_analysis", {})
        if not frequency_analysis.get("is_typical_day", True):
            risk_factors.append(0.3)  # Low-moderate risk for unusual day

        # Return average of risk factors
        return sum(risk_factors) / len(risk_factors) if risk_factors else 0.0

    def _calculate_history_risk(self, user_data: UserData) -> float:
        """Calculate risk based on user history."""
        risk_score = 0.0

        # Failed login attempts
        if user_data.failed_login_attempts > 0:
            risk_score += min(0.5, user_data.failed_login_attempts / 10.0)

        # Account locked
        if user_data.is_locked():
            risk_score += 0.8

        # Account not verified
        if not user_data.is_verified:
            risk_score += 0.3

        # Account not active
        if not user_data.is_active:
            risk_score += 1.0

        return min(1.0, risk_score)

    def _calculate_context_risk(self, attempt: LoginAttempt) -> float:
        """Calculate risk based on attempt context."""
        risk_score = 0.0

        # Check for suspicious IP patterns
        if self._is_suspicious_ip(attempt.ip_address):
            risk_score += 0.4

        # Check for suspicious user agent
        if self._is_suspicious_user_agent(attempt.user_agent):
            risk_score += 0.2

        # Check for unusual timing (e.g., very late night)
        hour = attempt.timestamp.hour
        if hour < 4 or hour > 23:  # Between midnight and 4 AM
            risk_score += 0.1

        return min(1.0, risk_score)

    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious."""
        # Simple checks - in production, this would use threat intelligence
        suspicious_patterns = [
            "127.0.0.1",  # Localhost (suspicious in production)
            "0.0.0.0",  # Invalid IP
        ]

        return any(pattern in ip_address for pattern in suspicious_patterns)

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        if not user_agent:
            return True

        suspicious_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "curl",
            "wget",
        ]

        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)


class IntelligenceEngine:
    """
    Intelligence engine that integrates anomaly detection, behavioral analysis,
    and risk scoring for advanced authentication features.
    """

    def __init__(self, config: AuthConfig) -> None:
        """Initialize intelligence engine with configuration."""
        self.config = config
        self.anomaly_detector = AnomalyDetector(config)
        self.behavioral_analyzer = BehavioralAnalyzer(config)
        self.risk_scorer = RiskScorer(config)
        self.logger = logging.getLogger(f"{__name__}.IntelligenceEngine")
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the intelligence engine."""
        if self._initialized:
            return

        self.logger.info("Initializing intelligence engine")
        # Any async initialization can go here
        self._initialized = True
        self.logger.info("Intelligence engine initialized successfully")

    async def analyze_login_attempt(
        self,
        attempt: LoginAttempt,
        user_data: Optional[UserData] = None,
        historical_events: Optional[List[AuthEvent]] = None,
    ) -> IntelligenceResult:
        """Analyze a login attempt and return intelligence result."""
        start_time = datetime.utcnow()

        try:
            await self.initialize()

            # Perform behavioral analysis
            behavioral_analysis = await self.behavioral_analyzer.analyze_behavior(
                attempt, user_data, historical_events
            )

            # Extract behavioral pattern if available
            behavioral_pattern = None
            if behavioral_analysis.get("status") == "success":
                behavioral_pattern = behavioral_analysis.get("pattern")

            # Perform anomaly detection
            anomaly_result = await self.anomaly_detector.detect_anomalies(
                attempt, behavioral_pattern
            )

            # Calculate risk score
            risk_score, risk_level = self.risk_scorer.calculate_risk_score(
                attempt, anomaly_result, behavioral_analysis, user_data
            )

            # Determine if attempt should be blocked
            should_block = self._should_block_attempt(
                risk_score, risk_level, anomaly_result
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                risk_score, risk_level, anomaly_result, behavioral_analysis
            )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            result = IntelligenceResult(
                risk_score=risk_score,
                risk_level=risk_level,
                should_block=should_block,
                anomaly_result=anomaly_result,
                behavioral_analysis=behavioral_analysis,
                recommendations=recommendations,
                processing_time_ms=processing_time,
            )

            self.logger.info(
                f"Intelligence analysis completed: risk_score={risk_score:.3f}, "
                f"risk_level={risk_level}, should_block={should_block}, "
                f"processing_time={processing_time:.1f}ms"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error in intelligence analysis: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Return safe default result on error
            return IntelligenceResult(
                risk_score=0.5,
                risk_level="medium",
                should_block=False,
                recommendations=[
                    "Intelligence analysis failed - manual review recommended"
                ],
                processing_time_ms=processing_time,
            )

    async def calculate_risk_score(
        self, user_data: UserData, context: Dict[str, Any]
    ) -> float:
        """Calculate risk score for authentication context."""
        try:
            await self.initialize()

            # Create login attempt from context
            attempt = LoginAttempt(
                user_id=user_data.user_id,
                email=user_data.email,
                ip_address=context.get("ip_address", "unknown"),
                user_agent=context.get("user_agent", ""),
                timestamp=datetime.utcnow(),
                device_fingerprint=context.get("device_fingerprint"),
                geolocation=context.get("geolocation"),
                session_context=context.get("session_context"),
            )

            # Analyze the attempt
            result = await self.analyze_login_attempt(attempt, user_data)
            return result.risk_score

        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 0.5  # Default medium risk

    def _should_block_attempt(
        self,
        risk_score: float,
        risk_level: str,
        anomaly_result: Optional[AnomalyResult],
    ) -> bool:
        """Determine if an authentication attempt should be blocked."""
        # Block if risk score is above high threshold
        if risk_score >= self.config.intelligence.risk_threshold_high:
            return True

        # Block if multiple high-confidence anomalies detected
        if (
            anomaly_result
            and anomaly_result.is_anomaly
            and anomaly_result.confidence > 0.8
            and len(anomaly_result.anomaly_types) >= 2
        ):
            return True

        return False

    def _generate_recommendations(
        self,
        risk_score: float,
        risk_level: str,
        anomaly_result: Optional[AnomalyResult],
        behavioral_analysis: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        if risk_level == "critical":
            recommendations.append("Block authentication attempt immediately")
            recommendations.append("Require additional verification")
        elif risk_level == "high":
            recommendations.append("Require multi-factor authentication")
            recommendations.append("Monitor user activity closely")
        elif risk_level == "medium":
            recommendations.append("Consider additional verification")
            recommendations.append("Log for security review")

        if anomaly_result and anomaly_result.is_anomaly:
            for anomaly_type in anomaly_result.anomaly_types:
                if anomaly_type == "unusual_location":
                    recommendations.append("Verify user location via email or SMS")
                elif anomaly_type == "unusual_device":
                    recommendations.append("Send device verification notification")
                elif anomaly_type == "unusual_time":
                    recommendations.append("Consider time-based access restrictions")

        if behavioral_analysis and behavioral_analysis.get("status") == "success":
            analysis = behavioral_analysis.get("analysis", {})
            if not analysis.get("pattern_established", False):
                recommendations.append(
                    "Establish behavioral baseline with more login data"
                )

        return recommendations

    async def shutdown(self) -> None:
        """Gracefully shutdown the intelligence engine and its components."""
        if not self._initialized:
            return

        self.logger.info("Shutting down intelligence engine")

        try:
            if hasattr(self.anomaly_detector, "shutdown"):
                await self.anomaly_detector.shutdown()
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Error shutting down anomaly detector: {e}")

        try:
            if hasattr(self.behavioral_analyzer, "shutdown"):
                await self.behavioral_analyzer.shutdown()
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Error shutting down behavioral analyzer: {e}")

        try:
            if hasattr(self.risk_scorer, "shutdown"):
                await self.risk_scorer.shutdown()
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Error shutting down risk scorer: {e}")

        self._initialized = False
        self.logger.info("Intelligence engine shutdown complete")

    async def get_stats(self) -> Dict[str, Any]:
        """Get intelligence engine statistics."""
        return {
            "initialized": self._initialized,
            "anomaly_detection_enabled": self.config.intelligence.enable_anomaly_detection,
            "behavioral_analysis_enabled": self.config.intelligence.enable_behavioral_analysis,
            "threat_detection_enabled": self.config.intelligence.enable_threat_detection,
            "risk_thresholds": {
                "low": self.config.intelligence.risk_threshold_low,
                "medium": self.config.intelligence.risk_threshold_medium,
                "high": self.config.intelligence.risk_threshold_high,
            },
            "model_settings": {
                "min_training_samples": self.config.intelligence.min_training_samples,
                "behavioral_window_days": self.config.intelligence.behavioral_window_days,
                "online_learning_enabled": self.config.intelligence.enable_online_learning,
            },
            "sensitivity_settings": {
                "location": self.config.intelligence.location_sensitivity,
                "time": self.config.intelligence.time_sensitivity,
                "device": self.config.intelligence.device_sensitivity,
            },
        }
