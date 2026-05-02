import importlib
import os

import pytest


def test_neuro_recall_blocked_by_default(monkeypatch):
    monkeypatch.delenv("KARI_NEURO_RECALL_LABS_ENABLED", raising=False)
    with pytest.raises(RuntimeError):
        importlib.import_module("ai_karen_engine.core.neuro_recall")


def test_neuro_recall_enabled(monkeypatch):
    monkeypatch.setenv("KARI_NEURO_RECALL_LABS_ENABLED", "true")
    mod = importlib.import_module("ai_karen_engine.core.neuro_recall")
    assert mod._labs_enabled() is True
