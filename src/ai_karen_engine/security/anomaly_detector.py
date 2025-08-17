"""
Core anomaly detection service for intelligent authentication system.

This module provides comprehensive anomaly detection using multi-dimensional
risk scoring that combines NLP features, embeddings, and behavioral patterns
with configurable thresholds and adaptive adjustment capabilities.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
import math
import statistics
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from cachetools import TTLCache
import threading

from ai_karen_engine.security.models import (
    AuthContext,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    RiskLevel,
    RiskThresholds,
    IntelligentAuthConfig,
    SecurityAction,
    SecurityActionType
)
from ai_karen_engine.security.intelligent_auth_base import (
    BaseIntelligentAuthService,
    AnomalyDetectorInterface,
    ServiceHealthStatus,
    ServiceStatus
)
from ai_karen_engine.security.adaptive_learning import (
    AdaptiveLearningEngine,
    AuthFeedback,
    LearningConfig
)

logger = logging.getLogger(__name__)


@dataclass
class RiskFactors:
    """Individual risk factors contributing to overall risk score."""
    
    nlp_risk: float = 0.0
    embedding_risk: float = 0.0
    behavioral_risk: float = 0.0
    temporal_risk: float = 0.0
    geolocation_risk: float = 0.0
    device_risk: float = 0.0
    threat_intel_risk: float = 0.0
    frequency_risk: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for logging and analysis."""
        return {
            'nlp_risk': self.nlp_risk,
            'embedding_risk': self.embedding_risk,
            'behavioral_risk': self.behavioral_risk,
            'temporal_risk': self.temporal_risk,
            'geolocation_risk': self.geolocation_risk,
            'device_risk': self.device_risk,
            'threat_intel_risk': self.threat_intel_risk,
            'frequency_risk': self.frequency_risk
        }


@dataclass
class UserRiskProfile:
    """User-specific risk profile for adaptive thresholds."""
    
    user_id: str
    baseline_risk: float = 0.5
    risk_history: List[float] = field(default_factory=list)
    false_positive_count: int = 0
    false_negative_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    adaptive_thresholds: Optional[RiskThresholds] = None
    
    def update_risk_history(self, risk_score: float, max_history: int = 100):
        """Update risk history with new score."""
        self.risk_history.append(risk_score)
        if len(self.risk_history) > max_history:
            self.risk_history = self.risk_history[-max_history:]
        
        # Update baseline risk as moving average
        if len(self.risk_history) >= 10:
            self.baseline_risk = statistics.mean(self.risk_history[-20:])
        
        self.last_updated = datetime.now()

