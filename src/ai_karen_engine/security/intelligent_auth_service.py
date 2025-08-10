from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ai_karen_engine.security.intelligence_engine import IntelligenceEngine
from ai_karen_engine.security.intelligent_auth_base import (
    BaseIntelligentAuthService,
    IntelligentAuthServiceInterface,
    IntelligentAuthHealthStatus,
    ServiceHealthStatus,
    ServiceStatus,
    register_service,
    get_service_registry,
    HealthMonitor,
)
from ai_karen_engine.security.models import (
    AuthAnalysisResult,
    AuthContext,
    IntelligentAuthConfig,
    NLPFeatures,
    EmbeddingAnalysis,
)

logger = logging.getLogger(__name__)


class IntelligentAuthService(BaseIntelligentAuthService, IntelligentAuthServiceInterface):
    """High-level service wrapping :class:`IntelligenceEngine`.

    This service orchestrates credential analysis, behavioral embedding,
    anomaly detection and adaptive learning. It exposes the
    ``IntelligentAuthServiceInterface`` for other modules and registers all
    component services in the global registry for dependency injection.
    """

    def __init__(
        self,
        config: Optional[IntelligentAuthConfig] = None,
        engine: Optional[IntelligenceEngine] = None,
    ) -> None:
        super().__init__(config or IntelligentAuthConfig())
        self.engine = engine or IntelligenceEngine(self.config)
        self.health_monitor: Optional[HealthMonitor] = None

        # Register components for dependency injection
        register_service("credential_analyzer", self.engine.credential_analyzer)
        register_service("behavioral_embedding", self.engine.behavioral_embedding)
        # Register underlying anomaly detector if available
        if hasattr(self.engine.anomaly_engine, "anomaly_detector"):
            register_service(
                "anomaly_detector", self.engine.anomaly_engine.anomaly_detector
            )
        else:
            register_service("anomaly_detector", self.engine.anomaly_engine)
        register_service("intelligent_auth_service", self)

    async def initialize(self) -> bool:
        """Initialize all dependent components and start monitoring."""
        try:
            await self.engine.initialize()
            # Start health monitoring for registered services
            self.health_monitor = HealthMonitor(get_service_registry())
            await self.health_monitor.start_monitoring()
            self.logger.info("IntelligentAuthService initialized successfully")
            return True
        except Exception as exc:  # pragma: no cover - initialization errors
            self.logger.error(f"Failed to initialize IntelligentAuthService: {exc}")
            return False

    async def shutdown(self) -> None:
        """Shutdown engine components and stop monitoring."""
        try:
            if self.health_monitor is not None:
                await self.health_monitor.stop_monitoring()
            await asyncio.gather(
                self.engine.credential_analyzer.shutdown(),
                self.engine.behavioral_embedding.shutdown(),
                self.engine.anomaly_engine.shutdown(),
                self.engine.adaptive_learning.shutdown(),
            )
            self.logger.info("IntelligentAuthService shutdown complete")
        except Exception as exc:  # pragma: no cover - shutdown errors
            self.logger.error(f"Error during IntelligentAuthService shutdown: {exc}")

    async def analyze_login_attempt(self, context: AuthContext) -> AuthAnalysisResult:
        """Run the full analysis pipeline for a login attempt."""
        # Ensure engine is initialized
        await self.engine.initialize()

        # Credential and embedding analysis
        nlp_features: NLPFeatures = await self.engine.credential_analyzer.analyze_credentials(
            context.email, context.password_hash
        )
        embedding_result = await self.engine.behavioral_embedding.generate_behavioral_embedding(
            context
        )
        embedding_analysis: EmbeddingAnalysis = (
            await self.engine.behavioral_embedding.analyze_embedding_for_anomalies(
                context, embedding_result
            )
        )

        # Comprehensive anomaly analysis
        comp_result = await self.engine.anomaly_engine.analyze_authentication_attempt(
            context, nlp_features, embedding_analysis
        )

        return AuthAnalysisResult(
            risk_score=comp_result.overall_risk_score,
            risk_level=comp_result.risk_level,
            should_block=comp_result.should_block,
            requires_2fa=comp_result.requires_2fa,
            nlp_features=nlp_features,
            embedding_analysis=embedding_analysis,
            behavioral_analysis=comp_result.behavioral_analysis,
            threat_analysis=comp_result.threat_analysis,
            processing_time=comp_result.processing_time,
            model_versions={
                "comprehensive_anomaly_engine": getattr(
                    self.engine.anomaly_engine, "model_version", "unknown"
                )
            },
            confidence_score=comp_result.confidence_score,
            recommended_actions=comp_result.recommended_actions,
            user_feedback_required=False,
        )

    async def update_user_behavioral_profile(
        self, user_id: str, context: AuthContext, success: bool
    ) -> None:
        """Update the adaptive learning model for a user."""
        await self.engine.adaptive_learning.update_user_behavioral_model(
            user_id, context, success
        )

    async def provide_feedback(
        self, user_id: str, context: AuthContext, feedback: Dict[str, Any]
    ) -> None:
        """Provide feedback to improve ML models."""
        nlp_features = await self.engine.credential_analyzer.analyze_credentials(
            context.email, context.password_hash
        )
        embedding_result = await self.engine.behavioral_embedding.generate_behavioral_embedding(
            context
        )
        embedding_analysis = (
            await self.engine.behavioral_embedding.analyze_embedding_for_anomalies(
                context, embedding_result
            )
        )
        analysis_result = await self.engine.anomaly_engine.analyze_authentication_attempt(
            context, nlp_features, embedding_analysis
        )
        await self.engine.anomaly_engine.process_feedback(
            user_id, context, analysis_result, feedback
        )

    def get_health_status(self) -> IntelligentAuthHealthStatus:
        """Get current health status for all registered components."""
        if self.health_monitor is not None:
            return self.health_monitor.get_current_health_status()
        return IntelligentAuthHealthStatus(
            overall_status=ServiceStatus.UNKNOWN,
            component_statuses={},
            last_updated=datetime.now(),
        )

    async def _perform_health_check(self) -> bool:
        """Check health of all engine components."""
        try:
            statuses = await asyncio.gather(
                self.engine.credential_analyzer.health_check(),
                self.engine.behavioral_embedding.health_check(),
                self.engine.anomaly_engine.health_check(),
                self.engine.adaptive_learning.health_check(),
            )
            return all(
                isinstance(status, ServiceHealthStatus)
                and status.status in {ServiceStatus.HEALTHY, ServiceStatus.DEGRADED}
                for status in statuses
            )
        except Exception as exc:  # pragma: no cover - health check errors
            self.logger.error(f"Health check error: {exc}")
            return False


def create_intelligent_auth_service(
    config: Optional[IntelligentAuthConfig] = None,
    engine: Optional[IntelligenceEngine] = None,
) -> IntelligentAuthService:
    """Factory helper to create and register an ``IntelligentAuthService``."""
    service = IntelligentAuthService(config, engine)
    register_service("intelligent_auth_service", service)
    return service


__all__ = ["IntelligentAuthService", "create_intelligent_auth_service"]
