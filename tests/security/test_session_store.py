
import pytest
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from ai_karen_engine.security.session_store import SessionStore, Base

try:
    import fakeredis
except ImportError:  # pragma: no cover
    fakeredis = None


@pytest.mark.asyncio
async def test_memory_backend():
    store = SessionStore()
    await store.set_session("s1", {"user_id": "u1", "foo": "bar"}, ttl_seconds=60)

    data = await store.get_session("s1")
    assert data["foo"] == "bar"

    sessions = await store.get_sessions_by_user("u1")
    assert len(sessions) == 1

    assert await store.count_sessions() == 1
    assert await store.delete_session("s1")
    assert await store.get_session("s1") is None


@pytest.mark.asyncio
async def test_redis_backend():
    if fakeredis is None:
        pytest.skip("fakeredis not installed")
    client = fakeredis.FakeStrictRedis()
    store = SessionStore(backend="redis", redis_client=client)

    await store.set_session("s1", {"user_id": "u1", "foo": "bar"}, ttl_seconds=60)
    assert (await store.get_session("s1")) == {"user_id": "u1", "foo": "bar"}
    sessions = await store.get_sessions_by_user("u1")
    assert len(sessions) == 1
    assert await store.count_sessions() == 1
    assert await store.delete_session("s1")
    assert await store.get_session("s1") is None


@pytest.mark.asyncio
async def test_database_backend():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    store = SessionStore(backend="database", db_sessionmaker=Session)
    await store.set_session("s1", {"user_id": "u1", "foo": "bar"}, ttl_seconds=60)
    assert (await store.get_session("s1"))["foo"] == "bar"
    sessions = await store.get_sessions_by_user("u1")
    assert len(sessions) == 1
    assert await store.count_sessions() == 1
    assert await store.delete_session("s1")
    assert await store.get_session("s1") is None
