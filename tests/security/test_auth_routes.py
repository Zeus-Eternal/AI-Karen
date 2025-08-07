from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from uuid import uuid4

from ai_karen_engine.security.models import SessionData, UserData


class DummyAuthService:
    def __init__(self) -> None:
        self.users: dict[str, str] = {}
        self.sessions: dict[str, str] = {}

    async def create_user(self, email: str, password: str, **_) -> UserData:
        self.users[email] = password
        return UserData(
            user_id=email,
            email=email,
            full_name=None,
            roles=[],
            tenant_id="default",
            preferences={},
            two_factor_enabled=False,
            is_verified=True,
        )

    async def authenticate_user(self, email: str, password: str, **_) -> UserData | None:
        if self.users.get(email) == password:
            return UserData(
                user_id=email,
                email=email,
                full_name=None,
                roles=[],
                tenant_id="default",
                preferences={},
                two_factor_enabled=False,
                is_verified=True,
            )
        return None

    async def create_session(self, user_id: str, **_) -> SessionData:
        token = f"tok-{len(self.sessions)+1}"
        self.sessions[token] = user_id
        return SessionData(
            access_token=token,
            refresh_token=f"ref-{token}",
            session_token=token,
            expires_in=3600,
            user_data=None,
        )

    async def validate_session(self, session_token: str, **_) -> UserData | None:
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


def _unique_email() -> str:
    return f"user{uuid4().hex}@example.com"


def get_client() -> tuple[TestClient, DummyAuthService]:
    service = DummyAuthService()
    app = FastAPI()

    @app.post("/auth/register")
    async def register(data: dict, *_, **__) -> dict:
        user = await service.create_user(data["email"], data["password"])
        session = await service.create_session(user.user_id)
        return {"access_token": session.access_token, "user": {"email": user.email}}

    @app.post("/auth/login")
    async def login(data: dict, *_, **__) -> dict:
        user = await service.authenticate_user(data["email"], data["password"])
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        session = await service.create_session(user.user_id)
        return {"access_token": session.access_token, "user": {"email": user.email}}

    @app.get("/auth/me")
    async def me(request: Request, *_, **__) -> dict:
        header = request.headers.get("Authorization")
        if not header or not header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        token = header.split()[1]
        user = await service.validate_session(token)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return {"email": user.email}

    return TestClient(app), service


def test_register_and_me() -> None:
    client, _ = get_client()
    email = _unique_email()
    resp = client.post("/auth/register", json={"email": email, "password": "secret"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    resp_me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_me.status_code == 200
    assert resp_me.json()["email"] == email


def test_login_invalid_credentials() -> None:
    client, _ = get_client()
    email = _unique_email()
    client.post("/auth/register", json={"email": email, "password": "secret"})
    resp = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


def test_me_requires_auth() -> None:
    client, _ = get_client()
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authentication required"

