import uuid
from typing import Dict, Optional

import pytest

from ai_karen_engine.security.auth_service import AuthService
from ai_karen_engine.security.config import AuthConfig
from ai_karen_engine.security.models import SessionData, UserData


class DummyAuthenticator:
    """In-memory authenticator used for testing."""

    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, object]] = {}
        self.reset_tokens: Dict[str, str] = {}

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[list[str]] = None,
        tenant_id: str = "default",
        preferences: Optional[Dict[str, object]] = None,
    ) -> UserData:
        user = UserData(
            user_id=email,
            email=email,
            full_name=full_name,
            roles=roles or [],
            tenant_id=tenant_id,
            preferences=preferences or {},
            two_factor_enabled=False,
            is_verified=True,
        )
        self.users[email] = {"password": password, "user": user}
        return user

    async def authenticate_user(
        self, email: str, password: str, ip_address: str = "", user_agent: str = ""
    ) -> Optional[UserData]:
        record = self.users.get(email)
        if record and record["password"] == password:
            return record["user"]
        return None

    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        record = self.users.get(user_id)
        if not record:
            return False
        record["password"] = new_password
        return True

    async def create_password_reset_token(self, email: str) -> str:
        token = f"token-{email}"
        self.reset_tokens[token] = email
        return token

    async def verify_password_reset_token(self, token: str, new_password: str) -> bool:
        email = self.reset_tokens.get(token)
        if not email:
            return False
        return await self.update_user_password(email, new_password)


class DummySessionStore:
    """Simple in-memory session store for tests."""

    def __init__(self) -> None:
        self.sessions: Dict[str, str] = {}
        self.refresh_map: Dict[str, str] = {}

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        token = f"sess-{uuid.uuid4()}"
        refresh = f"ref-{uuid.uuid4()}"
        self.sessions[token] = user_id
        self.refresh_map[refresh] = user_id
        return SessionData(
            access_token=token,
            refresh_token=refresh,
            session_token=token,
            expires_in=3600,
            user_data=None,
        )

    async def validate_session(
        self, session_token: str, ip_address: str = "", user_agent: str = ""
    ) -> Optional[UserData]:
        user_id = self.sessions.get(session_token)
        if not user_id:
            return None
        return UserData(
            user_id=user_id,
            email=user_id,
            full_name=None,
            roles=[],
            tenant_id="default",
            preferences={},
            two_factor_enabled=False,
            is_verified=True,
        )

    async def refresh_token(
        self, refresh_token: str, ip_address: str = "", user_agent: str = ""
    ) -> Optional[SessionData]:
        user_id = self.refresh_map.get(refresh_token)
        if not user_id:
            return None
        return await self.create_session(user_id, ip_address, user_agent)

    async def invalidate_session(self, session_token: str) -> bool:
        return self.sessions.pop(session_token, None) is not None


class DummySecurityEnhancer:
    def __init__(self) -> None:
        self.events: list[tuple[str, Dict[str, object]]] = []

    def allow_auth_attempt(self, key: str) -> bool:  # noqa: D401
        """Always allow auth attempts in tests."""
        return True

    def log_event(self, event: str, data: Optional[Dict[str, object]] = None) -> None:
        self.events.append((event, data or {}))


class DummyIntelligenceEngine:
    class Result:
        def __init__(self) -> None:
            self.should_block = False

    async def analyze_login_attempt(self, context: object) -> "DummyIntelligenceEngine.Result":
        return DummyIntelligenceEngine.Result()


@pytest.mark.asyncio
async def test_authentication_flow():
    authenticator = DummyAuthenticator()
    session_store = DummySessionStore()
    enhancer = DummySecurityEnhancer()
    engine = DummyIntelligenceEngine()
    service = AuthService(
        config=AuthConfig(),
        core_authenticator=authenticator,
        session_store=session_store,
        security_enhancer=enhancer,
        intelligence_engine=engine,
    )

    await service.create_user("user@example.com", "password")
    user = await service.authenticate_user("user@example.com", "password")
    assert user and user.email == "user@example.com"
    assert ("login_success", {"email": "user@example.com"}) in enhancer.events
    assert await service.authenticate_user("user@example.com", "wrong") is None
    assert any(e[0] == "login_failure" for e in enhancer.events)


@pytest.mark.asyncio
async def test_session_lifecycle():
    authenticator = DummyAuthenticator()
    session_store = DummySessionStore()
    service = AuthService(core_authenticator=authenticator, session_store=session_store)

    user = await service.create_user("user2@example.com", "password")
    session = await service.create_session(user.user_id)
    assert session.session_token
    validated = await service.validate_session(session.session_token)
    assert validated and validated.user_id == user.user_id
    new_session = await service.refresh_token(session.refresh_token)
    assert new_session and new_session.session_token != session.session_token


@pytest.mark.asyncio
async def test_password_updates_and_resets():
    authenticator = DummyAuthenticator()
    service = AuthService(core_authenticator=authenticator, session_store=DummySessionStore())

    user = await service.create_user("reset@example.com", "old")
    assert await service.update_password(user.user_id, "new")
    assert await service.authenticate_user("reset@example.com", "new")
    token = await authenticator.create_password_reset_token("reset@example.com")
    assert await service.reset_password(token, "final")
    assert await service.authenticate_user("reset@example.com", "final")


@pytest.mark.asyncio
async def test_log_event_wrapper():
    enhancer = DummySecurityEnhancer()
    service = AuthService(core_authenticator=DummyAuthenticator(), session_store=DummySessionStore(), security_enhancer=enhancer)
    service.log_event("custom", {"value": 1})
    assert ("custom", {"value": 1}) in enhancer.events
