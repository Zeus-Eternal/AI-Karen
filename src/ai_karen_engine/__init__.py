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
    raise AttributeError(name)

__all__ = [
    "SLMPool",
    "LLMOrchestrator",
    "NightlyFineTuner",
    "AutomationManager",
    "PluginRouter",
    "AccessDenied",
    "ModelManager",
    "EchoCore",
    "LNMClient",
    "BasicClassifier",
    "SpaCyClient",
]
