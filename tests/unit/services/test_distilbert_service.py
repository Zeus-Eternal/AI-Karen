import logging
import sys

# Ensure real numpy is available (tests may provide a stub)
sys.modules.pop("numpy", None)
import numpy as real_numpy  # noqa: E402
sys.modules["numpy"] = real_numpy

import torch
import ai_karen_engine.services.distilbert_service as ds
from ai_karen_engine.services.distilbert_service import DistilBertService, DistilBertConfig


def _mock_load_model(self):
    """Return empty tokenizer and model to bypass heavy initialization."""
    return None, None


def test_setup_device_gpu(monkeypatch, caplog):
    """Service should use GPU when CUDA is available."""
    monkeypatch.setattr(ds, "torch", torch)
    monkeypatch.setattr(ds, "TRANSFORMERS_AVAILABLE", True)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda: "Mock GPU")
    monkeypatch.setattr(DistilBertService, "_load_model", _mock_load_model)

    caplog.set_level(logging.INFO)
    service = DistilBertService(DistilBertConfig(enable_gpu=True))

    assert service.device.type == "cuda"
    assert "Using GPU: Mock GPU" in caplog.text


def test_setup_device_cpu_when_cuda_unavailable(monkeypatch, caplog):
    """Service should fall back to CPU when CUDA is unavailable."""
    monkeypatch.setattr(ds, "torch", torch)
    monkeypatch.setattr(ds, "TRANSFORMERS_AVAILABLE", True)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(DistilBertService, "_load_model", _mock_load_model)

    caplog.set_level(logging.INFO)
    service = DistilBertService(DistilBertConfig(enable_gpu=True))

    assert service.device.type == "cpu"
    assert "CUDA unavailable, using CPU for inference" in caplog.text

