from __future__ import annotations

import asyncio
import logging
from typing import Optional

from ai_karen_engine.security.adaptive_learning import AdaptiveLearningEngine
from ai_karen_engine.security.behavioral_embedding import BehavioralEmbeddingService
from ai_karen_engine.security.comprehensive_anomaly_engine import (
    ComprehensiveAnomalyEngine,
)
from ai_karen_engine.security.credential_analyzer import CredentialAnalyzer
from ai_karen_engine.security.models import AuthContext, IntelligentAuthConfig

# mypy: ignore-errors

logger = logging.getLogger(__name__)


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

    async def calculate_risk_score(self, context: AuthContext) -> float:
        """Calculate risk score for an authentication attempt."""
        await self.initialize()
        nlp_features = await self.credential_analyzer.analyze_credentials(
            context.email, context.password_hash
        )
        embedding_result = (
            await self.behavioral_embedding.generate_behavioral_embedding(context)
        )
        embedding_analysis = (
            await self.behavioral_embedding.analyze_embedding_for_anomalies(
                context, embedding_result
            )
        )
        analysis = await self.anomaly_engine.analyze_authentication_attempt(
            context, nlp_features, embedding_analysis
        )
        return analysis.overall_risk_score


__all__ = ["IntelligenceEngine"]
