import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio

from src.ai_karen_engine.auth.config import (
    AuthConfig,
    DatabaseConfig,
    FeatureToggles,
    IntelligenceConfig,
    SecurityConfig,
    SessionConfig,
)
from src.ai_karen_engine.auth.exceptions import (
    AnomalyDetectedError,
    InvalidCredentialsError,
    RateLimitExceededError,
    SessionNotFoundError,
)
from src.ai_karen_engine.auth.intelligence import IntelligenceResult
from src.ai_karen_engine.auth.models import UserData
from src.ai_karen_engine.auth.service import AuthService
from src.ai_karen_engine.auth import core as auth_core


class FakeAuthDatabaseClient:
    """Minimal in-memory stand-in for AuthDatabaseClient."""

    def __init__(self) -> None:
        self.users_by_email = {}
        self.password_hashes = {}

    async def initialize_schema(self) -> None:  # pragma: no cover - no-op
        return None

    async def _ensure_schema(self) -> None:  # pragma: no cover - no-op
        return None

    async def create_user(self, user: UserData, password_hash: str) -> None:
        self.users_by_email[user.email] = user
        self.password_hashes[user.user_id] = password_hash

    async def get_user_by_email(self, email: str):
        return self.users_by_email.get(email)

    async def get_user_password_hash(self, user_id: str):
        return self.password_hashes.get(user_id)

    async def update_user(self, user: UserData) -> None:
        self.users_by_email[user.email] = user

    async def update_user_password_hash(self, user_id: str, new_hash: str) -> None:
        self.password_hashes[user_id] = new_hash


@pytest_asyncio.fixture
async def auth_service(monkeypatch):
    """AuthService instance with in-memory backends for integration tests."""
    monkeypatch.setattr(auth_core, "AuthDatabaseClient", lambda config: FakeAuthDatabaseClient())
    config = AuthConfig(
        database=DatabaseConfig(database_url="sqlite:///:memory:"),
        session=SessionConfig(storage_type="memory", max_sessions_per_user=2, session_timeout_hours=1),
        security=SecurityConfig(
            enable_rate_limiting=True,
            rate_limit_max_requests=3,
            rate_limit_window_minutes=1,
            enable_audit_logging=True,
        ),
        features=FeatureToggles(
            enable_security_features=True,
            enable_rate_limiting=True,
            enable_audit_logging=True,
            enable_session_validation=True,
            enable_intelligent_auth=False,
        ),
        intelligence=IntelligenceConfig(
            enable_intelligent_auth=False,
        ),
    )

    import jwt as jwt_stub

    orig_encode = jwt_stub.encode

    def safe_encode(payload, key, algorithm="HS256"):
        serializable = {
            k: (v.isoformat() if hasattr(v, "isoformat") else v)
            for k, v in payload.items()
        }
        return orig_encode(serializable, key, algorithm)

    monkeypatch.setattr(jwt_stub, "encode", safe_encode)

    service = AuthService(config)
    await service.initialize()

    hasher = service.core_auth.password_hasher
    password_hash = hasher.hash_password("Password123!")
    user = UserData(user_id=str(uuid4()), email="user@example.com", full_name="Test User")
    await service.core_auth.db_client.create_user(user, password_hash)

    yield service, user

    service.core_auth.session_manager.stop_cleanup_task()


