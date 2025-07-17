import pytest

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


def test_fetch_announcements_cached(monkeypatch):
    calls = []

    def fake_api_get(*args, **kwargs):
        calls.append(1)
        return ["a1"]

    monkeypatch.setattr(api, "api_get", fake_api_get)
    api._ann_cache.clear()

    r1 = api.fetch_announcements(limit=5, token="t", org="o")
    r2 = api.fetch_announcements(limit=5, token="t", org="o")

    assert r1 == r2 == ["a1"]
    assert len(calls) == 1
