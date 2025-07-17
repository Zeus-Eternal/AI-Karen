import pytest
import requests
import tenacity

import ui_logic.utils.api as api


def test_fetch_announcements_404(monkeypatch):
    def fake_api_get(*_, **__):
        raise RuntimeError('API error: 404 {"detail":"Not Found"}')

    monkeypatch.setattr(api, "api_get", fake_api_get)
    assert api.fetch_announcements(limit=3) == []


def test_fetch_announcements_other_error(monkeypatch):
    def fake_api_get(*_, **__):
        raise RuntimeError('API error: 500 {"detail":"oops"}')

    monkeypatch.setattr(api, "api_get", fake_api_get)
    with pytest.raises(RuntimeError):
        api.fetch_announcements()
        
class DummyResponse:
    def __init__(self, status_code: int = 200, text: str = "ok"):
        self.status_code = status_code
        self.text = text
        self.headers = {"Content-Type": "text/plain"}

    def json(self):
        return self.text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def test_safe_request_retries(monkeypatch):
    calls = {"count": 0}

    def flaky_request(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.RequestException("temp fail")
        return DummyResponse()

    monkeypatch.setattr(api.requests, "request", flaky_request)
    monkeypatch.setattr(tenacity, "nap", lambda _: None)

    resp = api._safe_request("get", "http://x")
    assert calls["count"] == 3
    assert resp.status_code == 200


def test_safe_request_failure(monkeypatch):
    def always_fail(*_, **__):
        raise requests.RequestException("boom")

    monkeypatch.setattr(api.requests, "request", always_fail)
    monkeypatch.setattr(tenacity, "nap", lambda _: None)

    with pytest.raises(requests.RequestException):
        api._safe_request("get", "http://x")