@pytest_asyncio.fixture
async def auth_service_intel(monkeypatch):
    """AuthService with intelligence features enabled."""
    monkeypatch.setattr(auth_core, "AuthDatabaseClient", lambda config: FakeAuthDatabaseClient())
    config = AuthConfig(
        database=DatabaseConfig(database_url="sqlite:///:memory:"),
        session=SessionConfig(storage_type="memory", max_sessions_per_user=2, session_timeout_hours=1),
        security=SecurityConfig(
            enable_rate_limiting=True,
            rate_limit_max_requests=3,
            rate_limit_window_minutes=1,
            enable_audit_logging=True,
        ),
        features=FeatureToggles(
            enable_security_features=True,
            enable_rate_limiting=True,
            enable_audit_logging=True,
            enable_session_validation=True,
            enable_intelligent_auth=True,
        ),
        intelligence=IntelligenceConfig(
            enable_intelligent_auth=True,
            enable_anomaly_detection=True,
        ),
    )

    import jwt as jwt_stub

    orig_encode = jwt_stub.encode

    def safe_encode(payload, key, algorithm="HS256"):
        serializable = {
            k: (v.isoformat() if hasattr(v, "isoformat") else v)
            for k, v in payload.items()
        }
        return orig_encode(serializable, key, algorithm)

    monkeypatch.setattr(jwt_stub, "encode", safe_encode)

    service = AuthService(config)
    await service.initialize()

    hasher = service.core_auth.password_hasher
    password_hash = hasher.hash_password("Password123!")
    user = UserData(user_id=str(uuid4()), email="user@example.com", full_name="Test User")
    await service.core_auth.db_client.create_user(user, password_hash)

    yield service, user

    service.core_auth.session_manager.stop_cleanup_task()


class TestAuthFlows:
    @pytest.mark.asyncio
    async def test_successful_auth_flow_with_audit_logging(self, auth_service):
        service, user = auth_service

        logged_in = await service.authenticate_user(
            email=user.email,
            password="Password123!",
            ip_address="10.0.0.1",
            user_agent="test-agent",
        )
        assert logged_in.user_id == user.user_id

        session = await service.create_session(
            logged_in, ip_address="10.0.0.1", user_agent="test-agent"
        )
        validated = await service.validate_session(session.session_token)
        assert validated.email == user.email

        assert await service.invalidate_session(session.session_token)

        with pytest.raises(SessionNotFoundError):
            await service.validate_session(session.session_token)

        stats = service.security_layer.audit_logger.get_stats()
        assert stats["event_counts_by_type"].get("login_success", 0) >= 1
        assert stats["event_counts_by_type"].get("session_created", 0) >= 1

    @pytest.mark.asyncio
    async def test_invalid_login_records_audit(self, auth_service):
        service, _ = auth_service
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(
                email="user@example.com",
                password="wrong",
                ip_address="10.0.0.2",
            )

        stats = service.security_layer.audit_logger.get_stats()
        assert stats["event_counts_by_type"].get("login_failed", 0) >= 1

    @pytest.mark.asyncio
    async def test_rate_limiting_with_concurrent_requests(self, auth_service):
        service, _ = auth_service

        async def attempt(delay: float):
            await asyncio.sleep(delay)
            return await service.authenticate_user(
                email="user@example.com",
                password="wrong",
                ip_address="20.0.0.1",
            )

        tasks = [attempt(i * 0.01) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert any(isinstance(r, RateLimitExceededError) for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_session_limit(self, auth_service):
        service, user = auth_service

        async def create_session(i: int):
            await asyncio.sleep(i * 0.01)
            return await service.create_session(
                user, ip_address=f"30.0.0.{i}", user_agent=f"agent-{i}"
            )

        await asyncio.gather(*(create_session(i) for i in range(3)))
        sessions = await service.core_auth.session_manager.store.get_user_sessions(
            user.user_id
        )
        assert len(sessions) == service.config.session.max_sessions_per_user

    @pytest.mark.asyncio
    async def test_intelligence_blocks_anomalous_login(
        self, auth_service_intel, monkeypatch
    ):
        service, user = auth_service_intel

        async def fake_analysis(*args, **kwargs):
            return IntelligenceResult(risk_score=1.0, risk_level="high", should_block=True)

        monkeypatch.setattr(
            service.intelligence_layer, "analyze_login_attempt", fake_analysis
        )

        with pytest.raises(AnomalyDetectedError):
            await service.authenticate_user(
                email=user.email, password="Password123!", ip_address="40.0.0.1"
            )
