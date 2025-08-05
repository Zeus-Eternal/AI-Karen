# mypy: ignore-errors
"""Core runtime components for Kari."""


def __getattr__(name):
    if name == "SLMPool":
        from ai_karen_engine.clients.slm_pool import SLMPool as _SLMPool

        return _SLMPool
    if name == "LLMOrchestrator":
        from ai_karen_engine.llm_orchestrator import LLMOrchestrator as _LO

        return _LO
    if name == "NightlyFineTuner":
        from ai_karen_engine.echocore.fine_tuner import NightlyFineTuner as _NT

        return _NT
    if name == "ModelManager":
        from ai_karen_engine.core.model_manager import ModelManager as _MM

        return _MM
    if name == "EchoCore":
        from ai_karen_engine.core.echo_core import EchoCore as _EC

        return _EC
    if name == "LNMClient":
        from ai_karen_engine.clients.transformers.lnm_client import LNMClient as _LC

        return _LC
    if name == "BasicClassifier":
        from ai_karen_engine.clients.nlp.basic_classifier import BasicClassifier as _BC

        return _BC
    if name == "SpaCyClient":
        from ai_karen_engine.clients.nlp.spacy_client import SpaCyClient as _SC

        return _SC
    if name == "AutomationManager":
        from ai_karen_engine.automation_manager import AutomationManager as _AM

        return _AM
    if name == "PluginRouter":
        from ai_karen_engine.plugins.router import PluginRouter as _PR

        return _PR
    if name == "PluginManager":
        from ai_karen_engine.plugins.manager import PluginManager as _PM

        return _PM
    if name == "AccessDenied":
        from ai_karen_engine.plugins.router import AccessDenied as _AD

        return _AD
    if name == "DocumentStore":
        from ai_karen_engine.doc_store import DocumentStore as _DS

        return _DS
    raise AttributeError(name)


__all__ = [
    "SLMPool",
    "LLMOrchestrator",
    "NightlyFineTuner",
    "AutomationManager",
    "PluginRouter",
    "PluginManager",
    "AccessDenied",
    "ModelManager",
    "EchoCore",
    "LNMClient",
    "BasicClassifier",
    "SpaCyClient",
    "DocumentStore",
]