class AnomalyDetector(BaseIntelligentAuthService, AnomalyDetectorInterface):
    """
    Comprehensive anomaly detection service that combines multiple ML techniques
    for multi-dimensional risk assessment with adaptive learning capabilities.
    """
    
    def __init__(self, config: IntelligentAuthConfig, learning_config: Optional[LearningConfig] = None):
        super().__init__(config)
        
        # Risk calculation weights (configurable)
        self.risk_weights = {
            'nlp_weight': 0.15,
            'embedding_weight': 0.25,
            'behavioral_weight': 0.20,
            'temporal_weight': 0.10,
            'geolocation_weight': 0.10,
            'device_weight': 0.10,
            'threat_intel_weight': 0.10
        }
        
        # Initialize adaptive learning engine
        self.adaptive_learning_engine = AdaptiveLearningEngine(config, learning_config)
        
        # User risk profiles for adaptive thresholds (legacy - now handled by adaptive learning engine)
        self.user_risk_profiles: Dict[str, UserRiskProfile] = {}
        self.profiles_lock = threading.RLock()
        
        # Caching for risk calculations
        self.risk_cache = TTLCache(
            maxsize=config.cache_size,
            ttl=config.cache_ttl // 2  # Shorter TTL for risk calculations
        )
        self.cache_lock = threading.RLock()
        
        # Recent authentication attempts for pattern analysis
        self.recent_attempts: deque = deque(maxlen=10000)
        self.attempts_lock = threading.RLock()
        
        # Metrics tracking
        self._detection_count = 0
        self._high_risk_detections = 0
        self._false_positive_feedback = 0
        self._false_negative_feedback = 0
        self._processing_times = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Model version for tracking
        self.model_version = "anomaly_detector_v1.0"
        
        self.logger.info("AnomalyDetector initialized")
    
    async def initialize(self) -> bool:
        """Initialize the anomaly detection service."""
        try:
            # Initialize adaptive learning engine
            await self.adaptive_learning_engine.initialize()
            
            # Load any persisted user risk profiles
            await self._load_user_risk_profiles()
            
            # Initialize risk calculation components
            self._initialize_risk_calculators()
            
            self.logger.info("AnomalyDetector initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AnomalyDetector: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""
        try:
            # Shutdown adaptive learning engine
            await self.adaptive_learning_engine.shutdown()
            
            # Save user risk profiles
            await self._save_user_risk_profiles()
            
            # Clear caches
            with self.cache_lock:
                self.risk_cache.clear()
            
            with self.attempts_lock:
                self.recent_attempts.clear()
            
            self.logger.info("AnomalyDetector shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during AnomalyDetector shutdown: {e}")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check for the anomaly detector."""
        try:
            # Test basic risk calculation
            test_context = self._create_test_auth_context()
            test_nlp = self._create_test_nlp_features()
            test_embedding = self._create_test_embedding_analysis()
            
            # Perform test detection
            result = await self.detect_anomalies(test_context, test_nlp, test_embedding)
            
            return (
                result is not None and
                hasattr(result, 'time_deviation_score') and
                0.0 <= result.time_deviation_score <= 1.0
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False    
    
    async def detect_anomalies(
            self,
            context: AuthContext,
            nlp_features: NLPFeatures,
            embedding_analysis: EmbeddingAnalysis
        ) -> BehavioralAnalysis:
            """
            Detect behavioral anomalies in authentication attempt.
            
            Args:
                context: Authentication context
                nlp_features: NLP analysis features
                embedding_analysis: Embedding analysis results
                
            Returns:
                BehavioralAnalysis with anomaly detection results
            """
            start_time = time.time()
            
            try:
                # Store attempt for pattern analysis
                with self.attempts_lock:
                    self.recent_attempts.append({
                        'context': context,
                        'timestamp': datetime.now(),
                        'email': context.email,
                        'ip': context.client_ip
                    })
                
                # Calculate individual risk factors
                risk_factors = await self._calculate_risk_factors(
                    context, nlp_features, embedding_analysis
                )
                
                # Calculate overall risk score
                overall_risk_score = self._calculate_overall_risk_score(risk_factors)
                
                # Generate behavioral analysis
                behavioral_analysis = self._create_behavioral_analysis(
                    context, risk_factors, overall_risk_score
                )
                
                # Update user risk profile
                await self._update_user_risk_profile(context.email, overall_risk_score)
                
                processing_time = time.time() - start_time
                
                # Update metrics
                self._detection_count += 1
                self._processing_times.append(processing_time)
                if len(self._processing_times) > 1000:
                    self._processing_times = self._processing_times[-1000:]
                
                if overall_risk_score > self.config.risk_thresholds.high_risk_threshold:
                    self._high_risk_detections += 1
                
                self.logger.debug(
                    f"Anomaly detection completed for {context.email}: "
                    f"risk={overall_risk_score:.3f}, time={processing_time:.3f}s"
                )
                
                return behavioral_analysis
                
            except Exception as e:
                self.logger.error(f"Anomaly detection failed: {e}")
                # Return fallback behavioral analysis
                return self._create_fallback_behavioral_analysis(context, start_time)
    
    async def calculate_risk_score(
        self,
        context: AuthContext,
        nlp_features: NLPFeatures,
        embedding_analysis: EmbeddingAnalysis,
        behavioral_analysis: BehavioralAnalysis
    ) -> float:
        """
        Calculate overall risk score for authentication attempt.
        
        Args:
            context: Authentication context
            nlp_features: NLP analysis features
            embedding_analysis: Embedding analysis results
            behavioral_analysis: Behavioral analysis results
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        try:
            # Check cache first
            cache_key = self._get_risk_cache_key(context, nlp_features, embedding_analysis)
            with self.cache_lock:
                if cache_key in self.risk_cache:
                    self._cache_hits += 1
                    return self.risk_cache[cache_key]
                self._cache_misses += 1
            
            # Calculate risk factors
            risk_factors = await self._calculate_risk_factors(
                context, nlp_features, embedding_analysis
            )
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(risk_factors)
            
            # Apply user-specific adjustments
            adjusted_risk_score = await self._apply_user_specific_adjustments(
                context.email, overall_risk_score
            )
            
            # Cache the result
            with self.cache_lock:
                self.risk_cache[cache_key] = adjusted_risk_score
            
            return adjusted_risk_score
            
        except Exception as e:
            self.logger.error(f"Risk score calculation failed: {e}")
            return self.config.fallback_config.fallback_risk_score
    
    async def learn_from_feedback(
        self,
        user_id: str,
        context: AuthContext,
        feedback: Dict[str, Any]
    ) -> None:
        """
        Learn from authentication feedback to improve detection.
        
        Args:
            user_id: User identifier
            context: Authentication context
            feedback: Feedback data including correctness of detection
        """
        try:
            # Create AuthFeedback object for the adaptive learning engine
            auth_feedback = AuthFeedback(
                user_id=user_id,
                request_id=context.request_id,
                timestamp=context.timestamp,
                original_risk_score=feedback.get('original_risk_score', 0.5),
                original_decision=feedback.get('original_decision', 'allow'),
                is_false_positive=feedback.get('false_positive', False),
                is_false_negative=feedback.get('false_negative', False),
                is_correct=feedback.get('is_correct', True),
                actual_outcome=feedback.get('actual_outcome'),
                user_reported=feedback.get('user_reported', False),
                admin_verified=feedback.get('admin_verified', False),
                confidence=feedback.get('confidence', 1.0),
                feedback_source=feedback.get('feedback_source', 'system'),
                notes=feedback.get('notes')
            )
            
            # Process feedback through adaptive learning engine
            await self.adaptive_learning_engine.process_feedback(auth_feedback)
            
            # Update behavioral model
            await self.adaptive_learning_engine.update_user_behavioral_model(
                user_id, context, not auth_feedback.is_false_positive
            )
            
            # Legacy processing for backward compatibility
            feedback_type = feedback.get('type', 'unknown')
            is_false_positive = feedback.get('false_positive', False)
            is_false_negative = feedback.get('false_negative', False)
            actual_risk = feedback.get('actual_risk_score')
            
            with self.profiles_lock:
                if user_id not in self.user_risk_profiles:
                    self.user_risk_profiles[user_id] = UserRiskProfile(user_id=user_id)
                
                profile = self.user_risk_profiles[user_id]
                
                # Update false positive/negative counts
                if is_false_positive:
                    profile.false_positive_count += 1
                    self._false_positive_feedback += 1
                    
                    # Adjust thresholds to be less sensitive
                    await self._adjust_user_thresholds(user_id, increase_threshold=True)
                
                if is_false_negative:
                    profile.false_negative_count += 1
                    self._false_negative_feedback += 1
                    
                    # Adjust thresholds to be more sensitive
                    await self._adjust_user_thresholds(user_id, increase_threshold=False)
                
                # Update risk history if actual risk provided
                if actual_risk is not None:
                    profile.update_risk_history(actual_risk)
            
            self.logger.info(
                f"Processed feedback for user {user_id}: "
                f"type={feedback_type}, fp={is_false_positive}, fn={is_false_negative}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process feedback: {e}")    
    
    async def _calculate_risk_factors(
            self,
            context: AuthContext,
            nlp_features: NLPFeatures,
            embedding_analysis: EmbeddingAnalysis
        ) -> RiskFactors:
            """Calculate individual risk factors from different analysis components."""
            risk_factors = RiskFactors()
            
            try:
                # NLP-based risk factors
                risk_factors.nlp_risk = self._calculate_nlp_risk(nlp_features)
                
                # Embedding-based risk factors
                risk_factors.embedding_risk = self._calculate_embedding_risk(embedding_analysis)
                
                # Temporal risk factors
                risk_factors.temporal_risk = self._calculate_temporal_risk(context)
                
                # Geolocation risk factors
                risk_factors.geolocation_risk = self._calculate_geolocation_risk(context)
                
                # Device risk factors
                risk_factors.device_risk = self._calculate_device_risk(context)
                
                # Threat intelligence risk factors
                risk_factors.threat_intel_risk = context.threat_intel_score
                
                # Frequency-based risk factors
                risk_factors.frequency_risk = await self._calculate_frequency_risk(context)
                
            except Exception as e:
                self.logger.error(f"Risk factor calculation failed: {e}")
            
            return risk_factors
    
    def _calculate_nlp_risk(self, nlp_features: NLPFeatures) -> float:
        """Calculate risk score based on NLP features."""
        risk_score = 0.0
        
        try:
            # Risk from suspicious patterns
            if nlp_features.suspicious_patterns:
                pattern_risk = min(len(nlp_features.suspicious_patterns) * 0.2, 1.0)
                risk_score += pattern_risk * 0.4
            
            # Risk from credential similarity
            if nlp_features.credential_similarity > 0.7:
                similarity_risk = (nlp_features.credential_similarity - 0.7) / 0.3
                risk_score += similarity_risk * 0.3
            
            # Risk from language inconsistency
            if not nlp_features.language_consistency:
                risk_score += 0.2
            
            # Risk from email features
            email_entropy = nlp_features.email_features.entropy_score
            if email_entropy < 2.0:  # Low entropy indicates predictable patterns
                entropy_risk = (2.0 - email_entropy) / 2.0
                risk_score += entropy_risk * 0.1
            
            # Risk from password features (limited due to hashing)
            if nlp_features.password_features.contains_suspicious_patterns:
                risk_score += 0.3
            
        except Exception as e:
            self.logger.error(f"NLP risk calculation failed: {e}")
        
        return min(risk_score, 1.0)
    
    def _calculate_embedding_risk(self, embedding_analysis: EmbeddingAnalysis) -> float:
        """Calculate risk score based on embedding analysis."""
        risk_score = 0.0
        
        try:
            # Risk from low similarity to user profile
            if embedding_analysis.similarity_to_user_profile < 0.5:
                profile_risk = (0.5 - embedding_analysis.similarity_to_user_profile) / 0.5
                risk_score += profile_risk * 0.5
            
            # Risk from high similarity to attack patterns
            attack_similarity_risk = embedding_analysis.similarity_to_attack_patterns
            risk_score += attack_similarity_risk * 0.3
            
            # Risk from outlier score
            outlier_risk = embedding_analysis.outlier_score
            risk_score += outlier_risk * 0.2
            
        except Exception as e:
            self.logger.error(f"Embedding risk calculation failed: {e}")
        
        return min(risk_score, 1.0)
    
    def _calculate_temporal_risk(self, context: AuthContext) -> float:
        """Calculate risk score based on temporal patterns."""
        risk_score = 0.0
        
        try:
            current_hour = context.timestamp.hour
            
            # Risk from unusual login times (night hours)
            if current_hour < 6 or current_hour > 22:
                risk_score += 0.3
            
            # Risk from weekend logins (if not typical)
            if context.timestamp.weekday() >= 5:  # Weekend
                risk_score += 0.1
            
            # Risk from time since last login
            if context.time_since_last_login:
                hours_since_last = context.time_since_last_login.total_seconds() / 3600
                
                # Very quick successive logins (< 1 minute)
                if hours_since_last < 1/60:
                    risk_score += 0.4
                # Very long time since last login (> 30 days)
                elif hours_since_last > 24 * 30:
                    risk_score += 0.2
            
        except Exception as e:
            self.logger.error(f"Temporal risk calculation failed: {e}")
        
        return min(risk_score, 1.0)
    
    def _calculate_geolocation_risk(self, context: AuthContext) -> float:
        """Calculate risk score based on geolocation patterns."""
        risk_score = 0.0
        
        try:
            if not context.geolocation:
                return 0.1  # Small risk for missing geolocation
            
            # Risk from unusual location
            if not context.geolocation.is_usual_location:
                risk_score += 0.5
            
        except Exception as e:
            self.logger.error(f"Geolocation risk calculation failed: {e}")
        
        return min(risk_score, 1.0)
    
    def _calculate_device_risk(self, context: AuthContext) -> float:
        """Calculate risk score based on device patterns."""
        risk_score = 0.0
        
        try:
            # Risk from Tor usage
            if context.is_tor_exit_node:
                risk_score += 0.6
            
            # Risk from VPN usage
            if context.is_vpn:
                risk_score += 0.3
            
            # Risk from missing device fingerprint
            if not context.device_fingerprint:
                risk_score += 0.1
            
            # Risk from unusual user agent patterns
            if self._is_unusual_user_agent(context.user_agent):
                risk_score += 0.2
            
        except Exception as e:
            self.logger.error(f"Device risk calculation failed: {e}")
        
        return min(risk_score, 1.0)    

    async def _calculate_frequency_risk(self, context: AuthContext) -> float:
        """Calculate risk score based on login frequency patterns."""
        risk_score = 0.0
        
        try:
            # Count recent attempts from same IP
            recent_ip_attempts = 0
            recent_user_attempts = 0
            
            cutoff_time = datetime.now() - timedelta(minutes=15)
            
            with self.attempts_lock:
                for attempt in self.recent_attempts:
                    if attempt['timestamp'] > cutoff_time:
                        if attempt['ip'] == context.client_ip:
                            recent_ip_attempts += 1
                        if attempt['email'] == context.email:
                            recent_user_attempts += 1
            
            # Risk from too many attempts from same IP
            if recent_ip_attempts > 10:
                ip_risk = min((recent_ip_attempts - 10) / 20, 1.0)
                risk_score += ip_risk * 0.6
            
            # Risk from too many attempts for same user
            if recent_user_attempts > 5:
                user_risk = min((recent_user_attempts - 5) / 10, 1.0)
                risk_score += user_risk * 0.4
            
            # Risk from previous failed attempts
            if context.previous_failed_attempts > 0:
                failed_risk = min(context.previous_failed_attempts / 10, 1.0)
                risk_score += failed_risk * 0.3
            
        except Exception as e:
            self.logger.error(f"Frequency risk calculation failed: {e}")
        
        return min(risk_score, 1.0)
    
    def _calculate_overall_risk_score(self, risk_factors: RiskFactors) -> float:
        """Calculate weighted overall risk score from individual factors."""
        try:
            weighted_score = (
                risk_factors.nlp_risk * self.risk_weights['nlp_weight'] +
                risk_factors.embedding_risk * self.risk_weights['embedding_weight'] +
                risk_factors.behavioral_risk * self.risk_weights['behavioral_weight'] +
                risk_factors.temporal_risk * self.risk_weights['temporal_weight'] +
                risk_factors.geolocation_risk * self.risk_weights['geolocation_weight'] +
                risk_factors.device_risk * self.risk_weights['device_weight'] +
                risk_factors.threat_intel_risk * self.risk_weights['threat_intel_weight']
            )
            
            # Apply frequency risk as a multiplier for high-frequency scenarios
            if risk_factors.frequency_risk > 0.5:
                frequency_multiplier = 1.0 + (risk_factors.frequency_risk - 0.5)
                weighted_score *= frequency_multiplier
            
            return min(weighted_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Overall risk score calculation failed: {e}")
            return 0.5  # Default moderate risk
    
    def _create_behavioral_analysis(
        self,
        context: AuthContext,
        risk_factors: RiskFactors,
        overall_risk_score: float
    ) -> BehavioralAnalysis:
        """Create BehavioralAnalysis from risk assessment results."""
        try:
            # Determine if patterns are usual based on risk scores
            is_usual_time = risk_factors.temporal_risk < 0.3
            is_usual_location = risk_factors.geolocation_risk < 0.3
            is_known_device = risk_factors.device_risk < 0.3
            
            # Calculate deviation scores
            time_deviation_score = risk_factors.temporal_risk
            location_deviation_score = risk_factors.geolocation_risk
            device_similarity_score = 1.0 - risk_factors.device_risk
            
            # Calculate anomaly scores
            login_frequency_anomaly = risk_factors.frequency_risk
            session_duration_anomaly = 0.0  # Would need session data
            
            # Calculate success rate (placeholder - would need historical data)
            success_rate_last_30_days = 0.95  # Default assumption
            
            # Create failed attempts pattern
            failed_attempts_pattern = {
                'recent_failures': context.previous_failed_attempts,
                'failure_rate': min(context.previous_failed_attempts / 10, 1.0),
                'last_failure_time': context.timestamp.isoformat() if context.previous_failed_attempts > 0 else None
            }
            
            return BehavioralAnalysis(
                is_usual_time=is_usual_time,
                time_deviation_score=time_deviation_score,
                is_usual_location=is_usual_location,
                location_deviation_score=location_deviation_score,
                is_known_device=is_known_device,
                device_similarity_score=device_similarity_score,
                login_frequency_anomaly=login_frequency_anomaly,
                session_duration_anomaly=session_duration_anomaly,
                success_rate_last_30_days=success_rate_last_30_days,
                failed_attempts_pattern=failed_attempts_pattern
            )
            
        except Exception as e:
            self.logger.error(f"Behavioral analysis creation failed: {e}")
            return self._create_default_behavioral_analysis()
    
    async def _update_user_risk_profile(self, user_email: str, risk_score: float) -> None:
        """Update user's risk profile with new risk score."""
        try:
            with self.profiles_lock:
                if user_email not in self.user_risk_profiles:
                    self.user_risk_profiles[user_email] = UserRiskProfile(user_id=user_email)
                
                profile = self.user_risk_profiles[user_email]
                profile.update_risk_history(risk_score)
                
        except Exception as e:
            self.logger.error(f"User risk profile update failed: {e}")
    
    async def _apply_user_specific_adjustments(self, user_email: str, risk_score: float) -> float:
        """Apply user-specific adjustments to risk score."""
        try:
            # Use adaptive learning engine for primary adjustments
            adaptive_thresholds = await self.adaptive_learning_engine.get_adaptive_thresholds(user_email)
            
            # Apply threshold-based adjustments
            if adaptive_thresholds != self.config.risk_thresholds:
                # User has custom thresholds, apply adjustment based on difference
                default_high = self.config.risk_thresholds.high_risk_threshold
                adaptive_high = adaptive_thresholds.high_risk_threshold
                
                # Adjust risk score based on threshold difference
                threshold_adjustment = (adaptive_high - default_high) * 0.5
                risk_score = max(0.0, min(1.0, risk_score - threshold_adjustment))
            
            # Legacy adjustments for backward compatibility
            with self.profiles_lock:
                if user_email not in self.user_risk_profiles:
                    return risk_score
                
                profile = self.user_risk_profiles[user_email]
                
                # Adjust based on false positive history
                if profile.false_positive_count > 5:
                    # Reduce sensitivity for users with many false positives
                    fp_adjustment = min(profile.false_positive_count / 50, 0.2)
                    risk_score = max(0.0, risk_score - fp_adjustment)
                
                # Adjust based on false negative history
                if profile.false_negative_count > 2:
                    # Increase sensitivity for users with false negatives
                    fn_adjustment = min(profile.false_negative_count / 20, 0.1)
                    risk_score = min(1.0, risk_score + fn_adjustment)
                
                return risk_score
                
        except Exception as e:
            self.logger.error(f"User-specific adjustment failed: {e}")
            return risk_score 
   
    async def _adjust_user_thresholds(self, user_id: str, increase_threshold: bool) -> None:
        """Adjust user-specific thresholds based on feedback."""
        try:
            with self.profiles_lock:
                if user_id not in self.user_risk_profiles:
                    return
                
                profile = self.user_risk_profiles[user_id]
                
                if not profile.adaptive_thresholds:
                    profile.adaptive_thresholds = RiskThresholds()
                
                adjustment = 0.05 if increase_threshold else -0.05
                
                # Adjust all thresholds
                profile.adaptive_thresholds.low_risk_threshold = max(
                    0.1, min(0.9, profile.adaptive_thresholds.low_risk_threshold + adjustment)
                )
                profile.adaptive_thresholds.medium_risk_threshold = max(
                    0.2, min(0.95, profile.adaptive_thresholds.medium_risk_threshold + adjustment)
                )
                profile.adaptive_thresholds.high_risk_threshold = max(
                    0.4, min(0.98, profile.adaptive_thresholds.high_risk_threshold + adjustment)
                )
                profile.adaptive_thresholds.critical_risk_threshold = max(
                    0.6, min(1.0, profile.adaptive_thresholds.critical_risk_threshold + adjustment)
                )
                
        except Exception as e:
            self.logger.error(f"Threshold adjustment failed: {e}")
    
    def _is_unusual_user_agent(self, user_agent: str) -> bool:
        """Check if user agent indicates unusual or suspicious client."""
        try:
            suspicious_patterns = [
                'bot', 'crawler', 'spider', 'scraper',
                'curl', 'wget', 'python', 'java',
                'automated', 'script'
            ]
            
            user_agent_lower = user_agent.lower()
            return any(pattern in user_agent_lower for pattern in suspicious_patterns)
            
        except Exception:
            return False
    
    def _get_risk_cache_key(
        self,
        context: AuthContext,
        nlp_features: NLPFeatures,
        embedding_analysis: EmbeddingAnalysis
    ) -> str:
        """Generate cache key for risk calculation."""
        import hashlib
        
        # Create hash from key components
        key_components = [
            context.email,
            context.client_ip,
            str(context.timestamp.hour),
            str(len(nlp_features.suspicious_patterns)),
            f"{embedding_analysis.similarity_to_user_profile:.2f}",
            f"{embedding_analysis.outlier_score:.2f}"
        ]
        
        key_string = ":".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _load_user_risk_profiles(self) -> None:
        """Load user risk profiles from persistent storage."""
        # Placeholder for loading from database or file
        self.logger.debug("User risk profiles loading skipped (no persistent storage configured)")
    
    async def _save_user_risk_profiles(self) -> None:
        """Save user risk profiles to persistent storage."""
        # Placeholder for saving to database or file
        self.logger.debug("User risk profiles saving skipped (no persistent storage configured)")
    
    def _initialize_risk_calculators(self) -> None:
        """Initialize risk calculation components."""
        # Initialize any additional risk calculation components
        self.logger.debug("Risk calculators initialized")
    
    def _create_test_auth_context(self) -> AuthContext:
        """Create test authentication context for health checks."""
        return AuthContext(
            email="test@example.com",
            password_hash="test_hash",
            client_ip="127.0.0.1",
            user_agent="test_agent",
            timestamp=datetime.now(),
            request_id="test_request"
        )
    
    def _create_test_nlp_features(self) -> NLPFeatures:
        """Create test NLP features for health checks."""
        from ai_karen_engine.security.models import CredentialFeatures
        
        email_features = CredentialFeatures(
            token_count=2,
            unique_token_ratio=1.0,
            entropy_score=3.0,
            language="en",
            contains_suspicious_patterns=False
        )
        
        password_features = CredentialFeatures(
            token_count=1,
            unique_token_ratio=1.0,
            entropy_score=4.0,
            language="unknown",
            contains_suspicious_patterns=False
        )
        
        return NLPFeatures(
            email_features=email_features,
            password_features=password_features,
            credential_similarity=0.0,
            language_consistency=True
        )
    
    def _create_test_embedding_analysis(self) -> EmbeddingAnalysis:
        """Create test embedding analysis for health checks."""
        return EmbeddingAnalysis(
            embedding_vector=[0.1] * 768,
            similarity_to_user_profile=0.8,
            similarity_to_attack_patterns=0.1,
            outlier_score=0.2
        )
    
    def _create_fallback_behavioral_analysis(self, context: AuthContext, start_time: float) -> BehavioralAnalysis:
        """Create fallback behavioral analysis when detection fails."""
        processing_time = time.time() - start_time
        
        return BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.0,
            is_usual_location=True,
            location_deviation_score=0.0,
            is_known_device=True,
            device_similarity_score=1.0,
            login_frequency_anomaly=0.0,
            session_duration_anomaly=0.0,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={}
        )
    
    def _create_default_behavioral_analysis(self) -> BehavioralAnalysis:
        """Create default behavioral analysis."""
        return BehavioralAnalysis(
            is_usual_time=True,
            time_deviation_score=0.0,
            is_usual_location=True,
            location_deviation_score=0.0,
            is_known_device=True,
            device_similarity_score=1.0,
            login_frequency_anomaly=0.0,
            session_duration_anomaly=0.0,
            success_rate_last_30_days=0.95,
            failed_attempts_pattern={}
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for the anomaly detector."""
        with self.cache_lock:
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0
            
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
        
        with self.profiles_lock:
            user_profiles_count = len(self.user_risk_profiles)
        
        with self.attempts_lock:
            recent_attempts_count = len(self.recent_attempts)
        
        return {
            'detection_count': self._detection_count,
            'high_risk_detections': self._high_risk_detections,
            'false_positive_feedback': self._false_positive_feedback,
            'false_negative_feedback': self._false_negative_feedback,
            'cache_hit_rate': cache_hit_rate,
            'avg_processing_time': avg_processing_time,
            'user_profiles_count': user_profiles_count,
            'recent_attempts_count': recent_attempts_count,
            'model_version': self.model_version
        }   
 
    def _determine_risk_level(self, user_email: str, risk_score: float) -> RiskLevel:
        """Determine risk level based on score and user-specific thresholds."""
        try:
            # Get user-specific thresholds if available
            thresholds = self.config.risk_thresholds
            
            with self.profiles_lock:
                if user_email in self.user_risk_profiles:
                    profile = self.user_risk_profiles[user_email]
                    if profile.adaptive_thresholds:
                        thresholds = profile.adaptive_thresholds
            
            # Determine risk level
            if risk_score >= thresholds.critical_risk_threshold:
                return RiskLevel.CRITICAL
            elif risk_score >= thresholds.high_risk_threshold:
                return RiskLevel.HIGH
            elif risk_score >= thresholds.medium_risk_threshold:
                return RiskLevel.MEDIUM
            elif risk_score >= thresholds.low_risk_threshold:
                return RiskLevel.LOW
            else:
                return RiskLevel.LOW  # Below all thresholds
                
        except Exception as e:
            self.logger.error(f"Risk level determination failed: {e}")
            return RiskLevel.MEDIUM  # Default to medium risk
    
    def _calculate_confidence_score(self, risk_factors: RiskFactors) -> float:
        """Calculate confidence score for the risk assessment."""
        try:
            # Confidence based on number of contributing factors
            factor_values = [
                risk_factors.nlp_risk,
                risk_factors.embedding_risk,
                risk_factors.behavioral_risk,
                risk_factors.temporal_risk,
                risk_factors.geolocation_risk,
                risk_factors.device_risk,
                risk_factors.threat_intel_risk,
                risk_factors.frequency_risk
            ]
            
            # Count significant factors (> 0.1)
            significant_factors = sum(1 for factor in factor_values if factor > 0.1)
            
            # Base confidence on number of factors
            base_confidence = min(significant_factors / 8.0, 1.0)
            
            # Adjust based on factor variance (more consistent = higher confidence)
            if significant_factors > 1:
                factor_variance = statistics.variance([f for f in factor_values if f > 0.1])
                variance_adjustment = max(0.0, 1.0 - factor_variance)
                base_confidence *= (0.7 + 0.3 * variance_adjustment)
            
            return max(0.1, min(base_confidence, 1.0))
            
        except Exception as e:
            self.logger.error(f"Confidence score calculation failed: {e}")
            return 0.5  # Default moderate confidence
    
    async def _update_adaptive_thresholds(self, user_email: str, profile: UserRiskProfile) -> None:
        """Update adaptive thresholds based on user's risk history."""
        try:
            if len(profile.risk_history) < 10:
                return  # Need sufficient history
            
            # Calculate user-specific thresholds based on risk history
            risk_mean = statistics.mean(profile.risk_history)
            risk_std = statistics.stdev(profile.risk_history) if len(profile.risk_history) > 1 else 0.1
            
            # Adjust thresholds based on user's typical risk pattern
            base_thresholds = self.config.risk_thresholds
            
            # Create adaptive thresholds
            adaptive_thresholds = RiskThresholds(
                low_risk_threshold=max(0.1, risk_mean - risk_std),
                medium_risk_threshold=max(0.3, risk_mean),
                high_risk_threshold=max(0.6, risk_mean + risk_std),
                critical_risk_threshold=max(0.8, risk_mean + 2 * risk_std),
                enable_adaptive_thresholds=True,
                user_specific_thresholds=True,
                time_based_adjustments=base_thresholds.time_based_adjustments
            )
            
            # Ensure thresholds are in ascending order
            thresholds = [
                adaptive_thresholds.low_risk_threshold,
                adaptive_thresholds.medium_risk_threshold,
                adaptive_thresholds.high_risk_threshold,
                adaptive_thresholds.critical_risk_threshold
            ]
            
            if thresholds == sorted(thresholds):
                profile.adaptive_thresholds = adaptive_thresholds
                self.logger.debug(f"Updated adaptive thresholds for user {user_email}")
            
        except Exception as e:
            self.logger.error(f"Adaptive threshold update failed: {e}")