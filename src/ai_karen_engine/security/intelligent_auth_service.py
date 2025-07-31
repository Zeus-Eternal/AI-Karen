"""
Unified Intelligent Authentication Service.

This module provides the main orchestration service that coordinates all ML components
for intelligent authentication, including NLP analysis, embedding generation,
anomaly detection, and threat intelligence with comprehensive error handling
and performance monitoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cachetools import TTLCache
import threading

from ai_karen_engine.security.models import (
    AuthContext,
    AuthAnalysisResult,
    IntelligentAuthConfig,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis,
    SecurityAction,
    SecurityActionType,
    RiskLevel,
    CredentialFeatures
)
from ai_karen_engine.security.intelligent_auth_base import (
    BaseIntelligentAuthService,
    IntelligentAuthServiceInterface,
    ServiceHealthStatus,
    ServiceStatus,
    IntelligentAuthHealthStatus,
    get_service_registry
)

# Import existing components
from ai_karen_engine.security.credential_analyzer import CredentialAnalyzer
from ai_karen_engine.security.behavioral_embedding import BehavioralEmbeddingService
from ai_karen_engine.security.comprehensive_anomaly_engine import ComprehensiveAnomalyEngine
from ai_karen_engine.security.threat_intelligence import ThreatIntelligenceEngine
from ai_karen_engine.security.adaptive_learning import AdaptiveLearningEngine, AuthFeedback

# Import existing services
from ai_karen_engine.services.spacy_service import SpacyService
from ai_karen_engine.services.distilbert_service import DistilBertService

logger = logging.getLogger(__name__)


@dataclass
class ProcessingMetrics:
    """Metrics for processing performance tracking."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_processing_time: float = 0.0
    nlp_processing_time: float = 0.0
    embedding_processing_time: float = 0.0
    anomaly_processing_time: float = 0.0
    threat_processing_time: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'avg_processing_time': self.avg_processing_time,
            'nlp_processing_time': self.nlp_processing_time,
            'embedding_processing_time': self.embedding_processing_time,
            'anomaly_processing_time': self.anomaly_processing_time,
            'threat_processing_time': self.threat_processing_time,
            'cache_hit_rate': self.cache_hit_rate,
            'error_rate': self.error_rate,
            'last_updated': self.last_updated.isoformat()
        }


