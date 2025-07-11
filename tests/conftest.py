"""Shared pytest configuration."""
import importlib
import os
import sys
import types
import ai_karen_engine.clients.database.postgres_client as pg_mod


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

class TestPostgresClient(pg_mod.PostgresClient):
    def __init__(self, dsn: str = "sqlite:///:memory:", use_sqlite: bool = True) -> None:
        super().__init__(dsn=dsn, use_sqlite=use_sqlite)

pg_mod.PostgresClient = TestPostgresClient  # type: ignore

# Provide lightweight stubs for modules missing in the test environment
cortex_stub = types.ModuleType("ai_karen_engine.core.cortex.dispatch")

cortex_stub = types.ModuleType("ai_karen_engine.core.cortex.dispatch")

class CortexDispatcher:
    async def dispatch(self, query: str, **kwargs):
        if "hello" in query:
            return {"intent": "greet", "response": "greet"}
        if "time" in query:
            return {"intent": "time_query", "response": "UTC"}
        return {"intent": "hf_generate", "response": query}

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
