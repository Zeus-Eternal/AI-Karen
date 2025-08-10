import pytest
from datetime import datetime
from types import SimpleNamespace

from ai_karen_engine.security.intelligence_engine import IntelligenceEngine
from ai_karen_engine.security.models import AuthContext, IntelligentAuthConfig


class DummyCredentialAnalyzer:
    async def initialize(self):
        pass

    async def analyze_credentials(self, email: str, password_hash: str):
        raise RuntimeError("fail")

    def _create_fallback_nlp_features(self, email: str, password_hash: str, processing_time: float):
        return SimpleNamespace()


class DummyBehavioralEmbedding:
    async def initialize(self):
        pass

    async def generate_behavioral_embedding(self, context: AuthContext):
        return SimpleNamespace(
            embedding_vector=[0.0],
            processing_time=0.0,
            model_version="dummy",
        )

    async def analyze_embedding_for_anomalies(self, context: AuthContext, embedding_result: SimpleNamespace):
        return SimpleNamespace(
            embedding_vector=embedding_result.embedding_vector,
            similarity_to_user_profile=0.0,
            similarity_to_attack_patterns=0.0,
            cluster_assignment=None,
            outlier_score=0.0,
            processing_time=embedding_result.processing_time,
            model_version=embedding_result.model_version,
        )

    async def _generate_fallback_embedding(self, context: AuthContext, start_time: float):
        return await self.generate_behavioral_embedding(context)


class DummyAnomalyEngine:
    async def initialize(self):
        pass

    async def analyze_authentication_attempt(self, context: AuthContext, nlp_features, embedding_analysis):
        raise RuntimeError("fail")


class DummyAdaptiveLearning:
    async def initialize(self):
        pass


@pytest.mark.asyncio
async def test_fallback_flag_triggered():
    engine = IntelligenceEngine(IntelligentAuthConfig())
    engine.credential_analyzer = DummyCredentialAnalyzer()
    engine.behavioral_embedding = DummyBehavioralEmbedding()
    engine.anomaly_engine = DummyAnomalyEngine()
    engine.adaptive_learning = DummyAdaptiveLearning()

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
