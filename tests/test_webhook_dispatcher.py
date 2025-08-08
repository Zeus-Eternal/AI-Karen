import hashlib
import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from ai_karen_engine.database.models import Base, Webhook
from ai_karen_engine.services.webhook_service import dispatch_webhook


@pytest.mark.asyncio
async def test_dispatch_webhook_respects_enabled_and_events():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        hook1 = Webhook(webhook_id="1", url="https://example.com/h1", events=["file.uploaded"], enabled=True)
        hook2 = Webhook(webhook_id="2", url="https://example.com/h2", events=["file.uploaded"], enabled=False)
        hook3 = Webhook(webhook_id="3", url="https://example.com/h3", events=["other.event"], enabled=True)
        session.add_all([hook1, hook2, hook3])
        await session.commit()

        received = []

        async def handler(request):
            received.append(str(request.url))
            return httpx.Response(200)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            await dispatch_webhook("file.uploaded", {"x": 1}, session=session, http_client=client)

        assert received == ["https://example.com/h1"]


def test_webhook_secret_hashing():
    hook = Webhook(url="https://example.com", events=["a"], enabled=True)
    hook.secret = "topsecret"
    assert hook.secret == hashlib.sha256("topsecret".encode()).hexdigest()
