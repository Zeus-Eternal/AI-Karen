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
import secrets
import sys
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# === Constants & Configuration ===
DEFAULT_CONFIG = {
    "max_concurrent_requests": 8,
    "request_timeout": 60,
    "failure_trip_limit": 3,
    "watchdog_interval": 30,
    "cpu_reservation": 0.2,  # Reserve 20% CPU capacity
    "memory_threshold": 0.8,  # 80% memory usage threshold
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
    last_used: float = 0.0
    created: float = field(default_factory=time.time)
    status: ModelStatus = ModelStatus.ACTIVE


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
        self.circuit_breakers: Dict[str, int] = {}
        self.lock = threading.RLock()

    def execute(self, model_id: str, fn: Callable, *args, **kwargs) -> Future:
        """Execute function in secure environment"""
        if not self.hardware.check_memory():
            raise RuntimeError("System memory threshold exceeded")

        if self._check_circuit(model_id):
            raise RuntimeError(f"Circuit breaker tripped for {model_id}")

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

    def _check_circuit(self, model_id: str) -> bool:
        """Check if circuit breaker is tripped"""
        with self.lock:
            return (
                self.circuit_breakers.get(model_id, 0)
                >= DEFAULT_CONFIG["failure_trip_limit"]
            )

    def _record_outcome(self, model_id: str, success: bool):
        """Update circuit breaker state"""
        with self.lock:
            if success:
                self.circuit_breakers[model_id] = 0
            else:
                self.circuit_breakers[model_id] = (
                    self.circuit_breakers.get(model_id, 0) + 1
                )


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
            self._setup_watchdog()
            self._initialized = True
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

    def route(self, prompt: str, skill: Optional[str] = None, **kwargs) -> str:
        """Route request to appropriate model"""
        model_id, model = self._select_model(skill)
        if not model:
            raise RuntimeError("No suitable model available")

        try:
            future = self.pool.execute(
                model_id, model.model.generate_text, prompt, **kwargs
            )
            result = future.result(timeout=DEFAULT_CONFIG["request_timeout"])
            self.pool._record_outcome(model_id, True)
            return result
        except Exception as e:
            self.pool._record_outcome(model_id, False)
            logger.error(f"Request failed: {str(e)}")
            raise

    def route_with_copilotkit(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> str:
        """Route request specifically to CopilotKit provider with enhanced context"""
        # Try to get CopilotKit provider first
        copilotkit_model = None
        for model_id, model in self.registry._models.items():
            if "copilotkit" in model_id.lower() and model.status == ModelStatus.ACTIVE:
                copilotkit_model = (model_id, model)
                break

        if not copilotkit_model:
            # Fallback to regular routing if CopilotKit not available
            logger.warning(
                "CopilotKit provider not available, falling back to regular routing"
            )
            return self.route(prompt, **kwargs)

        model_id, model = copilotkit_model

        try:
            # Add conversation context for CopilotKit
            if context:
                kwargs["conversation_context"] = context

            future = self.pool.execute(
                model_id, model.model.generate_text, prompt, **kwargs
            )
            result = future.result(timeout=DEFAULT_CONFIG["request_timeout"])
            self.pool._record_outcome(model_id, True)
            return result
        except Exception as e:
            self.pool._record_outcome(model_id, False)
            logger.error(f"CopilotKit request failed: {str(e)}")
            # Fallback to regular routing
            return self.route(prompt, **kwargs)

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
        """Enhanced routing with CopilotKit code assistance integration"""
        model_id, model = self._select_model(skill)
        if not model:
            raise RuntimeError("No suitable model available")

        try:
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
            logger.error(f"Enhanced request failed: {str(e)}")
            raise

    def _select_model(
        self, skill: Optional[str]
    ) -> Tuple[Optional[str], Optional[ModelInfo]]:
        """Select best model for the task"""
        with self.registry._lock:
            candidates = []

            # First pass: exact skill matches
            if skill:
                candidates.extend(
                    (mid, model)
                    for mid, model in self.registry._models.items()
                    if skill in model.capabilities
                    and model.status == ModelStatus.ACTIVE
                )

            # Second pass: generic models
            if not candidates:
                candidates.extend(
                    (mid, model)
                    for mid, model in self.registry._models.items()
                    if "generic" in model.capabilities
                    and model.status == ModelStatus.ACTIVE
                )

            if candidates:
                # Select least used, lowest weight model
                candidates.sort(key=lambda x: (x[1].weight, x[1].last_used))
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


# === Singleton Access ===
def get_orchestrator() -> LLMOrchestrator:
    """Get the orchestrator instance"""
    return LLMOrchestrator()


llm_orchestrator = get_orchestrator()
