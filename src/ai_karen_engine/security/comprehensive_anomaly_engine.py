"""
Comprehensive anomaly detection engine that integrates all ML components.

This module provides a unified interface for multi-dimensional anomaly detection
that combines NLP features, embeddings, behavioral patterns, attack pattern detection,
and adaptive learning with configurable thresholds and threat correlation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ai_karen_engine.security.models import (
    AuthContext,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis,
    AuthAnalysisResult,
    RiskLevel,
    RiskThresholds,
    IntelligentAuthConfig,
    SecurityAction,
    SecurityActionType
)
from ai_karen_engine.security.intelligent_auth_base import (
    BaseIntelligentAuthService,
    ServiceHealthStatus,
    ServiceStatus
)
from ai_karen_engine.security.anomaly_detector import AnomalyDetector
from ai_karen_engine.security.attack_pattern_detector import AttackPatternDetector
from ai_karen_engine.security.adaptive_learning import (
    AdaptiveLearningEngine,
    AuthFeedback,
    LearningConfig
)

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveAnalysisResult:
    """Comprehensive analysis result combining all detection components."""
    
    # Core analysis results
    behavioral_analysis: BehavioralAnalysis
    threat_analysis: ThreatAnalysis
    overall_risk_score: float
    risk_level: RiskLevel
    
    # Processing metadata
    processing_time: float
    components_used: List[str]
    confidence_score: float
    
    # Recommendations
    recommended_actions: List[SecurityAction]
    should_block: bool
    requires_2fa: bool
    
    # Correlation data
    attack_correlation_score: float
    behavioral_anomaly_score: float
    threat_intelligence_score: float


class ComprehensiveAnomalyEngine(BaseIntelligentAuthService):
    """
    Comprehensive anomaly detection engine that integrates behavioral anomaly detection,
    attack pattern detection, and adaptive learning for complete threat assessment.
    """
    
    def __init__(self, config: IntelligentAuthConfig, learning_config: Optional[LearningConfig] = None):
        super().__init__(config)
        
        # Initialize component services
        self.anomaly_detector = AnomalyDetector(config, learning_config)
        self.attack_pattern_detector = AttackPatternDetector(config)
        self.adaptive_learning_engine = AdaptiveLearningEngine(config, learning_config)
        
        # Integration weights for combining results
        self.component_weights = {
            'behavioral_weight': 0.4,
            'attack_pattern_weight': 0.4,
            'threat_intel_weight': 0.2
        }
        
        # Metrics tracking
        self._comprehensive_analyses = 0
        self._high_risk_detections = 0
        self._blocked_attempts = 0
        self._correlation_matches = 0
        self._processing_times = []
        
        self.model_version = "comprehensive_anomaly_engine_v1.0"
        
        self.logger.info("ComprehensiveAnomalyEngine initialized")
    
    async def initialize(self) -> bool:
        """Initialize all component services."""
        try:
            # Initialize all components
            anomaly_init = await self.anomaly_detector.initialize()
            attack_init = await self.attack_pattern_detector.initialize()
            learning_init = await self.adaptive_learning_engine.initialize()
            
            if not all([anomaly_init, attack_init, learning_init]):
                self.logger.error("Failed to initialize one or more components")
                return False
            
            self.logger.info("ComprehensiveAnomalyEngine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ComprehensiveAnomalyEngine: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all component services."""
        try:
            # Shutdown all components
            await self.anomaly_detector.shutdown()
            await self.attack_pattern_detector.shutdown()
            await self.adaptive_learning_engine.shutdown()
            
            self.logger.info("ComprehensiveAnomalyEngine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during ComprehensiveAnomalyEngine shutdown: {e}")
    
    async def _perform_health_check(self) -> bool:
        """Perform comprehensive health check of all components."""
        try:
            # Check health of all components
            anomaly_health = await self.anomaly_detector.health_check()
            attack_health = await self.attack_pattern_detector.health_check()
            learning_health = await self.adaptive_learning_engine.health_check()
            
            # All components should be healthy or degraded
            healthy_statuses = [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
            
            return (
                anomaly_health.status in healthy_statuses and
                attack_health.status in healthy_statuses and
                learning_health.status in healthy_statuses
            )
            
        except Exception as e:
            self.logger.error(f"Comprehensive health check failed: {e}")
            return False
    
    async def analyze_authentication_attempt(
        self,
        context: AuthContext,
        nlp_features: NLPFeatures,
        embedding_analysis: EmbeddingAnalysis
    ) -> ComprehensiveAnalysisResult:
        """
        Perform comprehensive analysis of authentication attempt using all components.
        
        Args:
            context: Authentication context
            nlp_features: NLP analysis features
            embedding_analysis: Embedding analysis results
            
        Returns:
            ComprehensiveAnalysisResult with integrated analysis
        """
        start_time = time.time()
        components_used = []
        
        try:
            # Perform behavioral anomaly detection
            behavioral_analysis = await self.anomaly_detector.detect_anomalies(
                context, nlp_features, embedding_analysis
            )
            components_used.append("behavioral_anomaly_detector")
            
            # Perform attack pattern detection
            threat_analysis = await self.attack_pattern_detector.detect_attack_patterns(context)
            components_used.append("attack_pattern_detector")
            
            # Calculate individual risk scores
            behavioral_risk_score = await self.anomaly_detector.calculate_risk_score(
                context, nlp_features, embedding_analysis, behavioral_analysis
            )
            
            # Calculate attack pattern risk score
            attack_risk_score = self._calculate_attack_pattern_risk_score(threat_analysis)
            
            # Get adaptive thresholds
            adaptive_thresholds = await self.adaptive_learning_engine.get_adaptive_thresholds(
                context.email
            )
            
            # Combine risk scores using weighted approach
            overall_risk_score = self._calculate_comprehensive_risk_score(
                behavioral_risk_score, attack_risk_score, threat_analysis.ip_reputation_score
            )
            
            # Determine risk level using adaptive thresholds
            risk_level = self._determine_risk_level(overall_risk_score, adaptive_thresholds)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                behavioral_analysis, threat_analysis, overall_risk_score
            )
            
            # Generate security recommendations
            recommended_actions = self._generate_security_recommendations(
                overall_risk_score, risk_level, behavioral_analysis, threat_analysis
            )
            
            # Determine blocking decision
            should_block = overall_risk_score >= adaptive_thresholds.high_risk_threshold
            requires_2fa = (
                overall_risk_score >= adaptive_thresholds.medium_risk_threshold and
                not should_block
            )
            
            # Calculate correlation scores
            attack_correlation_score = self._calculate_attack_correlation_score(threat_analysis)
            behavioral_anomaly_score = behavioral_risk_score
            threat_intelligence_score = threat_analysis.ip_reputation_score
            
            processing_time = time.time() - start_time
            
            # Create comprehensive result
            result = ComprehensiveAnalysisResult(
                behavioral_analysis=behavioral_analysis,
                threat_analysis=threat_analysis,
                overall_risk_score=overall_risk_score,
                risk_level=risk_level,
                processing_time=processing_time,
                components_used=components_used,
                confidence_score=confidence_score,
                recommended_actions=recommended_actions,
                should_block=should_block,
                requires_2fa=requires_2fa,
                attack_correlation_score=attack_correlation_score,
                behavioral_anomaly_score=behavioral_anomaly_score,
                threat_intelligence_score=threat_intelligence_score
            )
            
            # Update metrics
            self._comprehensive_analyses += 1
            self._processing_times.append(processing_time)
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]
            
            if overall_risk_score >= adaptive_thresholds.high_risk_threshold:
                self._high_risk_detections += 1
            
            if should_block:
                self._blocked_attempts += 1
            
            if threat_analysis.attack_campaign_correlation:
                self._correlation_matches += 1
            
            self.logger.debug(
                f"Comprehensive analysis completed for {context.email}: "
                f"risk={overall_risk_score:.3f}, level={risk_level.value}, "
                f"block={should_block}, time={processing_time:.3f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            # Return fallback result
            return self._create_fallback_analysis_result(context, start_time, components_used)
    
    async def process_feedback(
        self,
        user_id: str,
        context: AuthContext,
        analysis_result: ComprehensiveAnalysisResult,
        feedback: Dict[str, Any]
    ) -> None:
        """
        Process feedback for all components to improve detection accuracy.
        
        Args:
            user_id: User identifier
            context: Authentication context
            analysis_result: Original analysis result
            feedback: Feedback data
        """
        try:
            # Create AuthFeedback for adaptive learning
            auth_feedback = AuthFeedback(
                user_id=user_id,
                request_id=context.request_id,
                timestamp=context.timestamp,
                original_risk_score=analysis_result.overall_risk_score,
                original_decision='block' if analysis_result.should_block else 'allow',
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
            
            # Process feedback through anomaly detector
            await self.anomaly_detector.learn_from_feedback(user_id, context, feedback)
            
            # Update behavioral model
            await self.adaptive_learning_engine.update_user_behavioral_model(
                user_id, context, not auth_feedback.is_false_positive
            )
            
            self.logger.info(f"Processed comprehensive feedback for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to process comprehensive feedback: {e}")
    
    def _calculate_attack_pattern_risk_score(self, threat_analysis: ThreatAnalysis) -> float:
        """Calculate risk score from attack pattern analysis."""
        try:
            risk_score = 0.0
            
            # Risk from brute force indicators
            if threat_analysis.brute_force_indicators.rapid_attempts:
                risk_score += 0.3
            if threat_analysis.brute_force_indicators.multiple_ips:
                risk_score += 0.2
            if threat_analysis.brute_force_indicators.password_variations:
                risk_score += 0.1
            
            # Risk from credential stuffing indicators
            if threat_analysis.credential_stuffing_indicators.multiple_accounts:
                risk_score += 0.4
            if threat_analysis.credential_stuffing_indicators.common_passwords:
                risk_score += 0.2
            if threat_analysis.credential_stuffing_indicators.distributed_sources:
                risk_score += 0.1
            
            # Risk from account takeover indicators
            if threat_analysis.account_takeover_indicators.location_anomaly:
                risk_score += 0.3
            if threat_analysis.account_takeover_indicators.device_change:
                risk_score += 0.2
            if threat_analysis.account_takeover_indicators.behavior_change:
                risk_score += 0.2
            if threat_analysis.account_takeover_indicators.privilege_escalation:
                risk_score += 0.4
            
            # Risk from known attack patterns
            pattern_risk = min(len(threat_analysis.known_attack_patterns) * 0.1, 0.3)
            risk_score += pattern_risk
            
            # Risk from campaign correlation
            if threat_analysis.attack_campaign_correlation:
                risk_score += 0.2
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Attack pattern risk calculation failed: {e}")
            return 0.0
    
    def _calculate_comprehensive_risk_score(
        self,
        behavioral_risk: float,
        attack_pattern_risk: float,
        threat_intel_risk: float
    ) -> float:
        """Calculate comprehensive risk score from all components."""
        try:
            weighted_score = (
                behavioral_risk * self.component_weights['behavioral_weight'] +
                attack_pattern_risk * self.component_weights['attack_pattern_weight'] +
                threat_intel_risk * self.component_weights['threat_intel_weight']
            )
            
            return min(weighted_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Comprehensive risk calculation failed: {e}")
            return 0.5  # Default moderate risk
    
    def _determine_risk_level(self, risk_score: float, thresholds: RiskThresholds) -> RiskLevel:
        """Determine risk level using adaptive thresholds."""
        if risk_score >= thresholds.critical_risk_threshold:
            return RiskLevel.CRITICAL
        elif risk_score >= thresholds.high_risk_threshold:
            return RiskLevel.HIGH
        elif risk_score >= thresholds.medium_risk_threshold:
            return RiskLevel.MEDIUM
        elif risk_score >= thresholds.low_risk_threshold:
            return RiskLevel.LOW
        else:
            return RiskLevel.LOW
    
    def _calculate_confidence_score(
        self,
        behavioral_analysis: BehavioralAnalysis,
        threat_analysis: ThreatAnalysis,
        overall_risk_score: float
    ) -> float:
        """Calculate confidence score for the analysis."""
        try:
            confidence_factors = []
            
            # Confidence from behavioral analysis consistency
            if behavioral_analysis.is_usual_time == behavioral_analysis.is_usual_location:
                confidence_factors.append(0.2)
            
            # Confidence from threat analysis correlation
            if threat_analysis.similar_attacks_detected > 0:
                confidence_factors.append(0.3)
            
            # Confidence from multiple attack indicators
            attack_indicators = sum([
                threat_analysis.brute_force_indicators.rapid_attempts,
                threat_analysis.credential_stuffing_indicators.multiple_accounts,
                threat_analysis.account_takeover_indicators.location_anomaly
            ])
            if attack_indicators >= 2:
                confidence_factors.append(0.3)
            
            # Confidence from risk score consistency
            if 0.3 <= overall_risk_score <= 0.7:
                confidence_factors.append(0.2)  # Moderate confidence for moderate risk
            elif overall_risk_score > 0.8 or overall_risk_score < 0.2:
                confidence_factors.append(0.4)  # High confidence for extreme scores
            
            # Base confidence
            base_confidence = 0.5
            additional_confidence = sum(confidence_factors)
            
            return min(base_confidence + additional_confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _generate_security_recommendations(
        self,
        risk_score: float,
        risk_level: RiskLevel,
        behavioral_analysis: BehavioralAnalysis,
        threat_analysis: ThreatAnalysis
    ) -> List[SecurityAction]:
        """Generate security action recommendations."""
        try:
            actions = []
            
            # High-risk actions
            if risk_level == RiskLevel.CRITICAL:
                actions.append(SecurityAction(
                    action_type=SecurityActionType.BLOCK,
                    priority=1,
                    description="Block authentication due to critical risk level",
                    automated=True,
                    requires_human_review=False
                ))
            elif risk_level == RiskLevel.HIGH:
                actions.append(SecurityAction(
                    action_type=SecurityActionType.REQUIRE_2FA,
                    priority=2,
                    description="Require additional authentication due to high risk",
                    automated=True,
                    requires_human_review=False
                ))
            
            # Behavioral anomaly actions
            if not behavioral_analysis.is_usual_location:
                actions.append(SecurityAction(
                    action_type=SecurityActionType.MONITOR,
                    priority=3,
                    description="Monitor for unusual location access",
                    automated=True,
                    requires_human_review=False
                ))
            
            # Attack pattern actions
            if threat_analysis.brute_force_indicators.rapid_attempts:
                actions.append(SecurityAction(
                    action_type=SecurityActionType.ALERT,
                    priority=2,
                    description="Alert on potential brute force attack",
                    automated=True,
                    requires_human_review=True
                ))
            
            if threat_analysis.attack_campaign_correlation:
                actions.append(SecurityAction(
                    action_type=SecurityActionType.ALERT,
                    priority=1,
                    description="Alert on coordinated attack campaign",
                    automated=True,
                    requires_human_review=True
                ))
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Security recommendation generation failed: {e}")
            return []
    
    def _calculate_attack_correlation_score(self, threat_analysis: ThreatAnalysis) -> float:
        """Calculate attack correlation score."""
        try:
            correlation_score = 0.0
            
            # Score from similar attacks
            if threat_analysis.similar_attacks_detected > 0:
                correlation_score += min(threat_analysis.similar_attacks_detected / 10, 0.4)
            
            # Score from campaign correlation
            if threat_analysis.attack_campaign_correlation:
                correlation_score += 0.3
            
            # Score from known attack patterns
            pattern_score = min(len(threat_analysis.known_attack_patterns) * 0.1, 0.3)
            correlation_score += pattern_score
            
            return min(correlation_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Attack correlation calculation failed: {e}")
            return 0.0
    
    def _create_fallback_analysis_result(
        self,
        context: AuthContext,
        start_time: float,
        components_used: List[str]
    ) -> ComprehensiveAnalysisResult:
        """Create fallback analysis result in case of errors."""
        try:
            processing_time = time.time() - start_time
            
            # Create minimal behavioral analysis
            fallback_behavioral = BehavioralAnalysis(
                is_usual_time=True,
                time_deviation_score=0.0,
                is_usual_location=True,
                location_deviation_score=0.0,
                is_known_device=True,
                device_similarity_score=1.0,
                login_frequency_anomaly=0.0,
                session_duration_anomaly=0.0,
                success_rate_last_30_days=1.0,
                failed_attempts_pattern={}
            )
            
            # Create minimal threat analysis
            from ai_karen_engine.security.models import (
                BruteForceIndicators,
                CredentialStuffingIndicators,
                AccountTakeoverIndicators
            )
            
            fallback_threat = ThreatAnalysis(
                ip_reputation_score=0.0,
                known_attack_patterns=[],
                threat_actor_indicators=[],
                brute_force_indicators=BruteForceIndicators(),
                credential_stuffing_indicators=CredentialStuffingIndicators(),
                account_takeover_indicators=AccountTakeoverIndicators(),
                similar_attacks_detected=0,
                attack_campaign_correlation=None
            )
            
            return ComprehensiveAnalysisResult(
                behavioral_analysis=fallback_behavioral,
                threat_analysis=fallback_threat,
                overall_risk_score=self.config.fallback_config.fallback_risk_score,
                risk_level=RiskLevel.LOW,
                processing_time=processing_time,
                components_used=components_used,
                confidence_score=0.1,
                recommended_actions=[],
                should_block=False,
                requires_2fa=False,
                attack_correlation_score=0.0,
                behavioral_anomaly_score=0.0,
                threat_intelligence_score=0.0
            )
            
        except Exception as e:
            self.logger.error(f"Fallback result creation failed: {e}")
            # Return absolute minimal result
            return ComprehensiveAnalysisResult(
                behavioral_analysis=fallback_behavioral,
                threat_analysis=fallback_threat,
                overall_risk_score=0.0,
                risk_level=RiskLevel.LOW,
                processing_time=0.0,
                components_used=[],
                confidence_score=0.0,
                recommended_actions=[],
                should_block=False,
                requires_2fa=False,
                attack_correlation_score=0.0,
                behavioral_anomaly_score=0.0,
                threat_intelligence_score=0.0
            )
    
    async def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all components."""
        try:
            # Get metrics from individual components
            anomaly_metrics = self.anomaly_detector.get_metrics()
            attack_metrics = self.attack_pattern_detector.get_service_metrics()
            learning_metrics = await self.adaptive_learning_engine.get_model_performance_metrics()
            
            # Calculate comprehensive metrics
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            comprehensive_metrics = {
                # Overall metrics
                'comprehensive_analyses': self._comprehensive_analyses,
                'high_risk_detections': self._high_risk_detections,
                'blocked_attempts': self._blocked_attempts,
                'correlation_matches': self._correlation_matches,
                'avg_processing_time': avg_processing_time,
                'model_version': self.model_version,
                
                # Component metrics
                'anomaly_detector_metrics': anomaly_metrics,
                'attack_pattern_metrics': attack_metrics,
                'adaptive_learning_metrics': learning_metrics,
                
                # Integration metrics
                'component_weights': self.component_weights,
                'components_health': {
                    'anomaly_detector': 'healthy',  # Would need actual health check
                    'attack_pattern_detector': 'healthy',
                    'adaptive_learning_engine': 'healthy'
                }
            }
            
            return comprehensive_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get comprehensive metrics: {e}")
            return {'error': str(e)}