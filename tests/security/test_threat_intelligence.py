import asyncio

import pytest

from ai_karen_engine.security.threat_intelligence import ThreatFeedManager


class MockResponse:
    def __init__(self, status=200, payload=None):
        self.status = status
        self._payload = payload or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def json(self):
        await asyncio.sleep(0)  # simulate async
        return self._payload


class DummySession:
    def __init__(self, response):
        self._response = response
        self.calls = 0
        self.closed = False

    def get(self, *args, **kwargs):
        self.calls += 1
        return self._response

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_query_abuse_ipdb_success_and_cache(monkeypatch):
    response = MockResponse(payload={"data": {"ipAddress": "1.2.3.4"}})
    session = DummySession(response)
    monkeypatch.setattr("aiohttp.ClientSession", lambda *a, **k: session)

    async with ThreatFeedManager({"abuseipdb_api_key": "key"}) as manager:
        result1 = await manager.query_abuse_ipdb("1.2.3.4")
        result2 = await manager.query_abuse_ipdb("1.2.3.4")  # cached

    assert result1 == {"ipAddress": "1.2.3.4"}
    assert result2 == {"ipAddress": "1.2.3.4"}
    assert session.calls == 1  # second call used cache


@pytest.mark.asyncio
async def test_query_abuse_ipdb_error_handling(monkeypatch):
    class ErrorSession(DummySession):
        def get(self, *args, **kwargs):  # type: ignore[override]
            raise RuntimeError("boom")

    session = ErrorSession(MockResponse())
    monkeypatch.setattr("aiohttp.ClientSession", lambda *a, **k: session)

    async with ThreatFeedManager({"abuseipdb_api_key": "key"}) as manager:
        result = await manager.query_abuse_ipdb("1.2.3.4")

    assert result is None
    assert session.calls == 0


@pytest.mark.asyncio
async def test_query_virustotal_rate_limit(monkeypatch):
    response = MockResponse(payload={"data": {"id": "1.2.3.4"}})
    session = DummySession(response)
    monkeypatch.setattr("aiohttp.ClientSession", lambda *a, **k: session)

    async with ThreatFeedManager({"virustotal_api_key": "key"}) as manager:
        monkeypatch.setattr(manager, "_check_rate_limit", lambda *a, **k: False)
        result = await manager.query_virustotal("1.2.3.4")

    assert result is None
    assert session.calls == 0


@pytest.mark.asyncio
async def test_explicit_close(monkeypatch):
    response = MockResponse(payload={"data": {"ipAddress": "1.2.3.4"}})
    session = DummySession(response)
    monkeypatch.setattr("aiohttp.ClientSession", lambda *a, **k: session)

    manager = ThreatFeedManager({"abuseipdb_api_key": "key"})
    await manager.__aenter__()
    await manager.query_abuse_ipdb("1.2.3.4")
    await manager.close()

    assert session.calls == 1
    assert session.closed
