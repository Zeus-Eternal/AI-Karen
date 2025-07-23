"""
OllamaEngine: Sandboxed, In-Process, GGUF-native LLM Engine for Kari AI
- Pure llama-cpp-python (NO REST, NO HTTP)
- Thread-safe model management, sync & async chat, streaming, embeddings
- Prometheus metrics, robust logging, model listing/switch, health check
- Singleton instance for plugin safety. No global sockets or ports.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Generator, AsyncGenerator, Union
from pathlib import Path
import threading

try:
    from llama_cpp import Llama
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

# === Config ===
MODEL_DIR = os.getenv("KARI_MODEL_DIR", "/models")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL_NAME", "llama3.gguf")
DEFAULT_MODEL_PATH = str(Path(MODEL_DIR) / DEFAULT_MODEL)
CTX_SIZE = int(os.getenv("OLLAMA_CTX_SIZE", 4096))
N_THREADS = int(os.getenv("OLLAMA_THREADS", 8))

log = logging.getLogger("ollama_inprocess")
log.setLevel(logging.INFO if os.getenv("ENV") == "production" else logging.DEBUG)

REQ_COUNT = Counter("ollama_requests_total", "Total Ollama LLM Calls", ["model", "method"]) if METRICS_ENABLED else Counter()
REQ_LATENCY = Histogram("ollama_latency_seconds", "Ollama LLM Latency", ["model", "method"]) if METRICS_ENABLED else Histogram()
ERR_COUNT = Counter("ollama_errors_total", "Ollama LLM Errors", ["error_type", "method"]) if METRICS_ENABLED else Counter()
IN_FLIGHT = Gauge("ollama_inflight_requests", "In-Process LLM Calls In Flight", ["method"]) if METRICS_ENABLED else Gauge()

class OllamaEngine:
    """
    In-process, thread-safe LLM engine (singleton)
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
        if getattr(self, "_initialized", False):
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
        """Load GGUF model from disk (thread-safe)"""
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
        """Hot-swap to new model from model dir"""
        model_path = str(Path(MODEL_DIR) / model_name)
        self._load_model(model_path)
        if ctx_size:
            self.ctx_size = ctx_size
        if n_threads:
            self.n_threads = n_threads
        log.info(f"[ollama_inprocess] Switched to model: {model_name}")

    def chat(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Sync chat with streaming support"""
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
        except Exception:
            ERR_COUNT.labels(error_type="inference", method=method).inc()
            log.exception("Ollama LLM error")
            raise
        finally:
            IN_FLIGHT.labels(method=method).dec()

    async def achat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Async chat wrapper with optional streaming."""

        import asyncio

        loop = asyncio.get_event_loop()
        if stream:
            async def generator() -> AsyncGenerator[str, None]:
                chunks = await loop.run_in_executor(
                    None, lambda: list(self.chat(messages, stream=True, **kwargs))
                )
                for ch in chunks:
                    yield ch

            return generator()

        def _run_sync() -> str:
            gen = self.chat(messages, stream=False, **kwargs)
            try:
                return next(gen)
            except StopIteration as ex:  # StopIteration.value contains return
                return ex.value

        return await loop.run_in_executor(None, _run_sync)

    def embedding(self, text: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """Get embedding(s) for text(s), single or batch"""
        try:
            REQ_COUNT.labels(model=self.model_name, method="embedding").inc()
            IN_FLIGHT.labels(method="embedding").inc()
            with REQ_LATENCY.labels(model=self.model_name, method="embedding").time():
                if isinstance(text, str):
                    return self.model.embed(text)
                else:
                    return [self.model.embed(t) for t in text]
        except Exception:
            ERR_COUNT.labels(error_type="embedding", method="embedding").inc()
            log.exception("Ollama embedding error")
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
        """Format role/content messages for llama-cpp-python"""
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
import urllib.request

TINY_LLAMA_URL = "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
TINY_LLAMA_FILENAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

def _download_tinyllama_if_missing():
    model_dir = Path(MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)
    target = model_dir / TINY_LLAMA_FILENAME
    if not target.exists():
        log.info(f"[ollama_inprocess] Downloading TinyLlama GGUF model from {TINY_LLAMA_URL} ...")
        try:
            with urllib.request.urlopen(TINY_LLAMA_URL) as resp, open(target, "wb") as out_file:
                out_file.write(resp.read())
            log.info(f"[ollama_inprocess] Downloaded: {target}")
        except Exception as e:
            log.error(f"[ollama_inprocess] Failed to download TinyLlama: {e}")
            raise

# Inject this call at the start of OllamaEngine.__init__ (before loading any model)
# Just after defining self.model_path ... before self._load_model(self.model_path):
    _download_tinyllama_if_missing()

# Singleton instance for plugin
ollama_inprocess_client = OllamaEngine()

# Simple FastAPI/diagnostics bridge
def health_check() -> Dict[str, Any]:
    return ollama_inprocess_client.health_check()
