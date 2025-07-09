"""
LLMOrchestrator: Nuclear-Grade LLM Routing Engine for Kari
- Zero-trust model routing with cryptographic validation
- Hardware-isolated execution domains (psutil/sched_setaffinity)
- Adaptive load balancing with circuit breakers
- Military-grade observability and audit trails
"""

import os
import logging
import time
import hashlib
import hmac
from typing import Optional, Dict, Any, List, Tuple, Callable, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError, Future
import threading
import random
import sys
import uuid
import traceback

# === LOGGING: One Ring to Rule Them All ===
def _resolve_log_path() -> Path:
    var_log = Path("/var/log/kari")
    try:
        var_log.mkdir(parents=True, exist_ok=True)
        log_file = var_log / "llm_orchestrator.log"
        with open(log_file, "a"):
            pass
        return log_file
    except (PermissionError, OSError):
        xdg_state = os.getenv("XDG_STATE_HOME")
        if xdg_state:
            user_log_dir = Path(xdg_state) / "kari"
        else:
            user_log_dir = Path.home() / ".kari" / "logs"
        user_log_dir.mkdir(parents=True, exist_ok=True)
        log_file = user_log_dir / "llm_orchestrator.log"
        try:
            with open(log_file, "a"):
                pass
        except Exception:
            log_file = Path.cwd() / "llm_orchestrator.log"
        return log_file

LOG_FILE = _resolve_log_path()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("llm_orchestrator")
logger.setLevel(logging.INFO)
logger.info(f"LLM Orchestrator logging initialized. Log file: {LOG_FILE}")

# === Security Constants ===
def get_signing_key() -> str:
    key = os.getenv("KARI_MODEL_SIGNING_KEY")
    if not key:
        raise RuntimeError("KARI_MODEL_SIGNING_KEY must be set in the environment for LLM operations!")
    return key

MAX_CONCURRENT_REQUESTS = int(os.getenv("KARI_MAX_LLM_CONCURRENT", "8"))
REQUEST_TIMEOUT = int(os.getenv("KARI_LLM_TIMEOUT", "60"))
FAILURE_TRIP_LIMIT = int(os.getenv("KARI_LLM_FAIL_LIMIT", "3"))

# === Hardware Isolation: psutil or sched_setaffinity ===
try:
    import psutil
    PSUTIL_ENABLED = True
except ImportError:
    PSUTIL_ENABLED = False

def set_worker_affinity(cpu_id: int):
    try:
        if PSUTIL_ENABLED:
            p = psutil.Process(os.getpid())
            p.cpu_affinity([cpu_id])
            logger.info(f"CPU affinity set via psutil to core {cpu_id}")
        elif hasattr(os, "sched_setaffinity"):
            os.sched_setaffinity(0, {cpu_id})
            logger.info(f"CPU affinity set via sched_setaffinity to core {cpu_id}")
        else:
            logger.warning("No CPU pinning available; running without explicit affinity.")
    except Exception as e:
        logger.warning(f"Failed to set CPU affinity: {e}")

# === Metrics & Observability ===
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
        def set(self, v): pass
    Counter = Histogram = Gauge = _DummyMetric

LLM_ROUTE_COUNT = Counter("llm_orchestrator_requests_total", "LLM routing decisions", ["skill", "model", "status"]) if METRICS_ENABLED else Counter()
LLM_LATENCY = Histogram("llm_orchestrator_latency_seconds", "Request latency", ["model"]) if METRICS_ENABLED else Histogram()
LLM_CIRCUIT_BREAKER = Gauge("llm_orchestrator_circuit_breaker", "Circuit breaker state", ["model"]) if METRICS_ENABLED else Gauge()

