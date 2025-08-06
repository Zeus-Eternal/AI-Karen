# mypy: ignore-errors

import importlib

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_karen_engine.database.models.auth_models import Base


@pytest.fixture()
def auth(tmp_path):
    db_path = tmp_path / "auth.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    def get_session_override():
        return SessionLocal()

    import ai_karen_engine.database.client as db_client_module

    db_client_module.get_db_session = get_session_override

    import ai_karen_engine.security.auth_service as auth_module

    importlib.reload(auth_module)
    authenticator = auth_module.CoreAuthenticator()
    yield authenticator


@pytest.mark.asyncio
async def test_password_utilities(auth):
    hashed = auth.hash_password("secret")
    assert hashed != "secret"
    assert auth.verify_password("secret", hashed)
    assert not auth.verify_password("wrong", hashed)


@pytest.mark.asyncio
async def test_authentication(auth):
    await auth.create_user("user@example.com", "password")
    user = await auth.authenticate_user("user@example.com", "password")
    assert user is not None
    assert user.email == "user@example.com"
    assert await auth.authenticate_user("user@example.com", "wrong") is None


@pytest.mark.asyncio
async def test_session_creation_and_validation(auth):
    user = await auth.create_user("session@example.com", "password")
    session = await auth.create_session(user.user_id)
    assert session.session_token
    validated = await auth.validate_session(session.session_token)
    assert validated is not None
    assert validated.email == "session@example.com"
