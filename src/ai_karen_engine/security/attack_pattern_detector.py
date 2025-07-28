"""
Attack pattern detection service for intelligent authentication system.

This module provides comprehensive attack pattern detection including brute force,
credential stuffing, account takeover detection, and coordinated attack campaign
analysis with temporal and spatial correlation capabilities.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
import hashlib
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque, Counter
from cachetools import TTLCache
import threading

from ai_karen_engine.security.models import (
    AuthContext,
    BruteForceIndicators,
    CredentialStuffingIndicators,
    AccountTakeoverIndicators,
    ThreatAnalysis,
    RiskLevel,
    IntelligentAuthConfig
)
from ai_karen_engine.security.intelligent_auth_base import (
    BaseIntelligentAuthService,
    ServiceHealthStatus,
    ServiceStatus
)

logger = logging.getLogger(__name__)


@dataclass
class AttackSignature:
    """Attack signature for pattern matching."""
    
    signature_id: str
    attack_type: str  # "brute_force", "credential_stuffing", "account_takeover", "campaign"
    pattern_indicators: Dict[str, Any]
    severity_score: float
    confidence_threshold: float
    temporal_window: timedelta
    spatial_correlation: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    match_count: int = 0
    
    def matches(self, context: AuthContext, recent_attempts: List[Dict]) -> Tuple[bool, float]:
        """Check if context matches this attack signature."""
        try:
            confidence = 0.0
            
            # Check pattern indicators
            for indicator, expected_value in self.pattern_indicators.items():
                if self._check_indicator(indicator, expected_value, context, recent_attempts):
                    confidence += 0.2
            
            # Normalize confidence
            confidence = min(confidence, 1.0)
            
            return confidence >= self.confidence_threshold, confidence
            
        except Exception as e:
            logger.error(f"Error matching signature {self.signature_id}: {e}")
            return False, 0.0
    
    def _check_indicator(self, indicator: str, expected_value: Any, 
                        context: AuthContext, recent_attempts: List[Dict]) -> bool:
        """Check individual pattern indicator."""
        try:
            if indicator == "rapid_attempts":
                return self._check_rapid_attempts(expected_value, recent_attempts)
            elif indicator == "multiple_ips":
                return self._check_multiple_ips(expected_value, recent_attempts)
            elif indicator == "user_agent_rotation":
                return self._check_user_agent_rotation(expected_value, recent_attempts)
            elif indicator == "location_jumping":
                return self._check_location_jumping(expected_value, context, recent_attempts)
            elif indicator == "credential_patterns":
                return self._check_credential_patterns(expected_value, recent_attempts)
            elif indicator == "timing_patterns":
                return self._check_timing_patterns(expected_value, recent_attempts)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error checking indicator {indicator}: {e}")
            return False
    
    def _check_rapid_attempts(self, threshold: int, recent_attempts: List[Dict]) -> bool:
        """Check for rapid authentication attempts."""
        return len(recent_attempts) >= threshold
    
    def _check_multiple_ips(self, threshold: int, recent_attempts: List[Dict]) -> bool:
        """Check for attempts from multiple IP addresses."""
        ips = set(attempt.get('ip', '') for attempt in recent_attempts)
        return len(ips) >= threshold
    
    def _check_user_agent_rotation(self, threshold: int, recent_attempts: List[Dict]) -> bool:
        """Check for user agent rotation patterns."""
        user_agents = set(attempt.get('user_agent', '') for attempt in recent_attempts)
        return len(user_agents) >= threshold
    
    def _check_location_jumping(self, threshold: float, context: AuthContext, 
                               recent_attempts: List[Dict]) -> bool:
        """Check for impossible location changes."""
        if not context.geolocation:
            return False
        
        # Check for rapid location changes that would be impossible
        for attempt in recent_attempts:
            if attempt.get('geolocation'):
                # Calculate distance and time difference
                # This is a simplified check - would need proper geolocation distance calculation
                time_diff = (context.timestamp - attempt.get('timestamp', context.timestamp)).total_seconds()
                if time_diff < 3600:  # Less than 1 hour
                    # If locations are different countries, likely impossible
                    if (context.geolocation.country != attempt['geolocation'].get('country', '') and
                        time_diff < 1800):  # Less than 30 minutes
                        return True
        
        return False
    
    def _check_credential_patterns(self, patterns: List[str], recent_attempts: List[Dict]) -> bool:
        """Check for credential stuffing patterns."""
        emails = [attempt.get('email', '') for attempt in recent_attempts]
        
        # Check for common patterns in credential stuffing
        for pattern in patterns:
            if pattern == "sequential_emails":
                # Check for sequential email patterns
                if self._has_sequential_pattern(emails):
                    return True
            elif pattern == "dictionary_emails":
                # Check for dictionary-based email patterns
                if self._has_dictionary_pattern(emails):
                    return True
        
        return False
    
    def _check_timing_patterns(self, pattern_type: str, recent_attempts: List[Dict]) -> bool:
        """Check for suspicious timing patterns."""
        if len(recent_attempts) < 2:
            return False
        
        timestamps = [attempt.get('timestamp', datetime.now()) for attempt in recent_attempts]
        timestamps.sort()
        
        if pattern_type == "regular_intervals":
            # Check for too-regular timing intervals (bot behavior)
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            if len(intervals) >= 3:
                # Check if intervals are suspiciously regular
                interval_variance = statistics.variance(intervals) if len(intervals) > 1 else 0
                return interval_variance < 1.0  # Very low variance indicates bot behavior
        
        return False
    
    def _has_sequential_pattern(self, emails: List[str]) -> bool:
        """Check for sequential patterns in email addresses."""
        # Simplified check for sequential patterns
        numeric_parts = []
        for email in emails:
            # Extract numeric parts from email
            import re
            numbers = re.findall(r'\d+', email)
            if numbers:
                numeric_parts.extend([int(n) for n in numbers])
        
        if len(numeric_parts) >= 3:
            numeric_parts.sort()
            # Check if numbers are sequential
            for i in range(1, len(numeric_parts)):
                if numeric_parts[i] - numeric_parts[i-1] == 1:
                    return True
        
        return False
    
    def _has_dictionary_pattern(self, emails: List[str]) -> bool:
        """Check for dictionary-based patterns in emails."""
        # Common dictionary words used in credential stuffing
        common_words = ['admin', 'test', 'user', 'demo', 'guest', 'info', 'support']
        
        for email in emails:
            email_lower = email.lower()
            for word in common_words:
                if word in email_lower:
                    return True
        
        return False


@dataclass
class AttackCampaign:
    """Coordinated attack campaign tracking."""
    
    campaign_id: str
    attack_type: str
    start_time: datetime
    last_activity: datetime
    source_ips: Set[str] = field(default_factory=set)
    target_accounts: Set[str] = field(default_factory=set)
    user_agents: Set[str] = field(default_factory=set)
    attempt_count: int = 0
    success_count: int = 0
    countries: Set[str] = field(default_factory=set)
    attack_signatures: List[str] = field(default_factory=list)
    severity_score: float = 0.0
    
    def update_activity(self, context: AuthContext, success: bool = False):
        """Update campaign with new activity."""
        self.last_activity = context.timestamp
        self.source_ips.add(context.client_ip)
        self.target_accounts.add(context.email)
        self.user_agents.add(context.user_agent)
        self.attempt_count += 1
        
        if success:
            self.success_count += 1
        
        if context.geolocation:
            self.countries.add(context.geolocation.country)
        
        # Update severity score based on campaign characteristics
        self._calculate_severity_score()
    
    def _calculate_severity_score(self):
        """Calculate campaign severity score."""
        score = 0.0
        
        # Score based on scale
        score += min(len(self.source_ips) / 100, 0.3)  # IP diversity
        score += min(len(self.target_accounts) / 1000, 0.3)  # Target scale
        score += min(self.attempt_count / 10000, 0.2)  # Volume
        
        # Score based on success rate
        if self.attempt_count > 0:
            success_rate = self.success_count / self.attempt_count
            score += success_rate * 0.2
        
        self.severity_score = min(score, 1.0)
    
    def is_active(self, max_idle_time: timedelta = timedelta(hours=1)) -> bool:
        """Check if campaign is still active."""
        return datetime.now() - self.last_activity < max_idle_time
    
    def get_campaign_summary(self) -> Dict[str, Any]:
        """Get campaign summary for analysis."""
        duration = self.last_activity - self.start_time
        
        return {
            'campaign_id': self.campaign_id,
            'attack_type': self.attack_type,
            'duration_hours': duration.total_seconds() / 3600,
            'source_ip_count': len(self.source_ips),
            'target_account_count': len(self.target_accounts),
            'attempt_count': self.attempt_count,
            'success_count': self.success_count,
            'success_rate': self.success_count / max(self.attempt_count, 1),
            'country_count': len(self.countries),
            'severity_score': self.severity_score,
            'is_active': self.is_active()
        }


class AttackPatternDetector(BaseIntelligentAuthService):
    """
    Comprehensive attack pattern detection service for identifying coordinated
    attacks, campaigns, and sophisticated threat patterns.
    """
    
    def __init__(self, config: IntelligentAuthConfig):
        super().__init__(config)
        
        # Attack signature database
        self.attack_signatures: Dict[str, AttackSignature] = {}
        self.signatures_lock = threading.RLock()
        
        # Active attack campaigns
        self.active_campaigns: Dict[str, AttackCampaign] = {}
        self.campaigns_lock = threading.RLock()
        
        # Recent authentication attempts for pattern analysis
        self.recent_attempts: deque = deque(maxlen=50000)  # Larger buffer for pattern analysis
        self.attempts_lock = threading.RLock()
        
        # IP-based tracking for distributed attacks
        self.ip_attempt_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.ip_history_lock = threading.RLock()
        
        # User-based tracking for account takeover detection
        self.user_attempt_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self.user_history_lock = threading.RLock()
        
        # Caching for pattern detection results
        self.pattern_cache = TTLCache(
            maxsize=config.cache_size,
            ttl=300  # 5 minute TTL for pattern detection
        )
        self.cache_lock = threading.RLock()
        
        # Metrics tracking
        self._pattern_detections = 0
        self._campaign_detections = 0
        self._brute_force_detections = 0
        self._credential_stuffing_detections = 0
        self._account_takeover_detections = 0
        self._processing_times = []
        
        # Model version for tracking
        self.model_version = "attack_pattern_detector_v1.0"
        
        # Initialize default attack signatures
        self._initialize_default_signatures()
        
        self.logger.info("AttackPatternDetector initialized")
    
    async def initialize(self) -> bool:
        """Initialize the attack pattern detection service."""
        try:
            # Load persisted attack signatures
            await self._load_attack_signatures()
            
            # Load active campaigns
            await self._load_active_campaigns()
            
            # Start background cleanup task
            asyncio.create_task(self._cleanup_inactive_campaigns())
            
            self.logger.info("AttackPatternDetector initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AttackPatternDetector: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""
        try:
            # Save attack signatures
            await self._save_attack_signatures()
            
            # Save active campaigns
            await self._save_active_campaigns()
            
            # Clear caches and data structures
            with self.cache_lock:
                self.pattern_cache.clear()
            
            with self.attempts_lock:
                self.recent_attempts.clear()
            
            with self.ip_history_lock:
                self.ip_attempt_history.clear()
            
            with self.user_history_lock:
                self.user_attempt_history.clear()
            
            self.logger.info("AttackPatternDetector shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during AttackPatternDetector shutdown: {e}")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check for the attack pattern detector."""
        try:
            # Test basic pattern detection
            test_context = self._create_test_auth_context()
            
            # Perform test detection
            result = await self.detect_attack_patterns(test_context)
            
            return (
                result is not None and
                hasattr(result, 'brute_force_indicators') and
                hasattr(result, 'credential_stuffing_indicators') and
                hasattr(result, 'account_takeover_indicators')
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False    
        
    async def detect_attack_patterns(self, context: AuthContext) -> ThreatAnalysis:
        """
        Detect attack patterns in authentication attempt.
        
        Args:
            context: Authentication context
            
        Returns:
            ThreatAnalysis with attack pattern detection results
        """
        start_time = time.time()
        
        try:
            # Store attempt for pattern analysis
            await self._store_attempt(context)
            
            # Get recent attempts for pattern analysis
            recent_attempts = await self._get_recent_attempts(context)
            
            # Detect specific attack patterns
            brute_force_indicators = await self._detect_brute_force(context, recent_attempts)
            credential_stuffing_indicators = await self._detect_credential_stuffing(context, recent_attempts)
            account_takeover_indicators = await self._detect_account_takeover(context, recent_attempts)
            
            # Detect coordinated campaigns
            campaign_correlation = await self._detect_attack_campaigns(context, recent_attempts)
            
            # Match against attack signatures
            matched_signatures = await self._match_attack_signatures(context, recent_attempts)
            
            # Calculate threat intelligence scores
            ip_reputation_score = await self._calculate_ip_reputation(context.client_ip)
            
            # Create comprehensive threat analysis
            threat_analysis = ThreatAnalysis(
                ip_reputation_score=ip_reputation_score,
                known_attack_patterns=matched_signatures,
                threat_actor_indicators=await self._identify_threat_actors(context, recent_attempts),
                brute_force_indicators=brute_force_indicators,
                credential_stuffing_indicators=credential_stuffing_indicators,
                account_takeover_indicators=account_takeover_indicators,
                similar_attacks_detected=len(recent_attempts),
                attack_campaign_correlation=campaign_correlation
            )
            
            processing_time = time.time() - start_time
            
            # Update metrics
            self._pattern_detections += 1
            self._processing_times.append(processing_time)
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]
            
            # Update specific detection counters
            if brute_force_indicators.rapid_attempts:
                self._brute_force_detections += 1
            if credential_stuffing_indicators.multiple_accounts:
                self._credential_stuffing_detections += 1
            if account_takeover_indicators.location_anomaly:
                self._account_takeover_detections += 1
            
            self.logger.debug(
                f"Attack pattern detection completed for {context.email}: "
                f"patterns={len(matched_signatures)}, time={processing_time:.3f}s"
            )
            
            return threat_analysis
            
        except Exception as e:
            self.logger.error(f"Attack pattern detection failed: {e}")
            # Return fallback threat analysis
            return self._create_fallback_threat_analysis(context, start_time)
    
    async def _detect_brute_force(self, context: AuthContext, 
                                 recent_attempts: List[Dict]) -> BruteForceIndicators:
        """Detect brute force attack indicators."""
        try:
            # Get IP-specific attempts
            ip_attempts = await self._get_ip_attempts(context.client_ip, timedelta(minutes=15))
            user_attempts = await self._get_user_attempts(context.email, timedelta(minutes=30))
            
            # Check for rapid attempts
            rapid_attempts = len(ip_attempts) >= 10 or len(user_attempts) >= 5
            
            # Check for high failure rate
            failed_attempts = sum(1 for attempt in ip_attempts if not attempt.get('success', False))
            high_failure_rate = failed_attempts / max(len(ip_attempts), 1) > 0.8
            
            # Check for password variations
            password_variations = self._detect_password_variations(user_attempts)
            
            # Check for distributed attempts (same user, multiple IPs)
            distributed_ips = set(attempt.get('ip', '') for attempt in user_attempts)
            distributed_attack = len(distributed_ips) >= 3
            
            # Check for timing patterns
            timing_patterns = self._analyze_timing_patterns(ip_attempts)
            
            return BruteForceIndicators(
                rapid_attempts=rapid_attempts,
                multiple_ips=distributed_attack,
                password_variations=password_variations,
                time_pattern_score=1.0 if timing_patterns else 0.0
            )
            
        except Exception as e:
            self.logger.error(f"Brute force detection failed: {e}")
            return BruteForceIndicators()
    
    async def _detect_credential_stuffing(self, context: AuthContext,
                                         recent_attempts: List[Dict]) -> CredentialStuffingIndicators:
        """Detect credential stuffing attack indicators."""
        try:
            # Get IP-specific attempts across multiple accounts
            ip_attempts = await self._get_ip_attempts(context.client_ip, timedelta(hours=1))
            
            # Check for multiple accounts from same IP
            unique_accounts = set(attempt.get('email', '') for attempt in ip_attempts)
            multiple_accounts = len(unique_accounts) >= 5
            
            # Check for low success rate (typical of credential stuffing)
            successful_attempts = sum(1 for attempt in ip_attempts if attempt.get('success', False))
            low_success_rate = successful_attempts / max(len(ip_attempts), 1) < 0.05
            
            # Check for user agent rotation
            user_agents = set(attempt.get('user_agent', '') for attempt in ip_attempts)
            user_agent_rotation = len(user_agents) >= 3
            
            # Check for credential list patterns
            credential_list_patterns = self._detect_credential_list_patterns(ip_attempts)
            
            # Check for automated behavior patterns
            automated_patterns = self._detect_automated_patterns(ip_attempts)
            
            return CredentialStuffingIndicators(
                multiple_accounts=multiple_accounts,
                common_passwords=credential_list_patterns,
                distributed_sources=user_agent_rotation,
                success_rate_pattern=successful_attempts / max(len(ip_attempts), 1)
            )
            
        except Exception as e:
            self.logger.error(f"Credential stuffing detection failed: {e}")
            return CredentialStuffingIndicators()
    
    async def _detect_account_takeover(self, context: AuthContext,
                                      recent_attempts: List[Dict]) -> AccountTakeoverIndicators:
        """Detect account takeover attack indicators."""
        try:
            # Get user-specific attempt history
            user_attempts = await self._get_user_attempts(context.email, timedelta(days=7))
            
            # Check for location anomaly
            location_anomaly = self._detect_location_anomaly(context, user_attempts)
            
            # Check for device anomaly
            device_anomaly = self._detect_device_anomaly(context, user_attempts)
            
            # Check for behavioral changes
            behavioral_changes = self._detect_behavioral_changes(context, user_attempts)
            
            # Check for credential changes
            credential_changes = self._detect_credential_changes(context, user_attempts)
            
            # Check for session anomalies
            session_anomalies = self._detect_session_anomalies(context, user_attempts)
            
            return AccountTakeoverIndicators(
                location_anomaly=location_anomaly,
                device_change=device_anomaly,
                behavior_change=behavioral_changes,
                privilege_escalation=credential_changes
            )
            
        except Exception as e:
            self.logger.error(f"Account takeover detection failed: {e}")
            return AccountTakeoverIndicators()
    
    async def _detect_attack_campaigns(self, context: AuthContext,
                                      recent_attempts: List[Dict]) -> Optional[str]:
        """Detect coordinated attack campaigns."""
        try:
            # Check for existing campaigns that match this attempt
            matching_campaign = await self._find_matching_campaign(context, recent_attempts)
            
            if matching_campaign:
                # Update existing campaign
                with self.campaigns_lock:
                    campaign = self.active_campaigns[matching_campaign]
                    campaign.update_activity(context)
                    self._campaign_detections += 1
                
                return matching_campaign
            
            # Check if this attempt should start a new campaign
            if await self._should_create_campaign(context, recent_attempts):
                campaign_id = await self._create_new_campaign(context, recent_attempts)
                return campaign_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Campaign detection failed: {e}")
            return None
    
    async def _match_attack_signatures(self, context: AuthContext,
                                      recent_attempts: List[Dict]) -> List[str]:
        """Match authentication attempt against known attack signatures."""
        try:
            matched_signatures = []
            
            with self.signatures_lock:
                for signature_id, signature in self.attack_signatures.items():
                    matches, confidence = signature.matches(context, recent_attempts)
                    
                    if matches:
                        matched_signatures.append(signature_id)
                        signature.match_count += 1
                        signature.last_updated = datetime.now()
                        
                        self.logger.info(
                            f"Attack signature match: {signature_id} "
                            f"(confidence: {confidence:.2f})"
                        )
            
            return matched_signatures
            
        except Exception as e:
            self.logger.error(f"Signature matching failed: {e}")
            return []
    
    async def _identify_threat_actors(self, context: AuthContext,
                                     recent_attempts: List[Dict]) -> List[str]:
        """Identify potential threat actors based on attack patterns."""
        try:
            threat_actors = []
            
            # Check for known threat actor patterns
            if await self._matches_apt_patterns(context, recent_attempts):
                threat_actors.append("APT_GROUP")
            
            if await self._matches_cybercriminal_patterns(context, recent_attempts):
                threat_actors.append("CYBERCRIMINAL")
            
            if await self._matches_script_kiddie_patterns(context, recent_attempts):
                threat_actors.append("SCRIPT_KIDDIE")
            
            if await self._matches_insider_threat_patterns(context, recent_attempts):
                threat_actors.append("INSIDER_THREAT")
            
            return threat_actors
            
        except Exception as e:
            self.logger.error(f"Threat actor identification failed: {e}")
            return []
    
    async def _store_attempt(self, context: AuthContext):
        """Store authentication attempt for pattern analysis."""
        try:
            attempt_data = {
                'timestamp': context.timestamp,
                'email': context.email,
                'ip': context.client_ip,
                'user_agent': context.user_agent,
                'geolocation': context.geolocation.to_dict() if context.geolocation else None,
                'is_tor': context.is_tor_exit_node,
                'is_vpn': context.is_vpn,
                'threat_score': context.threat_intel_score,
                'failed_attempts': context.previous_failed_attempts,
                'success': False  # Will be updated later if login succeeds
            }
            
            # Store in recent attempts
            with self.attempts_lock:
                self.recent_attempts.append(attempt_data)
            
            # Store in IP-specific history
            with self.ip_history_lock:
                self.ip_attempt_history[context.client_ip].append(attempt_data)
            
            # Store in user-specific history
            with self.user_history_lock:
                self.user_attempt_history[context.email].append(attempt_data)
            
        except Exception as e:
            self.logger.error(f"Failed to store attempt: {e}")
    
    async def _get_recent_attempts(self, context: AuthContext,
                                  time_window: timedelta = timedelta(minutes=30)) -> List[Dict]:
        """Get recent attempts within time window."""
        try:
            cutoff_time = context.timestamp - time_window
            recent = []
            
            with self.attempts_lock:
                for attempt in self.recent_attempts:
                    if attempt['timestamp'] > cutoff_time:
                        recent.append(attempt)
            
            return recent
            
        except Exception as e:
            self.logger.error(f"Failed to get recent attempts: {e}")
            return []
    
    async def _get_ip_attempts(self, ip: str, time_window: timedelta) -> List[Dict]:
        """Get attempts from specific IP within time window."""
        try:
            cutoff_time = datetime.now() - time_window
            attempts = []
            
            with self.ip_history_lock:
                if ip in self.ip_attempt_history:
                    for attempt in self.ip_attempt_history[ip]:
                        if attempt['timestamp'] > cutoff_time:
                            attempts.append(attempt)
            
            return attempts
            
        except Exception as e:
            self.logger.error(f"Failed to get IP attempts: {e}")
            return []
    
    async def _get_user_attempts(self, email: str, time_window: timedelta) -> List[Dict]:
        """Get attempts for specific user within time window."""
        try:
            cutoff_time = datetime.now() - time_window
            attempts = []
            
            with self.user_history_lock:
                if email in self.user_attempt_history:
                    for attempt in self.user_attempt_history[email]:
                        if attempt['timestamp'] > cutoff_time:
                            attempts.append(attempt)
            
            return attempts
            
        except Exception as e:
            self.logger.error(f"Failed to get user attempts: {e}")
            return []    
        
    def _detect_password_variations(self, attempts: List[Dict]) -> bool:
        """Detect password variation patterns in brute force attacks."""
        try:
            # This would analyze password patterns if we had access to them
            # For security, we only have hashes, so we check for other indicators
            
            # Check for rapid attempts with different failure patterns
            if len(attempts) >= 5:
                # Look for systematic attempt patterns
                time_intervals = []
                for i in range(1, len(attempts)):
                    interval = (attempts[i]['timestamp'] - attempts[i-1]['timestamp']).total_seconds()
                    time_intervals.append(interval)
                
                # Very regular intervals suggest automated password variation
                if len(time_intervals) >= 3:
                    avg_interval = statistics.mean(time_intervals)
                    if avg_interval < 5 and statistics.stdev(time_intervals) < 1:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Password variation detection failed: {e}")
            return False
    
    def _analyze_timing_patterns(self, attempts: List[Dict]) -> bool:
        """Analyze timing patterns for automated behavior."""
        try:
            if len(attempts) < 3:
                return False
            
            timestamps = [attempt['timestamp'] for attempt in attempts]
            timestamps.sort()
            
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            # Check for suspiciously regular timing
            if len(intervals) >= 3:
                variance = statistics.variance(intervals)
                mean_interval = statistics.mean(intervals)
                
                # Low variance with short intervals indicates automation
                return variance < 2.0 and mean_interval < 10
            
            return False
            
        except Exception as e:
            self.logger.error(f"Timing pattern analysis failed: {e}")
            return False
    
    def _detect_credential_list_patterns(self, attempts: List[Dict]) -> bool:
        """Detect patterns indicating use of credential lists."""
        try:
            emails = [attempt.get('email', '') for attempt in attempts]
            
            # Check for common credential stuffing patterns
            patterns = [
                self._has_sequential_usernames(emails),
                self._has_dictionary_usernames(emails),
                self._has_common_domain_patterns(emails),
                self._has_leaked_credential_patterns(emails)
            ]
            
            return any(patterns)
            
        except Exception as e:
            self.logger.error(f"Credential list pattern detection failed: {e}")
            return False
    
    def _detect_automated_patterns(self, attempts: List[Dict]) -> bool:
        """Detect automated behavior patterns."""
        try:
            if len(attempts) < 5:
                return False
            
            # Check user agent consistency (bots often use same UA)
            user_agents = [attempt.get('user_agent', '') for attempt in attempts]
            unique_uas = set(user_agents)
            
            # Too consistent user agents
            if len(unique_uas) == 1 and len(attempts) > 10:
                return True
            
            # Check for bot-like user agent strings
            for ua in unique_uas:
                if self._is_bot_user_agent(ua):
                    return True
            
            # Check timing regularity
            return self._analyze_timing_patterns(attempts)
            
        except Exception as e:
            self.logger.error(f"Automated pattern detection failed: {e}")
            return False
    
    def _detect_location_anomaly(self, context: AuthContext, user_attempts: List[Dict]) -> bool:
        """Detect location anomalies for account takeover."""
        try:
            if not context.geolocation:
                return False
            
            # Get recent successful logins
            recent_successful = [
                attempt for attempt in user_attempts[-10:]
                if attempt.get('success', False) and attempt.get('geolocation')
            ]
            
            if not recent_successful:
                return False
            
            # Check for impossible travel
            for attempt in recent_successful:
                time_diff = (context.timestamp - attempt['timestamp']).total_seconds()
                
                # If login is from different country within short time
                if (time_diff < 3600 and  # Less than 1 hour
                    context.geolocation.country != attempt['geolocation'].get('country', '')):
                    return True
                
                # If login is from very different timezone
                if abs(self._get_timezone_offset(context.geolocation.timezone) - 
                      self._get_timezone_offset(attempt['geolocation'].get('timezone', 'UTC'))) > 8:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Location anomaly detection failed: {e}")
            return False
    
    def _detect_device_anomaly(self, context: AuthContext, user_attempts: List[Dict]) -> bool:
        """Detect device anomalies for account takeover."""
        try:
            # Get recent user agents
            recent_uas = [attempt.get('user_agent', '') for attempt in user_attempts[-20:]]
            
            # Check if current user agent is completely new
            if context.user_agent not in recent_uas:
                # Check if it's a completely different type of device
                current_device_type = self._get_device_type(context.user_agent)
                recent_device_types = set(self._get_device_type(ua) for ua in recent_uas)
                
                if current_device_type not in recent_device_types:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Device anomaly detection failed: {e}")
            return False
    
    def _detect_behavioral_changes(self, context: AuthContext, user_attempts: List[Dict]) -> bool:
        """Detect behavioral changes indicating account takeover."""
        try:
            if len(user_attempts) < 10:
                return False
            
            # Analyze login time patterns
            recent_hours = [attempt['timestamp'].hour for attempt in user_attempts[-10:]]
            current_hour = context.timestamp.hour
            
            # Check if current login time is unusual
            if recent_hours:
                avg_hour = statistics.mean(recent_hours)
                hour_std = statistics.stdev(recent_hours) if len(recent_hours) > 1 else 12
                
                # If current hour is more than 2 standard deviations away
                if abs(current_hour - avg_hour) > 2 * hour_std:
                    return True
            
            # Check login frequency changes
            recent_intervals = []
            for i in range(1, len(user_attempts)):
                interval = (user_attempts[i]['timestamp'] - user_attempts[i-1]['timestamp']).total_seconds()
                recent_intervals.append(interval)
            
            if recent_intervals:
                avg_interval = statistics.mean(recent_intervals)
                # Sudden change in login frequency
                last_interval = (context.timestamp - user_attempts[-1]['timestamp']).total_seconds()
                
                if last_interval < avg_interval / 10:  # Much more frequent
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Behavioral change detection failed: {e}")
            return False
    
    def _detect_credential_changes(self, context: AuthContext, user_attempts: List[Dict]) -> bool:
        """Detect credential changes indicating account takeover."""
        try:
            # This would check for password changes, but we only have hashes
            # Instead, check for patterns that might indicate credential compromise
            
            # Check for sudden increase in failed attempts followed by success
            recent_failures = sum(1 for attempt in user_attempts[-5:] if not attempt.get('success', False))
            
            if recent_failures >= 3:
                # Multiple recent failures might indicate credential testing
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Credential change detection failed: {e}")
            return False
    
    def _detect_session_anomalies(self, context: AuthContext, user_attempts: List[Dict]) -> bool:
        """Detect session anomalies indicating account takeover."""
        try:
            # Check for concurrent sessions from different locations
            # This would require session tracking, which we simulate
            
            recent_ips = set(attempt.get('ip', '') for attempt in user_attempts[-5:])
            
            # Multiple IPs in recent attempts might indicate session hijacking
            if len(recent_ips) >= 3:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Session anomaly detection failed: {e}")
            return False
    
    def _calculate_takeover_risk_score(self, location_anomaly: bool, device_anomaly: bool,
                                      behavioral_changes: bool, credential_changes: bool,
                                      session_anomalies: bool) -> float:
        """Calculate account takeover risk score."""
        score = 0.0
        
        if location_anomaly:
            score += 0.3
        if device_anomaly:
            score += 0.2
        if behavioral_changes:
            score += 0.2
        if credential_changes:
            score += 0.2
        if session_anomalies:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _find_matching_campaign(self, context: AuthContext, 
                                     recent_attempts: List[Dict]) -> Optional[str]:
        """Find existing campaign that matches current attempt."""
        try:
            with self.campaigns_lock:
                for campaign_id, campaign in self.active_campaigns.items():
                    if not campaign.is_active():
                        continue
                    
                    # Check if attempt matches campaign characteristics
                    if (context.client_ip in campaign.source_ips or
                        context.email in campaign.target_accounts or
                        context.user_agent in campaign.user_agents):
                        
                        # Additional correlation checks
                        if self._correlates_with_campaign(context, campaign):
                            return campaign_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Campaign matching failed: {e}")
            return None
    
    def _correlates_with_campaign(self, context: AuthContext, campaign: AttackCampaign) -> bool:
        """Check if context correlates with existing campaign."""
        try:
            # Time correlation
            time_diff = (context.timestamp - campaign.last_activity).total_seconds()
            if time_diff > 3600:  # More than 1 hour gap
                return False
            
            # Geographic correlation
            if context.geolocation and campaign.countries:
                if context.geolocation.country not in campaign.countries:
                    # Allow expansion to nearby countries
                    if len(campaign.countries) > 3:  # Already distributed
                        return True
                    else:
                        return False
            
            # Attack type correlation
            # This would be more sophisticated in practice
            return True
            
        except Exception as e:
            self.logger.error(f"Campaign correlation check failed: {e}")
            return False
    
    async def _should_create_campaign(self, context: AuthContext, 
                                     recent_attempts: List[Dict]) -> bool:
        """Determine if a new campaign should be created."""
        try:
            # Check for minimum threshold of coordinated activity
            ip_attempts = [attempt for attempt in recent_attempts 
                          if attempt.get('ip') == context.client_ip]
            
            # Need multiple attempts from same IP
            if len(ip_attempts) < 5:
                return False
            
            # Check for multiple targets
            unique_targets = set(attempt.get('email', '') for attempt in ip_attempts)
            if len(unique_targets) < 3:
                return False
            
            # Check time window (campaign-like activity)
            time_span = max(attempt['timestamp'] for attempt in ip_attempts) - \
                       min(attempt['timestamp'] for attempt in ip_attempts)
            
            if time_span.total_seconds() < 300:  # At least 5 minutes of activity
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Campaign creation check failed: {e}")
            return False
    
    async def _create_new_campaign(self, context: AuthContext, 
                                  recent_attempts: List[Dict]) -> str:
        """Create new attack campaign."""
        try:
            campaign_id = f"campaign_{int(time.time())}_{context.client_ip[:8]}"
            
            # Determine attack type based on patterns
            attack_type = self._determine_attack_type(context, recent_attempts)
            
            campaign = AttackCampaign(
                campaign_id=campaign_id,
                attack_type=attack_type,
                start_time=context.timestamp,
                last_activity=context.timestamp
            )
            
            # Initialize with current attempt
            campaign.update_activity(context)
            
            # Add related attempts
            ip_attempts = [attempt for attempt in recent_attempts 
                          if attempt.get('ip') == context.client_ip]
            
            for attempt in ip_attempts:
                # Create temporary context for each attempt
                temp_context = AuthContext(
                    email=attempt.get('email', ''),
                    password_hash='',
                    client_ip=attempt.get('ip', ''),
                    user_agent=attempt.get('user_agent', ''),
                    timestamp=attempt.get('timestamp', datetime.now()),
                    request_id=f"temp_{int(time.time())}"
                )
                
                if attempt.get('geolocation'):
                    temp_context.geolocation = GeoLocation.from_dict(attempt['geolocation'])
                
                campaign.update_activity(temp_context, attempt.get('success', False))
            
            with self.campaigns_lock:
                self.active_campaigns[campaign_id] = campaign
            
            self.logger.info(f"Created new attack campaign: {campaign_id} ({attack_type})")
            return campaign_id
            
        except Exception as e:
            self.logger.error(f"Campaign creation failed: {e}")
            return f"campaign_error_{int(time.time())}"
    
    def _determine_attack_type(self, context: AuthContext, recent_attempts: List[Dict]) -> str:
        """Determine the type of attack based on patterns."""
        try:
            ip_attempts = [attempt for attempt in recent_attempts 
                          if attempt.get('ip') == context.client_ip]
            
            unique_accounts = set(attempt.get('email', '') for attempt in ip_attempts)
            
            # Credential stuffing: many accounts, low success rate
            if len(unique_accounts) >= 10:
                success_rate = sum(1 for attempt in ip_attempts if attempt.get('success', False)) / len(ip_attempts)
                if success_rate < 0.1:
                    return "credential_stuffing"
            
            # Brute force: few accounts, many attempts
            if len(unique_accounts) <= 3 and len(ip_attempts) >= 10:
                return "brute_force"
            
            # Account takeover: specific targeting
            if len(unique_accounts) <= 5:
                return "account_takeover"
            
            return "mixed_attack"
            
        except Exception as e:
            self.logger.error(f"Attack type determination failed: {e}")
            return "unknown" 
        
    async def _calculate_ip_reputation(self, ip: str) -> float:
        """Calculate IP reputation score."""
        try:
            # This would integrate with threat intelligence feeds
            # For now, implement basic checks
            
            score = 0.0
            
            # Check if IP is in known bad ra      if self._is_known_bad_ip(ip):
            score += 0.5
            
            # Check recent activity from this IP
            recent_attempts = await self._get_ip_attempts(ip, timedelta(hours=24))
            
            if len(recent_attempts) > 100:  # High volume
                score += 0.3
            
            # Check failure rate
            if recent_attempts:
                failures = sum(1 for attempt in recent_attempts if not attempt.get('success', False))
                failure_rate = failures / len(recent_attempts)
                score += failure_rate * 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"IP reputation calculation failed: {e}")
            return 0.0
    
    async def _matches_apt_patterns(self, context: AuthContext, recent_attempts: List[Dict]) -> bool:
        """Check if patterns match Advanced Persistent Threat characteristics."""
        try:
            # APT characteristics: sophisticated, persistent, targeted
            
            # Check for sophisticated evasion techniques
            if context.is_tor_exit_node or context.is_vpn:
                # Check for rotating infrastructure
                ip_attempts = await self._get_ip_attempts(context.client_ip, timedelta(days=7))
                if len(set(attempt.get('ip', '') for attempt in ip_attempts)) > 10:
                    return True
            
            # Check for targeted approach (specific high-value accounts)
            if self._is_high_value_target(context.email):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"APT pattern matching failed: {e}")
            return False
    
    async def _matches_cybercriminal_patterns(self, context: AuthContext, 
                                            recent_attempts: List[Dict]) -> bool:
        """Check if patterns match cybercriminal characteristics."""
        try:
            # Cybercriminal characteristics: volume, automation, profit-driven
            
            ip_attempts = await self._get_ip_attempts(context.client_ip, timedelta(hours=24))
            
            # High volume attacks
            if len(ip_attempts) > 1000:
                return True
            
            # Multiple attack types from same source
            attack_types = set()
            if len([a for a in ip_attempts if len(set(a.get('email', '') for a in ip_attempts)) > 50]):
                attack_types.add('credential_stuffing')
            if len([a for a in ip_attempts if a.get('email', '') == context.email]) > 20:
                attack_types.add('brute_force')
            
            if len(attack_types) > 1:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Cybercriminal pattern matching failed: {e}")
            return False
    
    async def _matches_script_kiddie_patterns(self, context: AuthContext,
                                            recent_attempts: List[Dict]) -> bool:
        """Check if patterns match script kiddie characteristics."""
        try:
            # Script kiddie characteristics: unsophisticated, obvious patterns
            
            # Check for obvious bot user agents
            if self._is_obvious_bot_user_agent(context.user_agent):
                return True
            
            # Check for very regular timing (unsophisticated automation)
            ip_attempts = await self._get_ip_attempts(context.client_ip, timedelta(hours=1))
            if len(ip_attempts) >= 10:
                intervals = []
                for i in range(1, len(ip_attempts)):
                    interval = (ip_attempts[i]['timestamp'] - ip_attempts[i-1]['timestamp']).total_seconds()
                    intervals.append(interval)
                
                if intervals and statistics.stdev(intervals) < 0.5:  # Very regular
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Script kiddie pattern matching failed: {e}")
            return False
    
    async def _matches_insider_threat_patterns(self, context: AuthContext,
                                             recent_attempts: List[Dict]) -> bool:
        """Check if patterns match insider threat characteristics."""
        try:
            # Insider threat characteristics: internal access, unusual behavior
            
            # Check for internal IP ranges (would need organization-specific config)
            if self._is_internal_ip(context.client_ip):
                # Check for unusual access patterns
                user_attempts = await self._get_user_attempts(context.email, timedelta(days=30))
                
                # Unusual time access
                if context.timestamp.hour < 6 or context.timestamp.hour > 22:
                    return True
                
                # Weekend access when not typical
                if context.timestamp.weekday() >= 5:  # Weekend
                    weekend_attempts = sum(1 for attempt in user_attempts 
                                         if attempt['timestamp'].weekday() >= 5)
                    if weekend_attempts / max(len(user_attempts), 1) < 0.1:  # Unusual weekend access
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Insider threat pattern matching failed: {e}")
            return False
    
    def _initialize_default_signatures(self):
        """Initialize default attack signatures."""
        try:
            # Brute force signature
            brute_force_sig = AttackSignature(
                signature_id="brute_force_basic",
                attack_type="brute_force",
                pattern_indicators={
                    "rapid_attempts": 10,
                    "timing_patterns": "regular_intervals"
                },
                severity_score=0.7,
                confidence_threshold=0.6,
                temporal_window=timedelta(minutes=15)
            )
            
            # Credential stuffing signature
            credential_stuffing_sig = AttackSignature(
                signature_id="credential_stuffing_basic",
                attack_type="credential_stuffing",
                pattern_indicators={
                    "multiple_ips": 3,
                    "credential_patterns": ["sequential_emails", "dictionary_emails"]
                },
                severity_score=0.8,
                confidence_threshold=0.7,
                temporal_window=timedelta(hours=1)
            )
            
            # Account takeover signature
            account_takeover_sig = AttackSignature(
                signature_id="account_takeover_basic",
                attack_type="account_takeover",
                pattern_indicators={
                    "location_jumping": 1000.0,  # km threshold
                    "user_agent_rotation": 2
                },
                severity_score=0.9,
                confidence_threshold=0.8,
                temporal_window=timedelta(hours=6),
                spatial_correlation=True
            )
            
            # Distributed attack signature
            distributed_attack_sig = AttackSignature(
                signature_id="distributed_attack",
                attack_type="campaign",
                pattern_indicators={
                    "multiple_ips": 5,
                    "rapid_attempts": 50,
                    "timing_patterns": "coordinated"
                },
                severity_score=0.9,
                confidence_threshold=0.8,
                temporal_window=timedelta(hours=2),
                spatial_correlation=True
            )
            
            with self.signatures_lock:
                self.attack_signatures = {
                    "brute_force_basic": brute_force_sig,
                    "credential_stuffing_basic": credential_stuffing_sig,
                    "account_takeover_basic": account_takeover_sig,
                    "distributed_attack": distributed_attack_sig
                }
            
            self.logger.info(f"Initialized {len(self.attack_signatures)} default attack signatures")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default signatures: {e}")
    
    async def _cleanup_inactive_campaigns(self):
        """Background task to cleanup inactive campaigns."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                inactive_campaigns = []
                
                with self.campaigns_lock:
                    for campaign_id, campaign in self.active_campaigns.items():
                        if not campaign.is_active(timedelta(hours=2)):  # 2 hour timeout
                            inactive_campaigns.append(campaign_id)
                
                # Remove inactive campaigns
                for campaign_id in inactive_campaigns:
                    with self.campaigns_lock:
                        if campaign_id in self.active_campaigns:
                            campaign = self.active_campaigns.pop(campaign_id)
                            self.logger.info(
                                f"Archived inactive campaign: {campaign_id} "
                                f"(duration: {campaign.last_activity - campaign.start_time})"
                            )
                
            except Exception as e:
                self.logger.error(f"Campaign cleanup failed: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    # Helper methods for pattern detection
    def _has_sequential_usernames(self, emails: List[str]) -> bool:
        """Check for sequential username patterns."""
        # Implementation similar to AttackSignature._has_sequential_pattern
        return len(emails) >= 5 and any('test' in email.lower() for email in emails)
    
    def _has_dictionary_usernames(self, emails: List[str]) -> bool:
        """Check for dictionary-based username patterns."""
        common_words = ['admin', 'test', 'user', 'demo', 'guest', 'info', 'support', 'root']
        return any(any(word in email.lower() for word in common_words) for email in emails)
    
    def _has_common_domain_patterns(self, emails: List[str]) -> bool:
        """Check for common domain patterns in credential stuffing."""
        domains = [email.split('@')[1] if '@' in email else '' for email in emails]
        common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        
        domain_counts = Counter(domains)
        for domain in common_domains:
            if domain_counts.get(domain, 0) >= 5:
                return True
        
        return False
    
    def _has_leaked_credential_patterns(self, emails: List[str]) -> bool:
        """Check for patterns indicating use of leaked credentials."""
        # This would check against known breach databases
        # For now, implement basic heuristics
        
        # Check for old email formats that might be from breaches
        old_patterns = ['@aol.com', '@msn.com', '@live.com']
        return any(any(pattern in email for pattern in old_patterns) for email in emails)
    
    def _is_bot_user_agent(self, user_agent: str) -> bool:
        """Check if user agent indicates bot/automated tool."""
        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python', 'java', 'automated', 'script', 'tool'
        ]
        
        ua_lower = user_agent.lower()
        return any(indicator in ua_lower for indicator in bot_indicators)
    
    def _is_obvious_bot_user_agent(self, user_agent: str) -> bool:
        """Check for obviously bot-like user agents."""
        obvious_bots = [
            'python-requests', 'curl/', 'wget/', 'java/', 'go-http-client',
            'okhttp', 'apache-httpclient', 'urllib'
        ]
        
        return any(bot in user_agent.lower() for bot in obvious_bots)
    
    def _get_timezone_offset(self, timezone: str) -> int:
        """Get timezone offset in hours."""
        # Simplified timezone offset calculation
        timezone_offsets = {
            'UTC': 0, 'GMT': 0, 'EST': -5, 'PST': -8, 'CST': -6,
            'MST': -7, 'JST': 9, 'CET': 1, 'IST': 5.5
        }
        
        return timezone_offsets.get(timezone, 0)
    
    def _get_device_type(self, user_agent: str) -> str:
        """Extract device type from user agent."""
        ua_lower = user_agent.lower()
        
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            return 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            return 'tablet'
        elif 'windows' in ua_lower or 'macintosh' in ua_lower or 'linux' in ua_lower:
            return 'desktop'
        else:
            return 'unknown'
    
    def _is_known_bad_ip(self, ip: str) -> bool:
        """Check if IP is in known bad IP ranges."""
        # This would integrate with threat intelligence feeds
        # For now, implement basic checks
        
        # Check for obvious bad ranges (example)
        bad_ranges = ['10.0.0.', '192.168.', '127.0.0.']  # These are actually private ranges
        
        # In practice, this would check against real threat intelligence
        return False  # Placeholder
    
    def _is_high_value_target(self, email: str) -> bool:
        """Check if email represents a high-value target."""
        # Check for admin/privileged accounts
        privileged_indicators = ['admin', 'root', 'administrator', 'superuser', 'sysadmin']
        
        email_lower = email.lower()
        return any(indicator in email_lower for indicator in privileged_indicators)
    
    def _is_internal_ip(self, ip: str) -> bool:
        """Check if IP is from internal network."""
        # Check for private IP ranges
        private_ranges = ['10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                         '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                         '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.']
        
        return any(ip.startswith(range_prefix) for range_prefix in private_ranges)
    
    def _create_fallback_threat_analysis(self, context: AuthContext, start_time: float) -> ThreatAnalysis:
        """Create fallback threat analysis when detection fails."""
        processing_time = time.time() - start_time
        
        return ThreatAnalysis(
            ip_reputation_score=0.0,
            known_attack_patterns=[],
            threat_actor_indicators=[],
            brute_force_indicators=BruteForceIndicators(),
            credential_stuffing_indicators=CredentialStuffingIndicators(),
            account_takeover_indicators=AccountTakeoverIndicators(),
            similar_attacks_detected=0,
            attack_campaign_correlation=None
        )
    
    def _create_test_auth_context(self) -> AuthContext:
        """Create test authentication context for health checks."""
        from ai_karen_engine.security.models import GeoLocation
        
        return AuthContext(
            email="test@example.com",
            password_hash="test_hash",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0 (Test)",
            timestamp=datetime.now(),
            request_id="test_request",
            geolocation=GeoLocation(
                country="US",
                region="CA",
                city="San Francisco",
                latitude=37.7749,
                longitude=-122.4194,
                timezone="PST",
                is_usual_location=True
            )
        )
    
    async def _load_attack_signatures(self):
        """Load persisted attack signatures."""
        # Placeholder for loading signatures from storage
        pass
    
    async def _save_attack_signatures(self):
        """Save attack signatures to storage."""
        # Placeholdesaving signatures to storage
        pass
    
    async def _load_active_campaigns(self):
        """Load active campaigns from storage."""
        # Placeholder for loading campaigns from storage
        pass
    
    async def _save_active_campaigns(self):
        """Save active campaigns to storage."""
        # Placeholder for saving campaigns to storage
        pass
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service metrics for monitoring."""
        avg_processing_time = (
            statistics.mean(self._processing_times) if self._processing_times else 0.0
        )
        
        return {
            'pattern_detections': self._pattern_detections,
            'campaign_detections': self._campaign_detections,
            'brute_force_detections': self._brute_force_detections,
            'credential_stuffing_detections': self._credential_stuffing_detections,
            'account_takeover_detections': self._account_takeover_detections,
            'avg_processing_time': avg_processing_time,
            'active_campaigns': len(self.active_campaigns),
            'attack_signatures': len(self.attack_signatures),
            'recent_attempts_buffer': len(self.recent_attempts)
        }
    
    def get_active_campaigns_summary(self) -> List[Dict[str, Any]]:
        """Get summary of active attack campaigns."""
        summaries = []
        
        with self.campaigns_lock:
            for campaign in self.active_campaigns.values():
                summaries.append(campaign.get_campaign_summary())
        
        return summari