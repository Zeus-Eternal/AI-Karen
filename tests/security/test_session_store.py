import asyncio
import uuid

import pytest
import fakeredis.aioredis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_karen_engine.security.session_store import (
    InMemorySessionStore,
    RedisSessionStore,
    DatabaseSessionStore,
)
from ai_karen_engine.database.models.auth_models import Base, User


@pytest.mark.asyncio
async def test_inmemory_store_expiration():
    store = InMemorySessionStore(expire_seconds=1)
    session = await store.create_session("user")
    assert await store.validate_session(session.session_token) is not None
    await asyncio.sleep(1.1)
    await store.cleanup()
    assert await store.validate_session(session.session_token) is None


@pytest.mark.asyncio
async def test_redis_store_expiration():
    redis = fakeredis.aioredis.FakeRedis()
    store = RedisSessionStore(redis, expire_seconds=1)
    session = await store.create_session("user")
    assert await store.validate_session(session.session_token) is not None
    await asyncio.sleep(1.1)
    assert await store.validate_session(session.session_token) is None


@pytest.fixture()
def db_override(tmp_path):
    db_path = tmp_path / "sess.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    def get_session_override():
        return SessionLocal()

    import ai_karen_engine.database.client as db_client_module
    db_client_module.get_db_session = get_session_override
    import ai_karen_engine.security.session_store as ss_module
    ss_module.get_db_session = get_session_override
    return get_session_override


@pytest.mark.asyncio
async def test_database_store_expiration(db_override):
    get_session = db_override
    user_id = uuid.uuid4()
    with get_session() as db:
        user = User(id=user_id, email="user@example.com", password_hash="x")
        db.add(user)
        db.commit()
    store = DatabaseSessionStore(expire_seconds=1)
    session = await store.create_session(str(user_id))
    assert await store.validate_session(session.session_token) is not None
    await asyncio.sleep(1.1)
    await store.cleanup()
    assert await store.validate_session(session.session_token) is None
