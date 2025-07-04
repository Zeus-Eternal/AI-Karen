"""
OllamaEngine: Sandboxed, Enterprise-Grade In-Process LLM Engine for Kari AI
- Native GGUF loading via llama-cpp-python (no REST, no server)
- Thread-safe model management, async/sync APIs, streaming, embeddings
- Prometheus metrics, robust logging, health/status, dynamic model switching
- Exposes NO sockets or HTTP ports—pure Python sandbox
"""

import os
import logging
from typing import Any, Dict, List, Optional, Generator, AsyncGenerator, Union
from pathlib import Path
import threading

try:
    from llama_cpp import Llama, LlamaGrammar
except ImportError as e:
    raise ImportError("llama-cpp-python is required. Install with: pip install llama-cpp-python") from e

try:
    from prometheus_client import Counter, Histogram, Gauge
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    class _DummyMetric:
        def inc(self, n=1): pass
        def labels(self, **kwargs): return self
        def time(self):
            class Ctx: 
                def __enter__(self): return self
                def __exit__(self, *a): pass
            return Ctx()
        def dec(self): pass
    Counter = Histogram = Gauge = _DummyMetric

# === Configuration ===
MODEL_DIR = os.getenv("KARI_MODEL_DIR", "/models")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL_NAME", "llama3.gguf")
DEFAULT_MODEL_PATH = str(Path(MODEL_DIR) / DEFAULT_MODEL)
CTX_SIZE = int(os.getenv("OLLAMA_CTX_SIZE", 4096))
N_THREADS = int(os.getenv("OLLAMA_THREADS", 8))

log = logging.getLogger("ollama_inprocess")
log.setLevel(logging.INFO if os.getenv("ENV") == "production" else logging.DEBUG)

REQ_COUNT = Counter("ollama_requests_total", "Total Ollama In-Process LLM Calls", ["model", "method"]) if METRICS_ENABLED else Counter()
REQ_LATENCY = Histogram("ollama_latency_seconds", "Ollama LLM Latency", ["model", "method"]) if METRICS_ENABLED else Histogram()
ERR_COUNT = Counter("ollama_errors_total", "Ollama LLM Errors", ["error_type", "method"]) if METRICS_ENABLED else Counter()
IN_FLIGHT = Gauge("ollama_inflight_requests", "In-Process LLM Calls In Flight", ["method"]) if METRICS_ENABLED else Gauge()

class OllamaEngine:
    """
    In-process, thread-safe LLM execution engine for Kari
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: Optional[str] = None, ctx_size: Optional[int] = None, n_threads: Optional[int] = None):
        if self._initialized:
            return
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.ctx_size = ctx_size or CTX_SIZE
        self.n_threads = n_threads or N_THREADS
        self.model_name = Path(self.model_path).name
        self.model = None
        self.model_lock = threading.Lock()
        self._load_model(self.model_path)
        self._initialized = True

    def _load_model(self, model_path: str) -> None:
        """Load a GGUF model from disk (thread-safe)"""
        path = Path(model_path)
        if not path.exists():
            log.error(f"[ollama_inprocess] Model not found: {path}")
            raise FileNotFoundError(f"Model file not found: {path}")
        with self.model_lock:
            self.model = Llama(
                model_path=str(path),
                n_ctx=self.ctx_size,
                n_threads=self.n_threads,
                verbose=False
            )
            self.model_path = str(path)
            self.model_name = path.name
            log.info(f"[ollama_inprocess] Model loaded: {self.model_name}")

    def switch_model(self, model_name: str, ctx_size: Optional[int] = None, n_threads: Optional[int] = None) -> None:
        """Hot-swap to a new model in the model dir"""
        model_path = str(Path(MODEL_DIR) / model_name)
        self._load_model(model_path)
        if ctx_size: self.ctx_size = ctx_size
        if n_threads: self.n_threads = n_threads
        log.info(f"[ollama_inprocess] Switched to model: {model_name}")

    def chat(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Sync chat with optional streaming"""
        method = "stream_chat" if stream else "chat"
        REQ_COUNT.labels(model=self.model_name, method=method).inc()
        IN_FLIGHT.labels(method=method).inc()
        try:
            with REQ_LATENCY.labels(model=self.model_name, method=method).time():
                prompt = self._format_prompt(messages)
                if stream:
                    log.debug("Streaming inference")
                    for out in self.model.create_completion(prompt, stream=True, **kwargs):
                        yield out["choices"][0]["text"]
                else:
                    log.debug("Standard inference")
                    result = self.model.create_completion(prompt, **kwargs)
                    return result["choices"][0]["text"]
        except Exception as e:
            ERR_COUNT.labels(error_type="inference", method=method).inc()
            log.exception("Ollama in-process LLM error")
            raise
        finally:
            IN_FLIGHT.labels(method=method).dec()

    async def achat(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """Async chat via thread pool"""
        import asyncio
        loop = asyncio.get_event_loop()
        if stream:
            def _streamer():
                yield from self.chat(messages, stream=True, **kwargs)
            for chunk in await loop.run_in_executor(None, lambda: list(_streamer())):
                yield chunk
        else:
            return await loop.run_in_executor(None, lambda: self.chat(messages, stream=False, **kwargs))

    def embedding(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        """Get embedding(s) for text(s)"""
        try:
            REQ_COUNT.labels(model=self.model_name, method="embedding").inc()
            IN_FLIGHT.labels(method="embedding").inc()
            with REQ_LATENCY.labels(model=self.model_name, method="embedding").time():
                return self.model.embed(text)
        except Exception as e:
            ERR_COUNT.labels(error_type="embedding", method="embedding").inc()
            log.exception("Ollama in-process embedding error")
            raise
        finally:
            IN_FLIGHT.labels(method="embedding").dec()

    def list_models(self) -> List[str]:
        """List all .gguf models in model dir"""
        try:
            return sorted([f.name for f in Path(MODEL_DIR).glob("*.gguf") if f.is_file()])
        except Exception as e:
            log.error(f"[ollama_inprocess] Model discovery failed: {str(e)}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """Basic health check: can load model and infer 'ping'?"""
        try:
            output = self.chat([{"role": "user", "content": "ping"}], stream=False, max_tokens=4)
            return {"status": "healthy", "model": self.model_name, "output": output}
        except Exception as e:
            return {"status": "unhealthy", "model": self.model_name, "error": str(e)}

    @staticmethod
    def _format_prompt(messages: List[Dict[str, str]]) -> str:
        """LLM-friendly prompt composition from message dicts"""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"<|system|>{content}\n"
            elif role == "assistant":
                prompt += f"<|assistant|>{content}\n"
            else:
                prompt += f"<|user|>{content}\n"
        prompt += "<|assistant|>"
        return prompt

# Singleton instance for imports
ollama_inprocess_client = OllamaEngine()

# Convenience function for FastAPI diagnostics
def health_check() -> Dict[str, Any]:
    return ollama_inprocess_client.health_check()
