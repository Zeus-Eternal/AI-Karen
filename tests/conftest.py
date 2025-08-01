"""Shared pytest configuration."""
import importlib
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
# Prefer the real `requests` package when available to support
# libraries that rely on its internal structure. Fall back to the
# lightweight stub only if `requests` cannot be imported.
try:
    import requests as _real_requests  # type: ignore
    sys.modules.setdefault("requests", _real_requests)
except Exception:  # pragma: no cover - only used when requests isn't installed
    sys.modules.setdefault("requests", importlib.import_module("tests.stubs.requests"))
sys.modules.setdefault("tenacity", importlib.import_module("tests.stubs.tenacity"))
pg_mod = importlib.import_module("tests.stubs.ai_karen_engine.clients.database.postgres_client")

sys.modules.setdefault("duckdb", importlib.import_module("tests.stubs.duckdb"))
sys.modules.setdefault("numpy", importlib.import_module("tests.stubs.numpy"))
sys.modules.setdefault("pyautogui", importlib.import_module("tests.stubs.pyautogui"))
sys.modules.setdefault("cryptography", importlib.import_module("tests.stubs.cryptography"))
sys.modules.setdefault("ollama", importlib.import_module("tests.stubs.ollama"))
sys.modules.setdefault("jwt", importlib.import_module("tests.stubs.jwt"))
sys.modules.setdefault(
    "streamlit_autorefresh", importlib.import_module("tests.stubs.streamlit_autorefresh")
)


# Alias installed-style packages for tests
sys.modules.setdefault("ai_karen_engine", importlib.import_module("ai_karen_engine"))
sys.modules.setdefault("ui_logic", importlib.import_module("ui_logic"))
sys.modules.setdefault("services", importlib.import_module("ai_karen_engine.services"))
sys.modules.setdefault("integrations", importlib.import_module("ai_karen_engine.integrations"))
sys.modules.setdefault("integrations.llm_registry", importlib.import_module("ai_karen_engine.integrations.llm_registry"))
sys.modules.setdefault("integrations.model_discovery", importlib.import_module("ai_karen_engine.integrations.model_discovery"))
sys.modules.setdefault("integrations.llm_utils", importlib.import_module("ai_karen_engine.integrations.llm_utils"))
sys.modules.setdefault("fastapi", importlib.import_module("ai_karen_engine.fastapi_stub"))
sys.modules.setdefault("fastapi_stub", importlib.import_module("ai_karen_engine.fastapi_stub"))
sys.modules.setdefault("fastapi.testclient", importlib.import_module("ai_karen_engine.fastapi_stub.testclient"))
sys.modules.setdefault("pydantic", importlib.import_module("ai_karen_engine.pydantic_stub"))

os.environ.setdefault("KARI_MODEL_SIGNING_KEY", "test")
os.environ.setdefault("KARI_DUCKDB_PASSWORD", "test")
os.environ.setdefault("KARI_JOB_SIGNING_KEY", "test")
os.environ.setdefault("DUCKDB_PATH", ":memory:")

# Lightweight LLMOrchestrator stub to avoid heavyweight dependencies
llm_stub = types.ModuleType("ai_karen_engine.llm_orchestrator")

class LLMOrchestrator:
    def __init__(self, pool=None):
        self.default_llm = object()

    def generate_text(self, prompt: str, *_, **__):
        return prompt

llm_stub.LLMOrchestrator = LLMOrchestrator
sys.modules.setdefault("ai_karen_engine.llm_orchestrator", llm_stub)

# Provide lightweight stubs for modules missing in the test environment
cortex_stub = types.ModuleType("ai_karen_engine.core.cortex.dispatch")

cortex_stub = types.ModuleType("ai_karen_engine.core.cortex.dispatch")

class CortexDispatcher:
    async def dispatch(self, user_ctx, query: str, role: str = "user", **_):
        text = query.lower()
        if "hello" in text:
            return {
                "intent": "greet",
                "confidence": 0.9,
                "response": "Hey there! I'm Kari—your AI co-pilot. What can I help with today?",
            }
        if text.startswith("why") or "why" in text:
            return {
                "intent": "deep_reasoning",
                "confidence": 0.8,
                "response": "Because of entropy and other mysterious forces.",
            }
        if "time" in text:
            return {"intent": "time_query", "confidence": 0.8, "response": "UTC"}
        return {"intent": "hf_generate", "confidence": 0.5, "response": query}

cortex_stub.CortexDispatcher = CortexDispatcher
cortex_stub.dispatch = lambda *a, **k: CortexDispatcher().dispatch(*a, **k)
cortex_stub.CortexDispatchError = Exception
sys.modules.setdefault("ai_karen_engine.core.cortex.dispatch", cortex_stub)

gpu_stub = types.ModuleType("ai_karen_engine.core.gpu_training")
gpu_stub.torch = None

def gpu_optimized_train(*_, **__):
    raise RuntimeError("GPU training requires torch")

gpu_stub.gpu_optimized_train = gpu_optimized_train
sys.modules.setdefault("ai_karen_engine.core.gpu_training", gpu_stub)

intent_stub = types.ModuleType("ai_karen_engine.core.intent_engine")

class IntentEngine:
    def detect(self, text: str) -> str:
        return "greet" if "hello" in text else "hf_generate"

intent_stub.IntentEngine = IntentEngine
sys.modules.setdefault("ai_karen_engine.core.intent_engine", intent_stub)

# Lightweight spaCy stub for document tests
spacy_stub = types.ModuleType("spacy")

class DummyDoc:
    def __init__(self, text: str):
        self.text = text
        self.sents = [types.SimpleNamespace(text=t) for t in text.split("\n")]

def blank(lang: str = "en"):
    def nlp(text: str):
        return DummyDoc(text)
    nlp.add_pipe = lambda name: None
    return nlp

spacy_stub.blank = blank
sys.modules.setdefault("spacy", spacy_stub)
