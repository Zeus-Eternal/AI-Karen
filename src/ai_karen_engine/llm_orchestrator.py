"""
LLMOrchestrator: Nuclear-Grade LLM Routing Engine for Kari
- Zero-trust model routing with cryptographic validation
- Hardware-isolated execution domains (psutil/sched_setaffinity)
- Adaptive load balancing with circuit breakers
- Military-grade observability and audit trails
- Enhanced with failover strategies and resource monitoring
"""

import hashlib
import hmac
import importlib.util
import logging
import os
import random
import re
import secrets
import sys
import textwrap
import threading
import time
import uuid
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

from ai_karen_engine.core.errors.exceptions import RateLimitError


# === Constants & Configuration ===
DEFAULT_CONFIG = {
    "max_concurrent_requests": 8,
    "request_timeout": 60,
    "failure_trip_limit": 3,
    "watchdog_interval": 30,
    "cpu_reservation": 0.2,  # Reserve 20% CPU capacity
    "memory_threshold": 0.8,  # 80% memory usage threshold
    "circuit_base_delay": 2.0,
    "circuit_max_delay": 60.0,
    "rate_limit_base_delay": 5.0,
    "rate_limit_max_delay": 180.0,
    "max_rate_limit_queue": 256,
}


# === Enhanced Logging ===
class SecureLogger:
    """Logging with redaction and secure handling"""

    REDACTION_KEYS = {"api_key", "token", "password", "secret"}

    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        log_file = self._resolve_log_path()
        logger = logging.getLogger("llm_orchestrator")
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S%z",
        )

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(self._security_filter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(self._security_filter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _security_filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from logs"""
        try:
            msg = record.getMessage()
            for sensitive in self.REDACTION_KEYS:
                if sensitive in msg.lower():
                    record.msg = "[REDACTED]"
                    record.args = ()
                    break
        except Exception:
            pass
        return True

    def _resolve_log_path(self) -> Path:
        """Resolve log file path with fallbacks"""
        paths = [
            os.getenv("KARI_LOG_DIR"),
            "/var/log/kari",
            Path.home() / ".kari" / "logs",
        ]

        for path in paths:
            if not path:
                continue
            try:
                log_dir = Path(path)
                log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
                log_file = log_dir / "llm_orchestrator.log"
                log_file.touch(exist_ok=True)
                os.chmod(log_file, 0o600)
                return log_file
            except (OSError, PermissionError):
                continue

        raise RuntimeError("Could not establish secure logging location")


logger = SecureLogger().logger


# === Security Core ===
class SecurityEngine:
    """Centralized security operations"""

    def __init__(self):
        self._signing_key = self._load_signing_key()

    def _load_signing_key(self) -> bytes:
        """Load and validate signing key

        Falls back to an ephemeral key in non-production environments if the
        environment variable is missing. This is intended only for local
        development; production environments must always provide a valid key.
        """
        key = os.getenv("KARI_MODEL_SIGNING_KEY")
        if key:
            if len(key) < 32:
                raise RuntimeError(
                    "KARI_MODEL_SIGNING_KEY must be at least 32 characters long"
                )
            return key.encode("utf-8")

        env = os.getenv("KARI_ENV", "local").lower()
        if env == "production":
            raise RuntimeError(
                "KARI_MODEL_SIGNING_KEY is required in production environments"
            )

        logger.warning(
            "KARI_MODEL_SIGNING_KEY not set; generating ephemeral key for development."
            " Do NOT use this in production."
        )
        return secrets.token_bytes(32)

    def generate_signature(self, *parts: str) -> str:
        """Generate HMAC-SHA256 signature"""
        message = "|".join(parts).encode("utf-8")
        return hmac.new(self._signing_key, message, hashlib.sha256).hexdigest()

    def verify_signature(self, signature: str, *parts: str) -> bool:
        """Verify HMAC-SHA256 signature"""
        expected = self.generate_signature(*parts)
        return hmac.compare_digest(signature, expected)


# === Hardware Isolation ===
class HardwareManager:
    """Manage hardware resources and isolation"""

    def __init__(self):
        self.cpu_count = self._detect_cpu_count()
        self.psutil_available = self._check_psutil()

    def _detect_cpu_count(self) -> int:
        """Get available CPU count with safety margin"""
        total = os.cpu_count() or 4
        reserved = max(1, int(total * DEFAULT_CONFIG["cpu_reservation"]))
        return max(1, total - reserved)

    def _check_psutil(self) -> bool:
        """Check if psutil is available"""
        try:
            return importlib.util.find_spec("psutil") is not None
        except Exception:
            return False

    def set_affinity(self, cpu_id: int) -> bool:
        """Set CPU affinity for current thread"""
        try:
            if self.psutil_available:
                import psutil

                p = psutil.Process(os.getpid())
                p.cpu_affinity([cpu_id])
            elif hasattr(os, "sched_setaffinity"):
                os.sched_setaffinity(0, {cpu_id})
            else:
                return False
            return True
        except Exception as e:
            logger.warning(f"CPU affinity setting failed: {e}")
            return False

    def check_memory(self) -> bool:
        """Check if memory usage is within safe thresholds"""
        try:
            if self.psutil_available:
                import psutil

                mem = psutil.virtual_memory()
                return mem.percent < (DEFAULT_CONFIG["memory_threshold"] * 100)
            return True
        except Exception:
            return True


# === Model Definitions ===
class ModelStatus(Enum):
    ACTIVE = auto()
    DEGRADED = auto()
    RATE_LIMITED = auto()
    FAILED = auto()
    CIRCUIT_BROKEN = auto()


@dataclass
class ModelInfo:
    model_id: str
    model: Any
    capabilities: List[str]
    weight: int = 1
    tags: List[str] = field(default_factory=list)
    signature: str = ""
    failure_count: int = 0
    consecutive_failures: int = 0
    last_used: float = 0.0
    created: float = field(default_factory=time.time)
    status: ModelStatus = ModelStatus.ACTIVE
    latency_samples: List[float] = field(default_factory=list)
    warmed: bool = False
    cooldown_until: float = 0.0
    rate_limit_until: float = 0.0
    last_error: Optional[str] = None
    degradation_notes: List[str] = field(default_factory=list)

    def record_latency(self, latency: float, max_samples: int = 50) -> None:
        self.latency_samples.append(latency)
        if len(self.latency_samples) > max_samples:
            self.latency_samples.pop(0)

    def p95_latency(self) -> float:
        if not self.latency_samples:
            return float("inf")
        samples = sorted(self.latency_samples)
        idx = max(0, int(0.95 * (len(samples) - 1)))
        return samples[idx]


# === Circuit Breaker State ===


class CircuitOpenError(RuntimeError):
    """Raised when attempting to use a model whose circuit breaker is open."""

    def __init__(
        self,
        model_id: str,
        retry_after: float,
        reason: str = "",
        rate_limited: bool = False,
    ) -> None:
        message = (
            f"Circuit open for model {model_id}. Retry after {retry_after:.2f}s"
        )
        if reason:
            message = f"{message} (reason: {reason})"
        super().__init__(message)
        self.model_id = model_id
        self.retry_after = retry_after
        self.reason = reason
        self.rate_limited = rate_limited


@dataclass
class CircuitState:
    failure_count: int = 0
    opened_until: float = 0.0
    last_failure: float = 0.0
    reason: str = ""
    rate_limited: bool = False
    retry_after: float = 0.0

    def is_open(self) -> bool:
        if self.opened_until <= 0:
            return False
        return time.time() < self.opened_until

    def remaining(self) -> float:
        return max(0.0, self.opened_until - time.time())


# === Enhanced Model Registry ===
class ModelRegistry:
    """Secure model registry with enhanced management"""

    def __init__(self, security: SecurityEngine):
        self._models: Dict[str, ModelInfo] = {}
        self._lock = threading.RLock()
        self.security = security

    def register(self, model_id: str, model: Any, capabilities: List[str], **kwargs):
        """Register a new model with cryptographic validation"""
        with self._lock:
            if model_id in self._models:
                raise ValueError(f"Model {model_id} already registered")

            signature = self._generate_signature(
                model_id, capabilities, kwargs.get("weight", 1)
            )
            self._models[model_id] = ModelInfo(
                model_id=model_id,
                model=model,
                capabilities=capabilities,
                signature=signature,
                **kwargs,
            )
            logger.info(
                f"Registered model {model_id} with capabilities: {capabilities}"
            )

    def _generate_signature(
        self, model_id: str, capabilities: List[str], weight: int
    ) -> str:
        """Generate cryptographic signature for model"""
        return self.security.generate_signature(
            model_id, ",".join(sorted(capabilities)), str(weight)
        )

    def verify(self, model_id: str) -> bool:
        """Verify model integrity"""
        with self._lock:
            if model_id not in self._models:
                return False
            model = self._models[model_id]
            expected = self._generate_signature(
                model_id, model.capabilities, model.weight
            )
            return hmac.compare_digest(expected, model.signature)

    def get(self, model_id: str) -> Optional[ModelInfo]:
        """Get model info if it exists and is valid"""
        with self._lock:
            if model_id in self._models and self.verify(model_id):
                return self._models[model_id]
            return None

    def list_models(self) -> List[Dict[str, Any]]:
        """Get list of all valid models"""
        with self._lock:
            return [
                {
                    "model_id": model.model_id,
                    "capabilities": model.capabilities,
                    "tags": model.tags,
                    "status": model.status.name,
                    "last_used": model.last_used,
                    "failure_count": model.failure_count,
                }
                for model in self._models.values()
                if self.verify(model.model_id)
            ]


# === Execution Pool with Enhanced Features ===
class ExecutionPool:
    """Secure execution environment with resource management"""

    def __init__(self, hardware: HardwareManager):
        self.hardware = hardware
        self.executor = ThreadPoolExecutor(
            max_workers=DEFAULT_CONFIG["max_concurrent_requests"],
            thread_name_prefix="llm_worker",
        )
        self.circuit_states: Dict[str, CircuitState] = {}
        self.lock = threading.RLock()

    def execute(self, model_id: str, fn: Callable, *args, **kwargs) -> Future:
        """Execute function in secure environment"""
        if not self.hardware.check_memory():
            raise RuntimeError("System memory threshold exceeded")

        state = self._check_circuit(model_id)
        if state:
            raise CircuitOpenError(
                model_id,
                state.remaining(),
                reason=state.reason,
                rate_limited=state.rate_limited,
            )

        cpu_id = random.randint(0, self.hardware.cpu_count - 1)
        job_id = str(uuid.uuid4())[:8]

        def _wrapped():
            try:
                self.hardware.set_affinity(cpu_id)
                logger.info(f"[{job_id}] Executing on CPU {cpu_id}")
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"[{job_id}] Execution failed: {str(e)}")
                raise
            finally:
                logger.info(f"[{job_id}] Execution completed")

        future = self.executor.submit(_wrapped)
        future.model_id = model_id  # type: ignore
        future.job_id = job_id  # type: ignore
        return future

    def _check_circuit(self, model_id: str) -> Optional[CircuitState]:
        """Return circuit state if breaker is currently open."""
        with self.lock:
            state = self.circuit_states.get(model_id)
            if not state:
                return None
            if state.is_open():
                return state
            # Circuit is no longer open; reset transient flags
            if state.rate_limited:
                state.rate_limited = False
                state.reason = ""
                state.retry_after = 0.0
            if state.failure_count == 0:
                return None
            return None

    def _record_outcome(
        self, model_id: str, success: bool, error: Optional[Exception] = None
    ) -> None:
        """Update circuit breaker state with exponential backoff handling."""

        with self.lock:
            state = self.circuit_states.setdefault(model_id, CircuitState())
            if success:
                state.failure_count = 0
                state.opened_until = 0.0
                state.reason = ""
                state.rate_limited = False
                state.retry_after = 0.0
                return

            state.failure_count += 1
            state.last_failure = time.time()

            reason = str(error) if error else "Unknown failure"
            state.reason = reason

            base_delay = DEFAULT_CONFIG.get("circuit_base_delay", 2.0)
            max_delay = DEFAULT_CONFIG.get("circuit_max_delay", 60.0)
            exponent = min(state.failure_count - 1, 6)
            jitter = random.uniform(0, base_delay)
            delay = min(max_delay, base_delay * (2 ** exponent)) + jitter

            retry_after = getattr(error, "retry_after", None)
            is_rate_limited = isinstance(error, RateLimitError) or (
                isinstance(reason, str) and "rate limit" in reason.lower()
            )
            if is_rate_limited:
                rate_base = DEFAULT_CONFIG.get("rate_limit_base_delay", base_delay)
                delay = max(delay, rate_base)
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except (TypeError, ValueError):
                        pass
                delay = min(
                    DEFAULT_CONFIG.get("rate_limit_max_delay", max_delay), delay
                )
                state.rate_limited = True
            else:
                state.rate_limited = False

            state.retry_after = delay
            state.opened_until = time.time() + delay


# === Core Orchestrator ===
class LLMOrchestrator:
    """Enhanced LLM routing engine with failover strategies"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.__init__()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.security = SecurityEngine()
            self.hardware = HardwareManager()
            self.registry = ModelRegistry(self.security)
            self.pool = ExecutionPool(self.hardware)
            queue_size = int(DEFAULT_CONFIG.get("max_rate_limit_queue", 256))
            self._rate_limit_queue: Deque[Dict[str, Any]] = deque(maxlen=queue_size)
            self._degraded_events: Deque[Dict[str, Any]] = deque(maxlen=64)
            self._setup_watchdog()
            self._initialized = True
            self._preload_providers()
            logger.info("LLMOrchestrator initialized in secure mode")

    def _setup_watchdog(self):
        """Start monitoring thread"""

        def _monitor():
            while True:
                time.sleep(DEFAULT_CONFIG["watchdog_interval"])
                self._audit_models()

        thread = threading.Thread(
            target=_monitor, daemon=True, name="orchestrator-watchdog"
        )
        thread.start()

    def _audit_models(self):
        """Periodically verify all models"""
        with self.registry._lock:
            for model_id in list(self.registry._models.keys()):
                if not self.registry.verify(model_id):
                    logger.warning(f"Model integrity check failed: {model_id}")
                    del self.registry._models[model_id]

    def _preload_providers(self) -> None:
        """Initialize providers at startup and warm their caches."""
        from ai_karen_engine.integrations.provider_registry import (
            ModelInfo as ProviderModelInfo,
            get_provider_registry,
        )

        registry = get_provider_registry()
        for provider_name in registry.list_providers():
            info = registry.get_provider_info(provider_name)
            if not info:
                continue
            models: List[ProviderModelInfo] = info.models or []
            if not models:
                default_name = info.default_model or provider_name
                models = [ProviderModelInfo(name=default_name, capabilities=["generic"])]
            for m in models:
                try:
                    provider = registry.get_provider(provider_name, model=m.name)
                    model_id = f"{provider_name}:{m.name}"
                    capabilities = m.capabilities or ["generic"]
                    register_kwargs = {}
                    if provider_name.lower() == "fallback":
                        # Ensure fallback provider is always tried last
                        register_kwargs["weight"] = 100
                        register_kwargs["tags"] = ["fallback", "deterministic"]
                    self.registry.register(
                        model_id,
                        provider,
                        capabilities,
                        **register_kwargs,
                    )
                    latency = self._warm_model(model_id, provider)
                    if latency is not None:
                        info = self.registry._models.get(model_id)
                        if info:
                            info.warmed = True
                            info.record_latency(latency)
                except Exception as e:  # pragma: no cover - warmup is best effort
                    logger.warning(f"Provider preload failed for {provider_name}:{m.name}: {e}")

        # Register local models as fallback
        self._register_local_models()
        # Ensure we always have a deterministic fallback available
        self._ensure_fallback_provider()

    def _ensure_fallback_provider(self) -> None:
        """Guarantee that a deterministic fallback model is available."""
        try:
            from ai_karen_engine.integrations.providers.fallback_provider import (
                FallbackProvider,
            )
        except Exception as exc:  # pragma: no cover - import should always succeed
            logger.error("Failed to import fallback provider: %s", exc)
            return

        fallback_provider = FallbackProvider()
        fallback_model_id = f"fallback:{fallback_provider.model}"
        fallback_caps = ["generic", "conversation", "text"]

        # If already registered, refresh the instance to keep it healthy
        with self.registry._lock:
            existing = self.registry._models.get(fallback_model_id)
            if existing:
                existing.model = fallback_provider
                existing.status = ModelStatus.ACTIVE
                existing.tags = list({*existing.tags, "fallback", "offline"})
                logger.debug("Refreshed fallback provider instance")
                return

        try:
            self.registry.register(
                fallback_model_id,
                fallback_provider,
                fallback_caps,
                weight=1,
                tags=["fallback", "offline"],
            )
            logger.info("Registered deterministic fallback provider")
        except ValueError:
            # Another thread may have registered it concurrently; refresh and exit
            with self.registry._lock:
                existing = self.registry._models.get(fallback_model_id)
                if existing:
                    existing.model = fallback_provider
                    existing.status = ModelStatus.ACTIVE
                    existing.tags = list({*existing.tags, "fallback", "offline"})
            return

        latency = self._warm_model(fallback_model_id, fallback_provider)
        if latency is not None:
            info = self.registry._models.get(fallback_model_id)
            if info:
                info.warmed = True
                info.record_latency(latency)

    def _register_local_models(self) -> None:
        """Register local models as fallback options."""
        try:
            from pathlib import Path
            from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime
            
            # Check if llama-cpp-python is available
            if not LlamaCppRuntime.is_available():
                logger.debug("llama-cpp-python not available, skipping local model registration")
                return
            
            # Discover any local GGUF models dynamically
            models_dir = Path("models/llama-cpp")
            ggufs = []
            if models_dir.exists():
                try:
                    ggufs = [p for p in models_dir.glob("*.gguf") if p.is_file()]
                    # Basic validity: header magic
                    valid = []
                    for p in ggufs:
                        try:
                            with open(p, "rb") as f:
                                if f.read(4) == b"GGUF":
                                    valid.append(p)
                        except Exception:
                            continue
                    ggufs = valid
                except Exception:
                    ggufs = []

            if ggufs:
                ggufs.sort(key=lambda p: p.stat().st_size, reverse=True)
                chosen = ggufs[0]
                logger.info(f"Registering local GGUF model: {chosen}")
                
                class LocalGGUFProvider:
                    def __init__(self, path: str):
                        self.runtime = None
                        self.model_path = path
                    
                    def generate_text(self, prompt: str, **kwargs) -> str:
                        if not self.runtime:
                            self.runtime = LlamaCppRuntime(
                                model_path=self.model_path,
                                n_ctx=2048,
                                n_batch=512,
                                n_gpu_layers=0,
                                verbose=False
                            )
                        
                        response = self.runtime.generate(
                            prompt=prompt,
                            max_tokens=kwargs.get("max_tokens", 256),
                            temperature=kwargs.get("temperature", 0.7),
                            top_p=kwargs.get("top_p", 0.9),
                            stream=False
                        )
                        return response if isinstance(response, str) else str(response)
                    
                    def generate_response(self, prompt: str, **kwargs) -> str:
                        return self.generate_text(prompt, **kwargs)
                    
                    def enhanced_generate_response(self, prompt: str, **kwargs) -> str:
                        return self.generate_text(prompt, **kwargs)
                # Register the local model
                local_provider = LocalGGUFProvider(str(chosen))
                model_id = f"local:{chosen.name}"
                capabilities = ["generic", "conversation", "text"]
                self.registry.register(model_id, local_provider, capabilities, weight=10, tags=["local", "fallback"])
                logger.info(f"Successfully registered local model: {model_id}")
            else:
                logger.debug("No local GGUF models found under models/llama-cpp/")
                
        except Exception as e:
            logger.warning(f"Failed to register local models: {e}")

    def _warm_model(self, model_id: str, provider: Any) -> Optional[float]:
        """Warm a model and return latency in seconds if successful."""
        start = time.time()
        try:
            if hasattr(provider, "warm_cache"):
                provider.warm_cache()
            else:  # Fallback minimal generation
                provider.generate_text("hello", max_tokens=1)
            latency = time.time() - start
            logger.info(f"Warmed {model_id} in {latency:.3f}s")
            return latency
        except Exception as e:
            logger.warning(f"Warmup failed for {model_id}: {e}")
            return None

    def _track_latency(self, model_id: str, latency: float) -> None:
        info = self.registry._models.get(model_id)
        if info:
            info.record_latency(latency)
            info.warmed = True

    def route(self, prompt: str, skill: Optional[str] = None, **kwargs) -> str:
        """Route request to appropriate model with advanced fallback handling."""

        return self._route_request(
            prompt,
            skill,
            mode="text",
            context=None,
            **kwargs,
        )

    def route_with_copilotkit(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> str:
        """Route request specifically to CopilotKit provider with enhanced context."""

        return self._route_request(
            prompt,
            None,
            mode="copilotkit",
            context=context,
            **kwargs,
        )

    async def enhanced_route(
        self, prompt: str, skill: Optional[str] = None, **kwargs
    ) -> str:
        """Enhanced routing with instruction-aware providers and fallback orchestration."""

        return self._route_request(
            prompt,
            skill,
            mode="enhanced",
            context=None,
            **kwargs,
        )

    def _route_request(
        self,
        prompt: str,
        skill: Optional[str],
        *,
        mode: str,
        context: Optional[Dict[str, Any]],
        **kwargs,
    ) -> str:
        """Core routing pipeline with retry, backoff, and degraded-mode handling."""

        attempted_models: List[str] = []
        last_error: Optional[Exception] = None
        preferred_models: Deque[str] = deque()

        if mode == "copilotkit":
            with self.registry._lock:
                for mid, info in self.registry._models.items():
                    if "copilotkit" in mid.lower() and self._model_ready(mid, info):
                        preferred_models.append(mid)

        while True:
            if preferred_models:
                candidate_id = preferred_models.popleft()
                if candidate_id in attempted_models:
                    continue
                with self.registry._lock:
                    model = self.registry._models.get(candidate_id)
                    if not model or not self._model_ready(candidate_id, model):
                        continue
                model_id = candidate_id
            else:
                model_id, model = self._select_model(skill)

            if not model or model_id in attempted_models:
                break

            attempted_models.append(model_id)
            self._log_request_event(
                "attempt",
                model_id,
                prompt,
                mode=mode,
                metadata={"skill": skill},
            )

            try:
                return self._execute_model(
                    model_id,
                    model,
                    prompt,
                    mode=mode,
                    context=context,
                    **kwargs,
                )
            except CircuitOpenError as circuit_error:
                last_error = circuit_error
                self._log_request_event(
                    "circuit_open",
                    model_id,
                    prompt,
                    mode=mode,
                    metadata={
                        "retry_after": circuit_error.retry_after,
                        "reason": circuit_error.reason,
                        "rate_limited": circuit_error.rate_limited,
                    },
                )
                self._handle_circuit_open(model_id, model, circuit_error)
            except RateLimitError as rate_limit_error:
                last_error = rate_limit_error
                self._log_request_event(
                    "rate_limited",
                    model_id,
                    prompt,
                    mode=mode,
                    metadata={
                        "retry_after": getattr(rate_limit_error, "retry_after", None),
                        "error": str(rate_limit_error),
                    },
                )
                self._handle_rate_limit(model_id, model, rate_limit_error, prompt)
            except Exception as generic_error:
                last_error = generic_error
                error_text = str(generic_error)
                lower_error = error_text.lower()
                rate_limit_keywords = (
                    "rate limit",
                    "quota",
                    "too many requests",
                    "429",
                )

                if any(keyword in lower_error for keyword in rate_limit_keywords):
                    synthetic_error = RateLimitError(message=error_text)
                    retry_hint = getattr(generic_error, "retry_after", None)
                    if retry_hint is None:
                        retry_hint = self._extract_retry_after(error_text)
                    if retry_hint is not None:
                        try:
                            setattr(synthetic_error, "retry_after", float(retry_hint))
                        except (TypeError, ValueError):
                            pass
                    self._log_request_event(
                        "rate_limited",
                        model_id,
                        prompt,
                        mode=mode,
                        metadata={
                            "retry_after": getattr(synthetic_error, "retry_after", None),
                            "error": error_text,
                        },
                    )
                    self._handle_rate_limit(model_id, model, synthetic_error, prompt)
                    continue

                self._log_request_event(
                    "failure",
                    model_id,
                    prompt,
                    mode=mode,
                    metadata={
                        "error": error_text,
                        "exception": generic_error.__class__.__name__,
                    },
                )
                self._handle_model_failure(model_id, model, generic_error)

        return self._generate_degraded_response(prompt, attempted_models, last_error)

    def _execute_model(
        self,
        model_id: str,
        model: ModelInfo,
        prompt: str,
        *,
        mode: str,
        context: Optional[Dict[str, Any]],
        **kwargs,
    ) -> str:
        """Execute a provider call with instrumentation and recovery handling."""

        if hasattr(model.model, "is_loaded") and not model.model.is_loaded():
            logger.warning(
                "Model %s not loaded, attempting to load before execution", model_id
            )
            if hasattr(model.model, "load_model"):
                model.model.load_model()
            elif hasattr(model.model, "runtime") and getattr(model.model, "runtime") is None:
                logger.info("Initializing runtime for %s before retry", model_id)
                raise CircuitOpenError(
                    model_id,
                    DEFAULT_CONFIG.get("circuit_base_delay", 2.0),
                    "runtime initialization",
                )

        provider_kwargs = dict(kwargs)
        if mode == "copilotkit" and context:
            provider_kwargs.setdefault("conversation_context", context)

        if mode == "enhanced" and hasattr(model.model, "enhanced_generate_response"):
            target_fn = model.model.enhanced_generate_response
        elif hasattr(model.model, "generate_response"):
            target_fn = model.model.generate_response
        elif hasattr(model.model, "generate_text"):
            target_fn = model.model.generate_text
        else:
            raise RuntimeError(f"Model {model_id} does not implement a generation method")

        start = time.time()

        try:
            future = self.pool.execute(model_id, target_fn, prompt, **provider_kwargs)
            result = future.result(timeout=DEFAULT_CONFIG["request_timeout"])
        except CircuitOpenError:
            raise
        except Exception as exec_error:
            self.pool._record_outcome(model_id, False, exec_error)
            raise

        self.pool._record_outcome(model_id, True)
        latency = time.time() - start
        self._track_latency(model_id, latency)
        self._handle_model_recovery(model_id, model)
        self._log_request_event(
            "success",
            model_id,
            prompt,
            mode=mode,
            metadata={"latency": round(latency, 3)},
        )
        return result

    def _log_request_event(
        self,
        event_type: str,
        model_id: str,
        prompt: str,
        *,
        mode: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit structured logs for routing events with redacted prompt context."""

        payload: Dict[str, Any] = {
            "event": event_type,
            "model": model_id,
            "mode": mode,
            "prompt_digest": self._sanitize_prompt(prompt),
        }
        if metadata:
            payload.update({k: v for k, v in metadata.items() if v is not None})
        logger.info("[LLM_ROUTER] %s", payload)

    def _handle_model_recovery(self, model_id: str, model: ModelInfo) -> None:
        """Reset model health metadata after a successful request."""

        if model.status != ModelStatus.ACTIVE:
            logger.info(
                "Model %s recovered from %s state", model_id, model.status.name
            )
        model.status = ModelStatus.ACTIVE
        model.cooldown_until = 0.0
        model.rate_limit_until = 0.0
        model.consecutive_failures = 0
        model.last_error = None

    def _handle_model_failure(
        self, model_id: str, model: ModelInfo, error: Exception
    ) -> None:
        """Apply exponential backoff and circuit logic for generic failures."""

        now = time.time()
        reason = str(error)
        model.failure_count += 1
        model.consecutive_failures += 1
        model.last_error = reason

        note = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))}: {reason}"[:256]
        model.degradation_notes.append(note)
        if len(model.degradation_notes) > 10:
            model.degradation_notes.pop(0)

        base_delay = DEFAULT_CONFIG.get("circuit_base_delay", 2.0)
        max_delay = DEFAULT_CONFIG.get("circuit_max_delay", 60.0)
        exponent = min(model.consecutive_failures, 6)
        jitter = random.uniform(0.5, base_delay)
        cooldown = min(max_delay, base_delay * (2 ** exponent)) + jitter

        model.cooldown_until = now + cooldown
        logger.warning(
            "Model %s entering degraded state for %.2fs due to: %s",
            model_id,
            cooldown,
            reason,
        )

        if model.consecutive_failures >= DEFAULT_CONFIG["failure_trip_limit"]:
            model.status = ModelStatus.CIRCUIT_BROKEN
        else:
            model.status = ModelStatus.DEGRADED

        if model.failure_count >= DEFAULT_CONFIG["failure_trip_limit"] * 2:
            model.status = ModelStatus.FAILED

    def _handle_rate_limit(
        self,
        model_id: str,
        model: ModelInfo,
        error: RateLimitError,
        prompt: str,
    ) -> None:
        """Special handling for rate limiting errors with queue management."""

        now = time.time()
        retry_after = getattr(error, "retry_after", None)
        parsed_retry = self._extract_retry_after(str(error)) if retry_after is None else retry_after

        base_delay = DEFAULT_CONFIG.get("rate_limit_base_delay", 5.0)
        cooldown = float(base_delay)
        if parsed_retry is not None:
            try:
                cooldown = max(cooldown, float(parsed_retry))
            except (TypeError, ValueError):
                cooldown = max(cooldown, base_delay)

        cooldown = min(
            DEFAULT_CONFIG.get("rate_limit_max_delay", 180.0),
            cooldown + random.uniform(0.5, 1.5),
        )

        model.status = ModelStatus.RATE_LIMITED
        model.rate_limit_until = now + cooldown
        model.cooldown_until = model.rate_limit_until
        model.consecutive_failures += 1
        model.failure_count += 1
        model.last_error = str(error)

        self._record_rate_limit_event(
            model_id,
            cooldown,
            self._sanitize_prompt(prompt),
            str(error),
        )

        logger.warning(
            "Rate limit triggered for %s; retrying after %.2fs", model_id, cooldown
        )

    def _handle_circuit_open(
        self, model_id: str, model: ModelInfo, error: CircuitOpenError
    ) -> None:
        """Handle attempts on models with open circuits."""

        cooldown = max(error.retry_after, DEFAULT_CONFIG.get("circuit_base_delay", 2.0))
        model.cooldown_until = time.time() + cooldown
        model.consecutive_failures += 1
        if error.rate_limited:
            model.status = ModelStatus.RATE_LIMITED
            model.rate_limit_until = model.cooldown_until
        else:
            model.status = ModelStatus.CIRCUIT_BROKEN
        if error.reason:
            model.last_error = error.reason
        logger.debug(
            "Circuit open for %s; delaying retries for %.2fs", model_id, cooldown
        )

    def _record_rate_limit_event(
        self, model_id: str, retry_after: float, prompt_digest: str, message: str
    ) -> None:
        """Add a rate limiting event to the in-memory queue for monitoring."""

        event = {
            "model_id": model_id,
            "retry_after": round(retry_after, 2),
            "timestamp": time.time(),
            "prompt_digest": prompt_digest,
            "message": message[:256],
        }
        self._rate_limit_queue.append(event)

    def _extract_retry_after(self, message: str) -> Optional[float]:
        """Best-effort extraction of retry-after values from provider errors."""

        if not message:
            return None

        retry_after_match = re.search(r"retry[- ]?after[:\s]*(\d+(?:\.\d+)?)", message, re.I)
        if retry_after_match:
            try:
                return float(retry_after_match.group(1))
            except ValueError:
                return None

        seconds_match = re.search(r"(\d+(?:\.\d+)?)\s*(seconds|sec|s)\b", message, re.I)
        if seconds_match:
            try:
                return float(seconds_match.group(1))
            except ValueError:
                return None

        return None

    def _sanitize_prompt(self, prompt: str) -> str:
        """Return a stable digest of the prompt for logging without raw text."""

        if not prompt:
            return ""
        cleaned = " ".join(prompt.strip().split())
        return hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:12]

    def _get_fallback_model(self) -> Optional[Tuple[str, ModelInfo]]:
        """Retrieve the deterministic fallback provider if available."""

        with self.registry._lock:
            for model_id, info in self.registry._models.items():
                if model_id.startswith("fallback:") or "fallback" in info.tags:
                    return model_id, info
        return None

    def _generate_degraded_response(
        self,
        prompt: str,
        attempted_models: List[str],
        last_error: Optional[Exception],
    ) -> str:
        """Generate a graceful degraded response when all providers fail."""

        reason = str(last_error) if last_error else "Unknown provider failure"
        attempted = attempted_models or ["<none>"]
        logger.error(
            "All providers failed; entering degraded mode. Attempted: %s | Reason: %s",
            attempted,
            reason,
        )

        event = {
            "timestamp": time.time(),
            "attempted_models": list(attempted),
            "reason": reason[:256],
            "prompt_digest": self._sanitize_prompt(prompt),
        }
        self._degraded_events.append(event)

        fallback_entry = self._get_fallback_model()
        if fallback_entry:
            fallback_id, fallback_model = fallback_entry
            fallback_prompt = textwrap.dedent(
                f"""
                The primary LLM providers failed with the following reason: {reason}.
                Provide a supportive acknowledgement and summarize the user's prompt below.

                User prompt:
                {prompt}
                """
            ).strip()
            try:
                response = fallback_model.model.generate_text(fallback_prompt)
                self._log_request_event(
                    "fallback_success",
                    fallback_id,
                    prompt,
                    mode="degraded",
                    metadata={"original_models": attempted},
                )
                return response
            except Exception as fallback_error:
                logger.error(
                    "Fallback provider %s failed during degraded mode: %s",
                    fallback_id,
                    fallback_error,
                )

        self._log_request_event(
            "fallback_rule_based",
            "rule_based",
            prompt,
            mode="degraded",
            metadata={"original_models": attempted},
        )
        return self._build_rule_based_response(prompt, attempted, reason)

    def _build_rule_based_response(
        self, prompt: str, attempted_models: List[str], reason: str
    ) -> str:
        """Create a deterministic acknowledgement message as ultimate fallback."""

        summary = textwrap.shorten(" ".join(prompt.split()), width=200, placeholder="…") if prompt else "(empty request)"
        attempted = ", ".join(attempted_models)
        guidance = [
            "Retry in a few minutes or switch to a different provider in settings.",
            "Review provider API keys and quotas to ensure availability.",
        ]

        return (
            "⚠️ I'm in degraded mode because I couldn't reach the configured language models.\n"
            f"Models attempted: {attempted}.\n"
            f"Last error: {reason}.\n\n"
            "Here's what I can offer right now:\n"
            f"- {guidance[0]}\n"
            f"- {guidance[1]}\n\n"
            f"Your request summary: {summary}"
        )

    async def get_code_suggestions(
        self, code: str, language: str = "python", **kwargs
    ) -> List[Dict[str, Any]]:
        """Get code suggestions from CopilotKit provider or enhanced providers"""
        # First try CopilotKit provider
        copilotkit_model = None
        for model_id, model in self.registry._models.items():
            if "copilotkit" in model_id.lower() and model.status == ModelStatus.ACTIVE:
                copilotkit_model = (model_id, model)
                break

        if copilotkit_model:
            model_id, model = copilotkit_model
            try:
                if hasattr(model.model, "get_code_suggestions"):
                    return await model.model.get_code_suggestions(
                        code, language, **kwargs
                    )
            except Exception as e:
                logger.warning(f"CopilotKit code suggestions failed: {e}")

        # Fallback to any provider with code assistance capabilities
        for model_id, model in self.registry._models.items():
            if model.status == ModelStatus.ACTIVE:
                try:
                    if hasattr(model.model, "get_code_suggestions"):
                        return await model.model.get_code_suggestions(
                            code, language, **kwargs
                        )
                except Exception as e:
                    logger.debug(f"Provider {model_id} code suggestions failed: {e}")
                    continue

        logger.warning("No providers available for code suggestions")
        return []

    async def get_debugging_assistance(
        self, code: str, error_message: str = "", language: str = "python", **kwargs
    ) -> Dict[str, Any]:
        """Get debugging assistance from enhanced providers"""
        # Try providers with debugging assistance capabilities
        for model_id, model in self.registry._models.items():
            if model.status == ModelStatus.ACTIVE:
                try:
                    if hasattr(model.model, "get_debugging_assistance"):
                        return await model.model.get_debugging_assistance(
                            code=code,
                            error_message=error_message,
                            language=language,
                            **kwargs,
                        )
                except Exception as e:
                    logger.debug(
                        f"Provider {model_id} debugging assistance failed: {e}"
                    )
                    continue

        logger.warning("No providers available for debugging assistance")
        return {"suggestions": [], "analysis": "No debugging assistance available"}

    async def generate_documentation(
        self,
        code: str,
        language: str = "python",
        style: str = "comprehensive",
        **kwargs,
    ) -> str:
        """Generate documentation using enhanced providers"""
        # Try providers with documentation generation capabilities
        for model_id, model in self.registry._models.items():
            if model.status == ModelStatus.ACTIVE:
                try:
                    if hasattr(model.model, "generate_documentation"):
                        return await model.model.generate_documentation(
                            code=code, language=language, style=style, **kwargs
                        )
                except Exception as e:
                    logger.debug(
                        f"Provider {model_id} documentation generation failed: {e}"
                    )
                    continue

        logger.warning("No providers available for documentation generation")
        return f"Documentation generation unavailable for {language} code"

    async def get_contextual_suggestions(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> List[Dict[str, Any]]:
        """Get contextual suggestions from CopilotKit provider or enhanced providers"""
        # First try CopilotKit provider
        copilotkit_model = None
        for model_id, model in self.registry._models.items():
            if "copilotkit" in model_id.lower() and model.status == ModelStatus.ACTIVE:
                copilotkit_model = (model_id, model)
                break

        if copilotkit_model:
            model_id, model = copilotkit_model
            try:
                if hasattr(model.model, "get_contextual_suggestions"):
                    return await model.model.get_contextual_suggestions(
                        message, context, **kwargs
                    )
            except Exception as e:
                logger.warning(f"CopilotKit contextual suggestions failed: {e}")

        # Fallback to any provider with contextual suggestions capabilities
        for model_id, model in self.registry._models.items():
            if model.status == ModelStatus.ACTIVE:
                try:
                    if hasattr(model.model, "get_contextual_suggestions"):
                        return await model.model.get_contextual_suggestions(
                            message, context, **kwargs
                        )
                except Exception as e:
                    logger.debug(
                        f"Provider {model_id} contextual suggestions failed: {e}"
                    )
                    continue

        logger.warning("No providers available for contextual suggestions")
        return []

    async def enhanced_route(
        self, prompt: str, skill: Optional[str] = None, **kwargs
    ) -> str:
        """Enhanced routing with CopilotKit code assistance integration and automatic fallback"""
        # Try multiple models in order of preference
        attempted_models = []
        
        while True:
            model_id, model = self._select_model(skill)
            if not model or model_id in attempted_models:
                break
                
            attempted_models.append(model_id)
            
            try:
                # Check if model is properly loaded
                if hasattr(model.model, 'is_loaded') and not model.model.is_loaded():
                    logger.warning(f"Model {model_id} not loaded, attempting to load...")
                    if hasattr(model.model, 'load_model'):
                        model.model.load_model()
                    elif hasattr(model.model, 'runtime') and model.model.runtime is None:
                        # For models that need runtime initialization
                        logger.info(f"Initializing runtime for {model_id}")
                        continue  # Skip this model and try next
                
                # Use enhanced response generation if available
                if hasattr(model.model, "enhanced_generate_response"):
                    future = self.pool.execute(
                        model_id, model.model.enhanced_generate_response, prompt, **kwargs
                    )
                else:
                    # Fallback to regular generation
                    future = self.pool.execute(
                        model_id, model.model.generate_response, prompt, **kwargs
                    )

                result = future.result(timeout=DEFAULT_CONFIG["request_timeout"])
                self.pool._record_outcome(model_id, True)
                return result
                
            except Exception as e:
                self.pool._record_outcome(model_id, False)
                logger.warning(f"Enhanced model {model_id} failed: {str(e)}, trying next model...")
                
                # Mark this model as temporarily unavailable
                model.status = ModelStatus.CIRCUIT_BROKEN
                continue
        
        # All models failed
        raise RuntimeError(f"All available models failed. Attempted: {attempted_models}")

    def _model_ready(
        self, model_id: str, model: ModelInfo, *, now: Optional[float] = None
    ) -> bool:
        """Determine if a model is available for routing, updating status if recovered."""

        if now is None:
            now = time.time()
        if model.status == ModelStatus.ACTIVE:
            return True
        if model.status == ModelStatus.FAILED:
            return False
        if model.cooldown_until and model.cooldown_until <= now:
            logger.info(
                "Model %s exiting %s state after cooldown", model_id, model.status.name
            )
            model.status = ModelStatus.ACTIVE
            model.cooldown_until = 0.0
            model.rate_limit_until = 0.0
            model.consecutive_failures = 0
            return True
        return False

    def _select_model(
        self, skill: Optional[str]
    ) -> Tuple[Optional[str], Optional[ModelInfo]]:
        """Select best model for the task respecting cooldowns and statuses."""

        now = time.time()

        with self.registry._lock:
            def _candidate_filter(predicate: Callable[[ModelInfo], bool]):
                return [
                    (mid, model)
                    for mid, model in self.registry._models.items()
                    if predicate(model) and self._model_ready(mid, model, now=now)
                ]

            candidates: List[Tuple[str, ModelInfo]] = []
            if skill:
                candidates = _candidate_filter(lambda m: skill in m.capabilities)

            if not candidates:
                candidates = _candidate_filter(lambda m: "generic" in m.capabilities)

            if candidates:
                warmed = [c for c in candidates if c[1].warmed]
                if warmed:
                    candidates = warmed
                candidates.sort(
                    key=lambda x: (
                        x[1].p95_latency(),
                        x[1].weight,
                        x[1].last_used,
                    )
                )
                selected = candidates[0]
                selected[1].last_used = time.time()
                return selected

            return None, None

    def health_check(self) -> Dict[str, Any]:
        """System health status"""
        return {
            "status": "operational",
            "models": len(self.registry._models),
            "active_workers": self.pool.executor._work_queue.qsize(),
            "memory_ok": self.hardware.check_memory(),
            "timestamp": time.time(),
        }
    
    def reset_circuit_breakers(self) -> None:
        """Reset circuit breakers for all models to allow retry"""
        with self.registry._lock:
            for model_id, model in self.registry._models.items():
                if model.status == ModelStatus.CIRCUIT_BROKEN:
                    model.status = ModelStatus.ACTIVE
                    logger.info(f"Reset circuit breaker for model: {model_id}")
    
    def get_model_status(self) -> Dict[str, str]:
        """Get status of all registered models"""
        with self.registry._lock:
            return {
                model_id: model.status.value 
                for model_id, model in self.registry._models.items()
            }


# === Singleton Access ===
_llm_orchestrator: Optional[LLMOrchestrator] = None


def get_orchestrator() -> LLMOrchestrator:
    """Get (or create) the orchestrator singleton."""
    global _llm_orchestrator
    if _llm_orchestrator is None:
        _llm_orchestrator = LLMOrchestrator()
    return _llm_orchestrator
