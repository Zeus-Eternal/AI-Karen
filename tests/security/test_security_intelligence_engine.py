from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest  # type: ignore[import-not-found]

from ai_karen_engine.security.intelligence_engine import (  # type: ignore[import-not-found]
    IntelligenceEngine,
)
from ai_karen_engine.security.models import (  # type: ignore[import-not-found]
    AuthContext,
    IntelligentAuthConfig,
)


class DummyCredentialAnalyzer:
    async def initialize(self) -> None:
        pass

    async def analyze_credentials(
        self, email: str, password_hash: str
    ) -> SimpleNamespace:
        raise RuntimeError("fail")

    def _create_fallback_nlp_features(
        self, email: str, password_hash: str, processing_time: float
    ) -> SimpleNamespace:
        return SimpleNamespace()


class DummyBehavioralEmbedding:
    async def initialize(self) -> None:
        pass

    async def generate_behavioral_embedding(
        self, context: AuthContext
    ) -> SimpleNamespace:
        return SimpleNamespace(
            embedding_vector=[0.0],
            processing_time=0.0,
            model_version="dummy",
        )

    async def analyze_embedding_for_anomalies(
        self, context: AuthContext, embedding_result: SimpleNamespace
    ) -> SimpleNamespace:
        return SimpleNamespace(
            embedding_vector=embedding_result.embedding_vector,
            similarity_to_user_profile=0.0,
            similarity_to_attack_patterns=0.0,
            cluster_assignment=None,
            outlier_score=0.0,
            processing_time=embedding_result.processing_time,
            model_version=embedding_result.model_version,
        )

    async def _generate_fallback_embedding(
        self, context: AuthContext, start_time: float
    ) -> SimpleNamespace:
        return await self.generate_behavioral_embedding(context)


class DummyAnomalyEngine:
    async def initialize(self) -> None:
        pass

    async def analyze_authentication_attempt(
        self, context: AuthContext, nlp_features: Any, embedding_analysis: Any
    ) -> Any:
        raise RuntimeError("fail")


class DummyAdaptiveLearning:
    async def initialize(self) -> None:
        pass


class FailingCredentialAnalyzer(DummyCredentialAnalyzer):
    async def initialize(self) -> None:
        raise RuntimeError("init fail")


@pytest.mark.asyncio  # type: ignore[misc]
async def test_fallback_flag_triggered() -> None:
    engine = IntelligenceEngine.__new__(IntelligenceEngine)
    engine.config = IntelligentAuthConfig()
    engine.credential_analyzer = DummyCredentialAnalyzer()
    engine.behavioral_embedding = DummyBehavioralEmbedding()
    engine.anomaly_engine = DummyAnomalyEngine()
    engine.adaptive_learning = DummyAdaptiveLearning()
    engine._initialized = False

    context = AuthContext(
        email="user@example.com",
        password_hash="hash",
        client_ip="127.0.0.1",
        user_agent="agent",
        timestamp=datetime.utcnow(),
        request_id="req",
    )

    result = await engine.calculate_risk_score(context)

    assert result.fallback_mode is True
    assert result.risk_score == engine.config.fallback_config.fallback_risk_score


@pytest.mark.asyncio  # type: ignore[misc]
async def test_initialize_failure_reverts_initialized_flag() -> None:
    engine = IntelligenceEngine.__new__(IntelligenceEngine)
    engine.config = IntelligentAuthConfig()
    engine.credential_analyzer = FailingCredentialAnalyzer()
    engine.behavioral_embedding = DummyBehavioralEmbedding()
    engine.anomaly_engine = DummyAnomalyEngine()
    engine.adaptive_learning = DummyAdaptiveLearning()
    engine._initialized = False

    with pytest.raises(RuntimeError):
        await engine.initialize()
    assert engine._initialized is False
