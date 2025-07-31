import importlib
import os
import pytest

from ai_karen_engine.core import default_models


@pytest.mark.asyncio
async def test_load_default_models_eco_mode(monkeypatch):
    monkeypatch.setenv("KARI_ECO_MODE", "true")
    importlib.reload(default_models)
    await default_models.load_default_models()
    assert default_models.embedding_manager.model_loaded is False
    assert default_models.spacy_client is None
    assert default_models.classifier is None


@pytest.mark.asyncio
async def test_load_default_models_normal(monkeypatch):
    monkeypatch.delenv("KARI_ECO_MODE", raising=False)
    importlib.reload(default_models)
    await default_models.load_default_models()
    assert default_models.embedding_manager is not None

