import importlib
import logging

import pytest


def _reload_module(monkeypatch):
    import ai_karen_engine.automation_manager.encryption_utils as eu
    importlib.reload(eu)
    return eu


def test_development_fallback(monkeypatch, caplog):
    monkeypatch.delenv("KARI_JOB_ENC_KEY", raising=False)
    caplog.set_level(
        logging.WARNING,
        logger="ai_karen_engine.automation_manager.encryption_utils",
    )
    eu = _reload_module(monkeypatch)
    assert eu.ENCRYPTION_KEY
    assert "ephemeral key" in caplog.text
    token = eu.encrypt_data("secret")
    assert eu.decrypt_data(token) == "secret"


def test_set_encryption_key_invalid(monkeypatch):
    monkeypatch.delenv("KARI_JOB_ENC_KEY", raising=False)
    eu = _reload_module(monkeypatch)
    with pytest.raises(ValueError):
        eu.set_encryption_key("invalid")