# === Model Registry ===
class ModelRegistry:
    """Cryptographically validated model registry with in-memory store and fast locking"""
    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def register(self, model_id: str, model: Any, capabilities: List[str], weight: int = 1, tags: Optional[List[str]]=None):
        with self._lock:
            signature = self._sign_model(model_id, capabilities, weight)
            self._models[model_id] = {
                "model": model,
                "capabilities": capabilities,
                "weight": weight,
                "tags": tags or [],
                "signature": signature,
                "failure_count": 0,
                "last_used": 0,
                "created": time.time()
            }
            logger.info(f"Registered model {model_id} for capabilities: {capabilities}")

    def _sign_model(self, model_id: str, capabilities: List[str], weight: int) -> str:
        msg = f"{model_id}|{','.join(sorted(capabilities))}|{weight}".encode()
        return hmac.new(get_signing_key().encode(), msg, hashlib.sha256).hexdigest()

    def verify_model(self, model_id: str) -> bool:
        with self._lock:
            model = self._models.get(model_id)
            if not model:
                return False
            expected = self._sign_model(model_id, model["capabilities"], model["weight"])
            return hmac.compare_digest(expected, model["signature"])

    def list_models(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(model_id=mid, **m) for mid, m in self._models.items()]

    def get(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._models.get(model_id)

# === Secure Execution Pool ===
class SecureLLMPool:
    """Thread-isolated model execution with circuit breakers and CPU affinity"""
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS)
        self.circuit_breakers: Dict[str, int] = {}  # model_id -> failure count
        self.lock = threading.RLock()
        self.cpu_count = os.cpu_count() or 4

    def execute(self, model_id: str, fn: Callable, *args, **kwargs) -> Future:
        if self._check_circuit(model_id):
            raise RuntimeError(f"Circuit breaker tripped for {model_id}")

        cpu_id = random.randint(0, self.cpu_count - 1)
        job_id = str(uuid.uuid4())[:8]

        def secured_call():
            set_worker_affinity(cpu_id)
            logger.info(f"[{job_id}] Executing {model_id} on CPU {cpu_id}")
            try:
                result = fn(*args, **kwargs)
                self._record_success(model_id)
                logger.info(f"[{job_id}] Model {model_id} execution success.")
                return result
            except Exception as e:
                self._record_failure(model_id)
                logger.error(f"[{job_id}] Model {model_id} execution failed: {e}\n{traceback.format_exc()}")
                raise

        return self.executor.submit(secured_call)
    
    def _check_circuit(self, model_id: str) -> bool:
        with self.lock:
            failures = self.circuit_breakers.get(model_id, 0)
            return failures >= FAILURE_TRIP_LIMIT
    
    def _record_success(self, model_id: str):
        with self.lock:
            self.circuit_breakers[model_id] = 0
            LLM_CIRCUIT_BREAKER.labels(model=model_id).set(0)
    
    def _record_failure(self, model_id: str):
        with self.lock:
            self.circuit_breakers[model_id] = self.circuit_breakers.get(model_id, 0) + 1
            LLM_CIRCUIT_BREAKER.labels(model=model_id).set(1)

    def circuit_status(self, model_id: str) -> int:
        with self.lock:
            return self.circuit_breakers.get(model_id, 0)

