from datetime import datetime
from types import SimpleNamespace

import pytest

from ai_karen_engine.security.intelligence_engine import IntelligenceEngine
from ai_karen_engine.security.models import (
    AuthContext,
    EmbeddingAnalysis,
    IntelligentAuthConfig,
)


class DummyCredentialAnalyzer:
    async def initialize(self):
        pass

    async def analyze_credentials(self, email: str, password_hash: str):
        return SimpleNamespace()

    def _create_fallback_nlp_features(
        self, email: str, password_hash: str, processing_time: float
    ):
        return SimpleNamespace()


class FailingCredentialAnalyzer(DummyCredentialAnalyzer):
    async def analyze_credentials(self, email: str, password_hash: str):
        raise RuntimeError("boom")


class DummyBehavioralEmbedding:
    async def initialize(self):
        pass

    async def generate_behavioral_embedding(self, context: AuthContext):
        return SimpleNamespace(
            embedding_vector=[0.0],
            processing_time=0.0,
            model_version="dummy",
        )

    async def analyze_embedding_for_anomalies(
        self, context: AuthContext, embedding_result: SimpleNamespace
    ):
        return EmbeddingAnalysis(
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
    ):
        return await self.generate_behavioral_embedding(context)


class DummyAnomalyEngine:
    async def initialize(self):
        pass

    async def analyze_authentication_attempt(
        self, context: AuthContext, nlp_features, embedding_analysis
    ):
        return SimpleNamespace(overall_risk_score=0.42)


class FailingAnomalyEngine(DummyAnomalyEngine):
    async def analyze_authentication_attempt(
        self, context: AuthContext, nlp_features, embedding_analysis
    ):
        raise RuntimeError("fail")


class DummyAdaptiveLearning:
    async def initialize(self):
        pass


@pytest.mark.asyncio
async def test_risk_score_normal_flow():
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
    assert result.fallback_mode is False
    assert result.risk_score == pytest.approx(0.42)


@pytest.mark.asyncio
async def test_risk_score_fallback_on_failure():
    engine = IntelligenceEngine.__new__(IntelligenceEngine)
    engine.config = IntelligentAuthConfig()
    engine.credential_analyzer = FailingCredentialAnalyzer()
    engine.behavioral_embedding = DummyBehavioralEmbedding()
    engine.anomaly_engine = FailingAnomalyEngine()
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
