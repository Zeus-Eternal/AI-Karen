"""Core runtime components for Kari."""

from __future__ import annotations

import importlib
import sys

# expose legacy packages under the ``ai_karen_engine`` namespace
for _pkg in [
    "core",
    "integrations",
    "plugins",
    "services",
    "self_refactor",
    "event_bus",
    "ui",
    "guardrails",
]:
    try:
        target = f"src.{_pkg}" if _pkg != "ui" else _pkg
        sys.modules[f"ai_karen_engine.{_pkg}"] = importlib.import_module(target)
    except ModuleNotFoundError:
        pass

from ai_karen_engine.clients.slm_pool import SLMPool
from ai_karen_engine.llm_orchestrator import LLMOrchestrator
from ai_karen_engine.echocore.fine_tuner import NightlyFineTuner
from ai_karen_engine.core.model_manager import ModelManager
from ai_karen_engine.core.echo_core import EchoCore
from ai_karen_engine.clients.transformers.lnm_client import LNMClient
from ai_karen_engine.clients.nlp.basic_classifier import BasicClassifier
from ai_karen_engine.clients.nlp.spacy_client import SpaCyClient

__all__ = [
    "SLMPool",
    "LLMOrchestrator",
    "NightlyFineTuner",
    "ModelManager",
    "EchoCore",
    "LNMClient",
    "BasicClassifier",
    "SpaCyClient",
]
