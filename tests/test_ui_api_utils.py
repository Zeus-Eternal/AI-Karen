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