class IntelligentAuthService(BaseIntelligentAuthService, IntelligentAuthServiceInterface):
    """
    Unified intelligent authentication service that orchestrates all ML components.
    
    This service provides comprehensive authentication analysis by coordinating:
    - NLP-based credential analysis
    - Behavioral embedding generation
    - Multi-dimensional anomaly detection
    - Threat intelligence integration
    - Adaptive learning and feedback processing
    """

    def __init__(self, 
                 config: Optional[IntelligentAuthConfig] = None,
                 spacy_service: Optional[SpacyService] = None,
                 distilbert_service: Optional[DistilBertService] = None):
        """
        Initialize the intelligent authentication service.
        
        Args:
            config: Configuration for intelligent authentication
            spacy_service: Optional SpaCy service instance
            distilbert_service: Optional DistilBERT service instance
        """
        super().__init__(config or IntelligentAuthConfig())
        
        # Core services
        self.spacy_service = spacy_service or SpacyService()
        self.distilbert_service = distilbert_service or DistilBertService()
        
        # ML Components
        self.credential_analyzer: Optional[CredentialAnalyzer] = None
        self.behavioral_embedding: Optional[BehavioralEmbeddingService] = None
        self.anomaly_engine: Optional[ComprehensiveAnomalyEngine] = None
        self.threat_intelligence: Optional[ThreatIntelligenceEngine] = None
        self.adaptive_learning: Optional[AdaptiveLearningEngine] = None
        
        # Caching and performance
        self.analysis_cache = TTLCache(
            maxsize=self.config.cache_size,
            ttl=self.config.cache_ttl
        )
        self.cache_lock = threading.RLock()
        
        # Metrics and monitoring
        self.metrics = ProcessingMetrics()
        self.processing_times: List[float] = []
        self.error_history: List[Dict[str, Any]] = []
        
        # Component health tracking
        self.component_health: Dict[str, ServiceHealthStatus] = {}
        self.last_health_check = datetime.now()
        
        # Initialization flag
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize all ML components and dependencies.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            self.logger.info("Initializing Intelligent Authentication Service...")
            
            # Initialize ML components
            await self._initialize_components()
            
            # Register components in service registry
            self._register_components()
            
            # Perform initial health check
            await self._perform_initial_health_check()
            
            self._initialized = True
            self.logger.info("Intelligent Authentication Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Intelligent Authentication Service: {e}")
            return False

    async def _initialize_components(self) -> None:
        """Initialize all ML components."""
        try:
            # Initialize credential analyzer
            self.credential_analyzer = CredentialAnalyzer(
                config=self.config,
                spacy_service=self.spacy_service
            )
            await self.credential_analyzer.initialize()
            
            # Initialize behavioral embedding service
            self.behavioral_embedding = BehavioralEmbeddingService(
                config=self.config,
                distilbert_service=self.distilbert_service
            )
            await self.behavioral_embedding.initialize()
            
            # Initialize comprehensive anomaly engine
            self.anomaly_engine = ComprehensiveAnomalyEngine(
                config=self.config
            )
            await self.anomaly_engine.initialize()
            
            # Initialize threat intelligence engine
            if self.config.enable_threat_intelligence:
                self.threat_intelligence = ThreatIntelligenceEngine(
                    config=self.config
                )
                await self.threat_intelligence.initialize()
            
            # Initialize adaptive learning engine
            if self.config.feature_flags.enable_behavioral_learning:
                self.adaptive_learning = AdaptiveLearningEngine(
                    config=self.config
                )
                await self.adaptive_learning.initialize()
                
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise

    def _register_components(self) -> None:
        """Register components in the service registry."""
        registry = get_service_registry()
        
        registry.register_service("intelligent_auth_service", self)
        
        if self.credential_analyzer:
            registry.register_service("credential_analyzer", self.credential_analyzer)
        
        if self.behavioral_embedding:
            registry.register_service("behavioral_embedding", self.behavioral_embedding)
        
        if self.anomaly_engine:
            registry.register_service("anomaly_engine", self.anomaly_engine)
        
        if self.threat_intelligence:
            registry.register_service("threat_intelligence", self.threat_intelligence)
        
        if self.adaptive_learning:
            registry.register_service("adaptive_learning", self.adaptive_learning)

    async def _perform_initial_health_check(self) -> None:
        """Perform initial health check on all components."""
        components = {
            "credential_analyzer": self.credential_analyzer,
            "behavioral_embedding": self.behavioral_embedding,
            "anomaly_engine": self.anomaly_engine,
            "threat_intelligence": self.threat_intelligence,
            "adaptive_learning": self.adaptive_learning
        }
        
        for name, component in components.items():
            if component:
                try:
                    health_status = await component.health_check()
                    self.component_health[name] = health_status
                except Exception as e:
                    self.logger.error(f"Health check failed for {name}: {e}")
                    self.component_health[name] = ServiceHealthStatus(
                        service_name=name,
                        status=ServiceStatus.UNHEALTHY,
                        last_check=datetime.now(),
                        error_message=str(e)
                    )

    async def analyze_login_attempt(self, context: AuthContext) -> AuthAnalysisResult:
        """
        Perform comprehensive analysis of login attempt.
        
        Args:
            context: Authentication context with login details
            
        Returns:
            AuthAnalysisResult: Comprehensive analysis result
        """
        start_time = time.time()
        request_id = context.request_id
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(context)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.debug(f"Cache hit for request {request_id}")
                return cached_result
            
            self.logger.info(f"Starting comprehensive analysis for request {request_id}")
            
            # Initialize result components with defaults
            nlp_features = await self._analyze_credentials_with_fallback(context)
            embedding_analysis = await self._generate_embedding_with_fallback(context)
            behavioral_analysis = await self._detect_anomalies_with_fallback(
                context, nlp_features, embedding_analysis
            )
            threat_analysis = await self._analyze_threats_with_fallback(context)
            
            # Calculate comprehensive risk score
            risk_score = await self._calculate_comprehensive_risk_score(
                context, nlp_features, embedding_analysis, behavioral_analysis, threat_analysis
            )
            
            # Determine risk level and actions
            risk_level = self._determine_risk_level(risk_score)
            should_block, requires_2fa = self._determine_security_actions(risk_score, risk_level)
            recommended_actions = self._generate_security_recommendations(
                risk_score, risk_level, context
            )
            
            # Create comprehensive result
            processing_time = time.time() - start_time
            result = AuthAnalysisResult(
                risk_score=risk_score,
                risk_level=risk_level,
                should_block=should_block,
                requires_2fa=requires_2fa,
                nlp_features=nlp_features,
                embedding_analysis=embedding_analysis,
                behavioral_analysis=behavioral_analysis,
                threat_analysis=threat_analysis,
                processing_time=processing_time,
                model_versions=self._get_model_versions(),
                confidence_score=self._calculate_confidence_score(
                    nlp_features, embedding_analysis, behavioral_analysis, threat_analysis
                ),
                analysis_timestamp=datetime.now(),
                recommended_actions=recommended_actions,
                user_feedback_required=self._should_request_feedback(risk_score, risk_level)
            )
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            # Update metrics
            self._update_metrics(processing_time, success=True)
            
            self.logger.info(
                f"Analysis completed for request {request_id}: "
                f"risk_score={risk_score:.3f}, risk_level={risk_level.value}, "
                f"processing_time={processing_time:.3f}s"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Analysis failed for request {request_id}: {e}")
            
            # Update error metrics
            self._update_metrics(processing_time, success=False)
            self._record_error(e, context)
            
            # Return fallback result
            return self._create_fallback_result(context, processing_time, str(e))

    async def _analyze_credentials_with_fallback(self, context: AuthContext) -> NLPFeatures:
        """Analyze credentials with fallback handling."""
        if not self.config.enable_nlp_analysis or not self.credential_analyzer:
            return self._create_fallback_nlp_features()
        
        try:
            start_time = time.time()
            result = await self.credential_analyzer.analyze_credentials(
                context.email, context.password_hash
            )
            self.metrics.nlp_processing_time = time.time() - start_time
            return result
        except Exception as e:
            self.logger.warning(f"NLP analysis failed, using fallback: {e}")
            if self.config.fallback_config.block_on_nlp_failure:
                raise
            return self._create_fallback_nlp_features()

    async def _generate_embedding_with_fallback(self, context: AuthContext) -> EmbeddingAnalysis:
        """Generate behavioral embedding with fallback handling."""
        if not self.config.enable_embedding_analysis or not self.behavioral_embedding:
            return self._create_fallback_embedding_analysis()
        
        try:
            start_time = time.time()
            result = await self.behavioral_embedding.generate_embedding(context)
            self.metrics.embedding_processing_time = time.time() - start_time
            return result
        except Exception as e:
            self.logger.warning(f"Embedding generation failed, using fallback: {e}")
            if self.config.fallback_config.block_on_embedding_failure:
                raise
            return self._create_fallback_embedding_analysis()

    async def _detect_anomalies_with_fallback(self, 
                                            context: AuthContext,
                                            nlp_features: NLPFeatures,
                                            embedding_analysis: EmbeddingAnalysis) -> BehavioralAnalysis:
        """Detect anomalies with fallback handling."""
        if not self.config.enable_behavioral_analysis or not self.anomaly_engine:
            return self._create_fallback_behavioral_analysis()
        
        try:
            start_time = time.time()
            result = await self.anomaly_engine.detect_anomalies(
                context, nlp_features, embedding_analysis
            )
            self.metrics.anomaly_processing_time = time.time() - start_time
            return result
        except Exception as e:
            self.logger.warning(f"Anomaly detection failed, using fallback: {e}")
            if self.config.fallback_config.block_on_anomaly_failure:
                raise
            return self._create_fallback_behavioral_analysis()

    async def _analyze_threats_with_fallback(self, context: AuthContext) -> ThreatAnalysis:
        """Analyze threats with fallback handling."""
        if not self.config.enable_threat_intelligence or not self.threat_intelligence:
            return self._create_fallback_threat_analysis()
        
        try:
            start_time = time.time()
            result = await self.threat_intelligence.analyze_threat_context(context)
            self.metrics.threat_processing_time = time.time() - start_time
            return result
        except Exception as e:
            self.logger.warning(f"Threat analysis failed, using fallback: {e}")
            return self._create_fallback_threat_analysis()

    async def _calculate_comprehensive_risk_score(self,
                                                context: AuthContext,
                                                nlp_features: NLPFeatures,
                                                embedding_analysis: EmbeddingAnalysis,
                                                behavioral_analysis: BehavioralAnalysis,
                                                threat_analysis: ThreatAnalysis) -> float:
        """Calculate comprehensive risk score from all analysis components."""
        try:
            if self.anomaly_engine:
                return await self.anomaly_engine.calculate_risk_score(
                    context, nlp_features, embedding_analysis, behavioral_analysis
                )
            else:
                # Fallback risk calculation
                return self._calculate_fallback_risk_score(
                    nlp_features, embedding_analysis, behavioral_analysis, threat_analysis
                )
        except Exception as e:
            self.logger.warning(f"Risk score calculation failed, using fallback: {e}")
            return self.config.fallback_config.fallback_risk_score

    def _calculate_fallback_risk_score(self,
                                     nlp_features: NLPFeatures,
                                     embedding_analysis: EmbeddingAnalysis,
                                     behavioral_analysis: BehavioralAnalysis,
                                     threat_analysis: ThreatAnalysis) -> float:
        """Calculate fallback risk score using simple heuristics."""
        risk_factors = []
        
        # NLP-based risk factors
        if nlp_features.suspicious_patterns:
            risk_factors.append(0.3)
        if nlp_features.credential_similarity > 0.8:
            risk_factors.append(0.2)
        
        # Embedding-based risk factors
        if embedding_analysis.outlier_score > 0.7:
            risk_factors.append(0.4)
        if embedding_analysis.similarity_to_attack_patterns > 0.6:
            risk_factors.append(0.5)
        
        # Behavioral risk factors
        if not behavioral_analysis.is_usual_time:
            risk_factors.append(0.2)
        if not behavioral_analysis.is_usual_location:
            risk_factors.append(0.3)
        if behavioral_analysis.login_frequency_anomaly > 0.7:
            risk_factors.append(0.3)
        
        # Threat intelligence risk factors
        if threat_analysis.ip_reputation_score > 0.7:
            risk_factors.append(0.6)
        if threat_analysis.known_attack_patterns:
            risk_factors.append(0.8)
        
        # Calculate weighted average
        if not risk_factors:
            return 0.0
        
        return min(sum(risk_factors) / len(risk_factors), 1.0)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on score and thresholds."""
        thresholds = self.config.risk_thresholds
        
        if risk_score >= thresholds.critical_risk_threshold:
            return RiskLevel.CRITICAL
        elif risk_score >= thresholds.high_risk_threshold:
            return RiskLevel.HIGH
        elif risk_score >= thresholds.medium_risk_threshold:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _determine_security_actions(self, risk_score: float, risk_level: RiskLevel) -> tuple[bool, bool]:
        """Determine if login should be blocked or require 2FA."""
        thresholds = self.config.risk_thresholds
        
        should_block = risk_score >= thresholds.critical_risk_threshold
        requires_2fa = risk_score >= thresholds.high_risk_threshold and not should_block
        
        return should_block, requires_2fa

    def _generate_security_recommendations(self,
                                         risk_score: float,
                                         risk_level: RiskLevel,
                                         context: AuthContext) -> List[SecurityAction]:
        """Generate security action recommendations."""
        actions = []
        
        if risk_level == RiskLevel.CRITICAL:
            actions.append(SecurityAction(
                action_type=SecurityActionType.BLOCK.value,
                priority=1,
                description="Block login due to critical risk level",
                automated=True,
                requires_human_review=False
            ))
        elif risk_level == RiskLevel.HIGH:
            actions.append(SecurityAction(
                action_type=SecurityActionType.REQUIRE_2FA.value,
                priority=2,
                description="Require 2FA due to high risk level",
                automated=True,
                requires_human_review=False
            ))
        elif risk_level == RiskLevel.MEDIUM:
            actions.append(SecurityAction(
                action_type=SecurityActionType.MONITOR.value,
                priority=3,
                description="Monitor user activity due to medium risk level",
                automated=True,
                requires_human_review=False
            ))
        
        # Add alerting for unusual patterns
        if context.is_tor_exit_node or context.is_vpn:
            actions.append(SecurityAction(
                action_type=SecurityActionType.ALERT.value,
                priority=2,
                description="Alert on Tor/VPN usage",
                automated=True,
                requires_human_review=True
            ))
        
        return actions

    def _calculate_confidence_score(self,
                                  nlp_features: NLPFeatures,
                                  embedding_analysis: EmbeddingAnalysis,
                                  behavioral_analysis: BehavioralAnalysis,
                                  threat_analysis: ThreatAnalysis) -> float:
        """Calculate confidence score for the analysis."""
        confidence_factors = []
        
        # NLP confidence
        if not nlp_features.used_fallback:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.3)
        
        # Embedding confidence
        if len(embedding_analysis.embedding_vector) > 0:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.2)
        
        # Behavioral confidence (based on historical data availability)
        if behavioral_analysis.success_rate_last_30_days > 0:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        # Threat intelligence confidence
        if threat_analysis.ip_reputation_score > 0:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5

    def _should_request_feedback(self, risk_score: float, risk_level: RiskLevel) -> bool:
        """Determine if user feedback should be requested."""
        # Request feedback for borderline cases to improve model accuracy
        thresholds = self.config.risk_thresholds
        
        return (
            (thresholds.medium_risk_threshold - 0.1 <= risk_score <= thresholds.medium_risk_threshold + 0.1) or
            (thresholds.high_risk_threshold - 0.1 <= risk_score <= thresholds.high_risk_threshold + 0.1)
        )

    async def update_user_behavioral_profile(self, 
                                           user_id: str, 
                                           context: AuthContext, 
                                           success: bool) -> None:
        """
        Update user's behavioral profile based on login outcome.
        
        Args:
            user_id: User identifier
            context: Authentication context
            success: Whether the login was successful
        """
        try:
            # Update behavioral embedding profile
            if self.behavioral_embedding:
                await self.behavioral_embedding.update_user_profile(
                    user_id, context, success
                )
            
            # Update anomaly detection models
            if self.anomaly_engine:
                await self.anomaly_engine.update_user_profile(
                    user_id, context, success
                )
            
            # Update adaptive learning
            if self.adaptive_learning:
                feedback = AuthFeedback(
                    user_id=user_id,
                    context=context,
                    actual_outcome=success,
                    feedback_type="login_outcome",
                    timestamp=datetime.now()
                )
                await self.adaptive_learning.process_feedback(feedback)
                
            self.logger.debug(f"Updated behavioral profile for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update behavioral profile for user {user_id}: {e}")

    async def provide_feedback(self, 
                             user_id: str, 
                             context: AuthContext,
                             feedback: Dict[str, Any]) -> None:
        """
        Provide feedback to improve ML models.
        
        Args:
            user_id: User identifier
            context: Authentication context
            feedback: Feedback data
        """
        try:
            if self.adaptive_learning:
                auth_feedback = AuthFeedback(
                    user_id=user_id,
                    context=context,
                    feedback_data=feedback,
                    feedback_type="user_feedback",
                    timestamp=datetime.now()
                )
                await self.adaptive_learning.process_feedback(auth_feedback)
                
            self.logger.info(f"Processed feedback for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to process feedback for user {user_id}: {e}")

    def get_health_status(self) -> IntelligentAuthHealthStatus:
        """Get comprehensive health status of all components."""
        # Update component health if needed
        if (datetime.now() - self.last_health_check).seconds > 300:  # 5 minutes
            asyncio.create_task(self._update_component_health())
        
        # Determine overall status
        overall_status = ServiceStatus.HEALTHY
        for health_status in self.component_health.values():
            if health_status.status == ServiceStatus.UNHEALTHY:
                overall_status = ServiceStatus.UNHEALTHY
                break
            elif health_status.status == ServiceStatus.DEGRADED:
                overall_status = ServiceStatus.DEGRADED
        
        return IntelligentAuthHealthStatus(
            overall_status=overall_status,
            component_statuses=self.component_health,
            last_updated=datetime.now(),
            processing_metrics=self.metrics.to_dict()
        )

    async def _update_component_health(self) -> None:
        """Update health status of all components."""
        components = {
            "credential_analyzer": self.credential_analyzer,
            "behavioral_embedding": self.behavioral_embedding,
            "anomaly_engine": self.anomaly_engine,
            "threat_intelligence": self.threat_intelligence,
            "adaptive_learning": self.adaptive_learning
        }
        
        for name, component in components.items():
            if component:
                try:
                    self.component_health[name] = await component.health_check()
                except Exception as e:
                    self.component_health[name] = ServiceHealthStatus(
                        service_name=name,
                        status=ServiceStatus.UNHEALTHY,
                        last_check=datetime.now(),
                        error_message=str(e)
                    )
        
        self.last_health_check = datetime.now()

    async def shutdown(self) -> None:
        """Gracefully shutdown the service and all components."""
        try:
            self.logger.info("Shutting down Intelligent Authentication Service...")
            
            # Shutdown all components
            components = [
                self.credential_analyzer,
                self.behavioral_embedding,
                self.anomaly_engine,
                self.threat_intelligence,
                self.adaptive_learning
            ]
            
            for component in components:
                if component and hasattr(component, 'shutdown'):
                    try:
                        await component.shutdown()
                    except Exception as e:
                        self.logger.error(f"Error shutting down component: {e}")
            
            # Clear caches
            self.analysis_cache.clear()
            
            self._initialized = False
            self.logger.info("Intelligent Authentication Service shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def _perform_health_check(self) -> bool:
        """Service-specific health check implementation."""
        try:
            # Check if core components are available
            if not self._initialized:
                return False
            
            # Check critical components
            critical_components = [
                self.credential_analyzer,
                self.behavioral_embedding,
                self.anomaly_engine
            ]
            
            for component in critical_components:
                if component:
                    health_status = await component.health_check()
                    if health_status.status == ServiceStatus.UNHEALTHY:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    # Cache management methods
    def _generate_cache_key(self, context: AuthContext) -> str:
        """Generate cache key for authentication context."""
        key_data = f"{context.email}:{context.client_ip}:{context.user_agent}:{context.timestamp.hour}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _get_cached_result(self, cache_key: str) -> Optional[AuthAnalysisResult]:
        """Get cached analysis result."""
        with self.cache_lock:
            return self.analysis_cache.get(cache_key)

    def _cache_result(self, cache_key: str, result: AuthAnalysisResult) -> None:
        """Cache analysis result."""
        with self.cache_lock:
            self.analysis_cache[cache_key] = result

    # Metrics and monitoring methods
    def _update_metrics(self, processing_time: float, success: bool) -> None:
        """Update processing metrics."""
        self.metrics.total_requests += 1
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Update processing times
        self.processing_times.append(processing_time)
        if len(self.processing_times) > 1000:  # Keep last 1000 measurements
            self.processing_times = self.processing_times[-1000:]
        
        # Calculate averages
        if self.processing_times:
            self.metrics.avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        
        # Calculate rates
        if self.metrics.total_requests > 0:
            self.metrics.error_rate = self.metrics.failed_requests / self.metrics.total_requests
            
            # Calculate cache hit rate
            cache_hits = len([t for t in self.processing_times if t < 0.1])  # Fast responses likely cached
            self.metrics.cache_hit_rate = cache_hits / len(self.processing_times) if self.processing_times else 0.0
        
        self.metrics.last_updated = datetime.now()

    def _record_error(self, error: Exception, context: AuthContext) -> None:
        """Record error for monitoring and debugging."""
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'request_id': context.request_id,
            'user_email': context.email,
            'client_ip': context.client_ip
        }
        
        self.error_history.append(error_record)
        
        # Keep only recent errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

    # Fallback result creation methods
    def _create_fallback_result(self, 
                              context: AuthContext, 
                              processing_time: float, 
                              error_message: str) -> AuthAnalysisResult:
        """Create fallback result when analysis fails."""
        return AuthAnalysisResult(
            risk_score=self.config.fallback_config.fallback_risk_score,
            risk_level=RiskLevel.LOW,
            should_block=False,
            requires_2fa=False,
            nlp_features=self._create_fallback_nlp_features(),
            embedding_analysis=self._create_fallback_embedding_analysis(),
            behavioral_analysis=self._create_fallback_behavioral_analysis(),
            threat_analysis=self._create_fallback_threat_analysis(),
            processing_time=processing_time,
            model_versions={"fallback": "1.0"},
            confidence_score=0.1,
            analysis_timestamp=datetime.now(),
            recommended_actions=[
                SecurityAction(
                    action_type=SecurityActionType.MONITOR.value,
                    priority=5,
                    description=f"Fallback mode due to error: {error_message}",
                    automated=False,
                    requires_human_review=True
                )
            ],
            user_feedback_required=True
        )

    def _create_fallback_nlp_features(self) -> NLPFeatures:
        """Create fallback NLP features."""
        return NLPFeatures(
            email_features=CredentialFeatures(
                token_count=0,
                unique_token_ratio=0.0,
                entropy_score=0.0,
                language="unknown",
                contains_suspicious_patterns=False,
                pattern_types=[]
            ),
            password_features=CredentialFeatures(
                token_count=0,
                unique_token_ratio=0.0,
                entropy_score=0.0,
                language="unknown",
                contains_suspicious_patterns=False,
                pattern_types=[]
            ),
            credential_similarity=0.0,
            language_consistency=True,
            suspicious_patterns=[],
            processing_time=0.0,
            used_fallback=True,
            model_version="fallback"
        )

    def _create_fallback_embedding_analysis(self) -> EmbeddingAnalysis:
        """Create fallback embedding analysis."""
        return EmbeddingAnalysis(
            embedding_vector=[0.0] * 768,  # Standard DistilBERT dimension
            similarity_to_user_profile=0.5,
            similarity_to_attack_patterns=0.0,
            cluster_assignment=None,
            outlier_score=0.0,
            processing_time=0.0,
            model_version="fallback"
        )

    def _create_fallback_behavioral_analysis(self) -> BehavioralAnalysis:
        """Create fallback behavioral analysis."""
        return BehavioralAnalysis(
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

    def _create_fallback_threat_analysis(self) -> ThreatAnalysis:
        """Create fallback threat analysis."""
        from ai_karen_engine.security.models import (
            BruteForceIndicators,
            CredentialStuffingIndicators,
            AccountTakeoverIndicators
        )
        
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

    def _get_model_versions(self) -> Dict[str, str]:
        """Get version information for all ML models."""
        versions = {}
        
        if self.credential_analyzer:
            versions["credential_analyzer"] = "1.0"
        
        if self.behavioral_embedding:
            versions["behavioral_embedding"] = "1.0"
        
        if self.anomaly_engine:
            versions["anomaly_engine"] = "1.0"
        
        if self.threat_intelligence:
            versions["threat_intelligence"] = "1.0"
        
        if self.adaptive_learning:
            versions["adaptive_learning"] = "1.0"
        
        return versions

    def get_processing_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics."""
        return self.metrics

    def get_error_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent error history."""
        return self.error_history[-limit:] if limit > 0 else self.error_history