# === Core Orchestrator ===
class LLMOrchestrator:
    """
    Military-grade LLM routing engine with:
    - Cryptographic model validation
    - Hardware-isolated execution
    - Adaptive circuit breakers
    - Zero-trust architecture
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
        return cls._instance

    def _init(self):
        self.registry = ModelRegistry()
        self.pool = SecureLLMPool()
        self.watchdog = threading.Thread(
            target=self._monitor_models,
            daemon=True,
            name="LLMOrchestratorWatchdog"
        )
        self.watchdog.start()
        logger.info("LLMOrchestrator initialized in secure mode")

    def _monitor_models(self):
        while True:
            time.sleep(30)
            self._audit_models()

    def _audit_models(self):
        with self._lock:
            for model_id in list(self.registry._models.keys()):
                if not self.registry.verify_model(model_id):
                    logger.critical(f"Model integrity violation: {model_id}")
                    self.registry._models.pop(model_id, None)

    def route_request(
        self,
        prompt: str,
        skill: Optional[str] = None,
        max_tokens: int = 128,
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Secure routing pipeline:
        1. Validate all models
        2. Select optimal model
        3. Execute in isolated environment
        4. Enforce timeouts
        """
        start_time = time.time()
        route = "unrouted"
        model_id = None
        job_id = str(uuid.uuid4())[:8]

        try:
            model_id, model = self._select_model(prompt, skill, max_tokens, user_id)
            if not model_id or not model:
                logger.error(f"[{job_id}] No valid model available for skill={skill}")
                raise RuntimeError("No valid model available")

            route = model_id
            LLM_ROUTE_COUNT.labels(skill=skill or "generic", model=model_id, status="started").inc()
            logger.info(f"[{job_id}] Routing prompt for skill={skill} to model={model_id}")

            with LLM_LATENCY.labels(model=model_id).time():
                future = self.pool.execute(
                    model_id,
                    model["model"].generate_text,
                    prompt,
                    max_tokens=max_tokens,
                    user_id=user_id,
                    **kwargs
                )
                result = future.result(timeout=REQUEST_TIMEOUT)

            LLM_ROUTE_COUNT.labels(skill=skill or "generic", model=model_id, status="success").inc()
            return result

        except TimeoutError:
            LLM_ROUTE_COUNT.labels(skill=skill or "generic", model=model_id or "none", status="timeout").inc()
            logger.error(f"[{job_id}] Request routing timed out for model {model_id}")
            raise
        except Exception as e:
            LLM_ROUTE_COUNT.labels(skill=skill or "generic", model=model_id or "none", status="failed").inc()
            logger.error(f"[{job_id}] Request routing failed: {e}\n{traceback.format_exc()}")
            raise
        finally:
            latency = time.time() - start_time
            logger.info(f"[{job_id}] Request routed to {route} in {latency:.2f}s")

    def _select_model(
        self, prompt: str, skill: Optional[str], max_tokens: int, user_id: Optional[str]=None
    ) -> Tuple[Optional[str], Any]:
        with self._lock:
            candidates = []
            # Priority: direct skill match, then tags, then fallback
            for mid, model in self.registry._models.items():
                if skill and skill in model["capabilities"] and self.registry.verify_model(mid):
                    candidates.append((mid, model))
            if not candidates:
                for mid, model in self.registry._models.items():
                    if "generic" in model["capabilities"] and self.registry.verify_model(mid):
                        candidates.append((mid, model))
            if candidates:
                # Prefer lowest-weight, least-recently-used
                candidates.sort(key=lambda x: (x[1]["weight"], x[1].get("last_used", 0)))
                selected = candidates[0]
                selected[1]["last_used"] = time.time()
                return selected
            return None, None

    def health_check(self) -> Dict[str, Any]:
        status = {
            "status": "unknown",
            "models": {},
            "circuit_breakers": {},
            "integrity_checks": 0
        }
        with self._lock:
            status["integrity_checks"] = sum(
                1 for mid in self.registry._models if self.registry.verify_model(mid)
            )
            for mid, model in self.registry._models.items():
                status["models"][mid] = {
                    "capabilities": model["capabilities"],
                    "tags": model.get("tags", []),
                    "verified": self.registry.verify_model(mid),
                    "failures": model.get("failure_count", 0),
                    "circuit": self.pool.circuit_status(mid),
                    "last_used": model.get("last_used", 0),
                }
            status["status"] = "healthy" if status["integrity_checks"] > 0 else "critical"
        return status

    def audit_log(self) -> List[Dict[str, Any]]:
        # For external review: return a copy of all model registry entries
        return self.registry.list_models()

def get_orchestrator():
    if LLMOrchestrator._instance is None:
        with LLMOrchestrator._lock:
            if LLMOrchestrator._instance is None:
                LLMOrchestrator._instance = LLMOrchestrator()
    return LLMOrchestrator._instance

llm_orchestrator = get_orchestrator()
