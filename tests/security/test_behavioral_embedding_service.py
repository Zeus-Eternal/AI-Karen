# mypy: ignore-errors
from datetime import datetime
from types import SimpleNamespace

import pytest

from ai_karen_engine.security.behavioral_embedding import (
    BehavioralEmbeddingConfig,
    BehavioralEmbeddingService,
)
from ai_karen_engine.security.models import AuthContext


class FailingDistilBertService:
    fallback_mode = False
    config = SimpleNamespace(model_name="test")

    async def get_embeddings(self, text: str, normalize: bool = True):
        raise RuntimeError("fail")


@pytest.mark.asyncio
async def test_fallback_embedding_generation():
    service = BehavioralEmbeddingService(
        distilbert_service=FailingDistilBertService(),
        config=BehavioralEmbeddingConfig(),
    )
    context = AuthContext(
        email="user@example.com",
        password_hash="hash",
        client_ip="127.0.0.1",
        user_agent="agent",
        timestamp=datetime.utcnow(),
        request_id="req",
    )
    result = await service.generate_behavioral_embedding(context)
    assert result.used_fallback is True
    assert len(result.embedding_vector) > 0


@pytest.mark.asyncio
async def test_minimal_fallback_when_hash_generation_fails():
    service = BehavioralEmbeddingService(
        distilbert_service=FailingDistilBertService(),
        config=BehavioralEmbeddingConfig(),
    )

    async def fail_hash(text: str):  # type: ignore[override]
        raise RuntimeError("hash fail")

    service._generate_hash_embedding = fail_hash  # type: ignore
    context = AuthContext(
        email="user@example.com",
        password_hash="hash",
        client_ip="127.0.0.1",
        user_agent="agent",
        timestamp=datetime.utcnow(),
        request_id="req",
    )
    result = await service.generate_behavioral_embedding(context)
    assert result.used_fallback is True
    assert result.model_version == "minimal_fallback"
    assert len(result.embedding_vector) == 768


@pytest.mark.asyncio
async def test_device_hash_consistency_across_sessions():
    service = BehavioralEmbeddingService(
        distilbert_service=FailingDistilBertService(),
        config=BehavioralEmbeddingConfig(),
    )
    context1 = AuthContext(
        email="user@example.com",
        password_hash="hash",
        client_ip="127.0.0.1",
        user_agent="agent",
        timestamp=datetime.utcnow(),
        request_id="req1",
    )
    result1 = await service.generate_behavioral_embedding(context1)
    await service.update_user_behavioral_profile(
        "user@example.com", context1, result1, login_successful=True
    )
    profile = service.get_user_profile("user@example.com")
    assert profile is not None
    assert len(profile.typical_devices) == 1
    first_hash = profile.typical_devices[0]

    context2 = AuthContext(
        email="user@example.com",
        password_hash="hash",
        client_ip="127.0.0.1",
        user_agent="agent",
        timestamp=datetime.utcnow(),
        request_id="req2",
    )
    result2 = await service.generate_behavioral_embedding(context2)
    await service.update_user_behavioral_profile(
        "user@example.com", context2, result2, login_successful=True
    )
    profile = service.get_user_profile("user@example.com")
    assert profile is not None
    assert len(profile.typical_devices) == 1
    assert profile.typical_devices[0] == first_hash
