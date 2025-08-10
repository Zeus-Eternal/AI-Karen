from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

from ai_karen_engine.security.adaptive_learning import AdaptiveLearningEngine
from ai_karen_engine.security.behavioral_embedding import BehavioralEmbeddingService
from ai_karen_engine.security.comprehensive_anomaly_engine import (
    ComprehensiveAnomalyEngine,
)
from ai_karen_engine.security.credential_analyzer import CredentialAnalyzer
from ai_karen_engine.security.models import (
    AuthContext,
    EmbeddingAnalysis,
    IntelligentAuthConfig,
)

# mypy: ignore-errors

logger = logging.getLogger(__name__)


@dataclass
class RiskScoreResult:
    """Risk score along with fallback state."""

    risk_score: float
    fallback_mode: bool = False


class IntelligenceEngine:
    """Orchestrates security analysis components and provides risk scoring."""

    def __init__(self, config: Optional[IntelligentAuthConfig] = None) -> None:
        self.config = config or IntelligentAuthConfig()
        self.credential_analyzer = CredentialAnalyzer(self.config)
        self.behavioral_embedding = BehavioralEmbeddingService(config=self.config)
        self.anomaly_engine = ComprehensiveAnomalyEngine(self.config)
        self.adaptive_learning = AdaptiveLearningEngine(self.config)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all component services."""
        if self._initialized:
            return
        await asyncio.gather(
            self.credential_analyzer.initialize(),
            self.behavioral_embedding.initialize(),
            self.anomaly_engine.initialize(),
            self.adaptive_learning.initialize(),
        )
        self._initialized = True

    async def calculate_risk_score(self, context: AuthContext) -> RiskScoreResult:
        """Calculate risk score for an authentication attempt."""
        await self.initialize()

        fallback_mode = False

        try:
            nlp_features = await self.credential_analyzer.analyze_credentials(
                context.email, context.password_hash
            )
        except Exception as e:  # pragma: no cover - logging only
            logger.error(f"Credential analysis failed: {e}")
            fallback_mode = True
            nlp_features = self.credential_analyzer._create_fallback_nlp_features(
                context.email, context.password_hash, 0.0
            )

        start_time = time.time()
        try:
            embedding_result = await self.behavioral_embedding.generate_behavioral_embedding(
                context
            )
        except Exception as e:  # pragma: no cover - logging only
            logger.error(f"Behavioral embedding generation failed: {e}")
            fallback_mode = True
            embedding_result = await self.behavioral_embedding._generate_fallback_embedding(
                context, start_time
            )

        try:
            embedding_analysis = await self.behavioral_embedding.analyze_embedding_for_anomalies(
                context, embedding_result
            )
        except Exception as e:  # pragma: no cover - logging only
            logger.error(f"Embedding anomaly analysis failed: {e}")
            fallback_mode = True
            embedding_analysis = EmbeddingAnalysis(
                embedding_vector=getattr(embedding_result, "embedding_vector", []),
                similarity_to_user_profile=0.0,
                similarity_to_attack_patterns=0.0,
                cluster_assignment=None,
                outlier_score=0.5,
                processing_time=getattr(embedding_result, "processing_time", 0.0),
                model_version=getattr(embedding_result, "model_version", "fallback"),
            )

        try:
            analysis = await self.anomaly_engine.analyze_authentication_attempt(
                context, nlp_features, embedding_analysis
            )
            risk_score = analysis.overall_risk_score
        except Exception as e:  # pragma: no cover - logging only
            logger.error(f"Anomaly engine analysis failed: {e}")
            fallback_mode = True
            risk_score = self.config.fallback_config.fallback_risk_score

        return RiskScoreResult(risk_score=risk_score, fallback_mode=fallback_mode)


__all__ = ["IntelligenceEngine", "RiskScoreResult"]
