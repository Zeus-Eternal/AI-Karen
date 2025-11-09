"""
Capsule Orchestrator - Lifecycle Management and Execution

Coordinates capsule discovery, validation, execution, and integration
with CORTEX intent mapping system.

Research Alignment:
- Kubernetes Orchestration Patterns
- Circuit Breaker Pattern (for failure isolation)
- Bulkhead Pattern (for resource isolation)
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List
import threading

from ai_karen_engine.capsules.registry import get_capsule_registry, CapsuleRegistryError
from ai_karen_engine.capsules.base_capsule import (
    BaseCapsule,
    CapsuleExecutionError,
    CapsuleValidationError,
)
from ai_karen_engine.capsules.schemas import CapsuleResult, CapsuleType

logger = logging.getLogger(__name__)

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram

    CAPSULE_EXECUTIONS = Counter(
        "capsule_executions_total",
        "Total capsule executions",
        ["capsule_id", "status"],
    )
    CAPSULE_EXECUTION_TIME = Histogram(
        "capsule_execution_seconds",
        "Capsule execution time",
        ["capsule_id"],
    )
except ImportError:
    # Fallback for when Prometheus not available
    class _DummyMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

    CAPSULE_EXECUTIONS = _DummyMetric()
    CAPSULE_EXECUTION_TIME = _DummyMetric()


class CapsuleOrchestrator:
    """
    Orchestrates capsule lifecycle and execution.

    Responsibilities:
    - Initialize and discover capsules
    - Route intents to capsules
    - Manage execution with observability
    - Integrate with CORTEX dispatch
    - Circuit breaking and failure isolation
    """

    _instance: Optional['CapsuleOrchestrator'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.registry = get_capsule_registry()
        self._intent_map: Dict[str, str] = {}  # intent -> capsule_id
        self._capability_map: Dict[str, List[str]] = {}  # capability -> [capsule_ids]
        self._circuit_breakers: Dict[str, Dict] = {}  # capsule_id -> breaker state
        self._metrics = {
            "executions_total": 0,
            "executions_success": 0,
            "executions_failed": 0,
        }
        self._initialized = True

        logger.info("Capsule orchestrator initialized")

    def initialize(self, auto_discover: bool = True) -> None:
        """
        Initialize the orchestrator and discover capsules.

        Args:
            auto_discover: Automatically discover capsules on init
        """
        if auto_discover:
            discovered = self.registry.discover()
            logger.info(f"Auto-discovered {discovered} capsules")

            # Build intent and capability maps
            self._build_maps()

    def _build_maps(self) -> None:
        """Build intent and capability mapping for CORTEX integration"""
        self._intent_map.clear()
        self._capability_map.clear()

        for capsule_id in self.registry.list_capsules():
            try:
                manifest = self.registry.get_manifest(capsule_id)

                # Map capsule ID to itself as an intent
                self._intent_map[capsule_id] = capsule_id

                # Map each capability to the capsule
                for capability in manifest.capabilities:
                    if capability not in self._capability_map:
                        self._capability_map[capability] = []
                    self._capability_map[capability].append(capsule_id)

                logger.debug(f"Mapped capsule {capsule_id} with {len(manifest.capabilities)} capabilities")

            except Exception as e:
                logger.warning(f"Failed to map capsule {capsule_id}: {e}")

        logger.info(
            f"Intent mapping complete: {len(self._intent_map)} intents, "
            f"{len(self._capability_map)} capabilities"
        )

    def execute_capsule(
        self,
        capsule_id: str,
        request: Dict[str, Any],
        user_ctx: Dict[str, Any],
        correlation_id: Optional[str] = None,
        memory_context: Optional[List[Dict[str, Any]]] = None,
    ) -> CapsuleResult:
        """
        Execute a capsule by ID.

        Args:
            capsule_id: Capsule identifier
            request: Request payload
            user_ctx: User context
            correlation_id: Optional correlation ID (generated if not provided)
            memory_context: Optional memory context

        Returns:
            CapsuleResult

        Raises:
            CapsuleExecutionError: On execution failure
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        # Check circuit breaker
        if self._is_circuit_open(capsule_id):
            raise CapsuleExecutionError(
                f"Circuit breaker open for capsule: {capsule_id}"
            )

        start_time = time.time()

        try:
            # Get capsule instance
            capsule = self.registry.get_capsule(capsule_id)

            # Execute
            result = capsule.execute(
                request=request,
                user_ctx=user_ctx,
                correlation_id=correlation_id,
                memory_context=memory_context,
            )

            # Record metrics
            execution_time = time.time() - start_time
            self._record_success(capsule_id, execution_time)

            CAPSULE_EXECUTIONS.labels(capsule_id=capsule_id, status="success").inc()
            CAPSULE_EXECUTION_TIME.labels(capsule_id=capsule_id).observe(execution_time)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self._record_failure(capsule_id)

            CAPSULE_EXECUTIONS.labels(capsule_id=capsule_id, status="failure").inc()

            logger.error(
                f"Capsule execution failed: {capsule_id}",
                extra={"correlation_id": correlation_id, "error": str(e)},
            )
            raise CapsuleExecutionError(f"Capsule execution failed: {e}") from e

    def execute_by_capability(
        self,
        capability: str,
        request: Dict[str, Any],
        user_ctx: Dict[str, Any],
        correlation_id: Optional[str] = None,
        memory_context: Optional[List[Dict[str, Any]]] = None,
    ) -> CapsuleResult:
        """
        Execute a capsule by capability (uses first available capsule).

        Args:
            capability: Capability identifier
            request: Request payload
            user_ctx: User context
            correlation_id: Optional correlation ID
            memory_context: Optional memory context

        Returns:
            CapsuleResult

        Raises:
            CapsuleExecutionError: If no capsule found or execution fails
        """
        if capability not in self._capability_map:
            raise CapsuleExecutionError(f"No capsule found for capability: {capability}")

        # Get first available capsule (future: add load balancing/priority)
        capsule_id = self._capability_map[capability][0]

        return self.execute_capsule(
            capsule_id=capsule_id,
            request=request,
            user_ctx=user_ctx,
            correlation_id=correlation_id,
            memory_context=memory_context,
        )

    def resolve_intent(self, intent: str) -> Optional[str]:
        """
        Resolve intent to capsule ID for CORTEX integration.

        Args:
            intent: Intent string

        Returns:
            Capsule ID if found, None otherwise
        """
        return self._intent_map.get(intent)

    def list_capabilities(self) -> List[str]:
        """Get list of all available capabilities"""
        return list(self._capability_map.keys())

    def list_capsules_for_capability(self, capability: str) -> List[str]:
        """Get list of capsules providing a capability"""
        return self._capability_map.get(capability, [])

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        return {
            **self._metrics,
            "registry": self.registry.get_metrics(),
            "circuit_breakers": {
                cid: state["failures"]
                for cid, state in self._circuit_breakers.items()
            },
        }

    def _is_circuit_open(self, capsule_id: str) -> bool:
        """Check if circuit breaker is open for capsule"""
        if capsule_id not in self._circuit_breakers:
            self._circuit_breakers[capsule_id] = {
                "failures": 0,
                "last_failure": None,
                "open": False,
            }
            return False

        state = self._circuit_breakers[capsule_id]

        # Check if circuit should be reset (5 minute cooldown)
        if state["open"] and state["last_failure"]:
            if time.time() - state["last_failure"] > 300:  # 5 minutes
                state["open"] = False
                state["failures"] = 0
                logger.info(f"Circuit breaker reset for capsule: {capsule_id}")

        return state["open"]

    def _record_success(self, capsule_id: str, execution_time: float) -> None:
        """Record successful execution"""
        self._metrics["executions_total"] += 1
        self._metrics["executions_success"] += 1

        # Reset circuit breaker on success
        if capsule_id in self._circuit_breakers:
            self._circuit_breakers[capsule_id]["failures"] = 0
            self._circuit_breakers[capsule_id]["open"] = False

    def _record_failure(self, capsule_id: str) -> None:
        """Record failed execution and update circuit breaker"""
        self._metrics["executions_total"] += 1
        self._metrics["executions_failed"] += 1

        if capsule_id not in self._circuit_breakers:
            self._circuit_breakers[capsule_id] = {
                "failures": 0,
                "last_failure": None,
                "open": False,
            }

        state = self._circuit_breakers[capsule_id]
        state["failures"] += 1
        state["last_failure"] = time.time()

        # Open circuit after 5 consecutive failures
        if state["failures"] >= 5:
            state["open"] = True
            logger.warning(f"Circuit breaker opened for capsule: {capsule_id}")

    def reload_capsules(self) -> None:
        """Reload all capsules and rebuild maps"""
        logger.info("Reloading capsules...")
        self.registry.reload_all()
        self._build_maps()
        logger.info("Capsule reload complete")


# Singleton instance
_orchestrator: Optional[CapsuleOrchestrator] = None


def get_capsule_orchestrator() -> CapsuleOrchestrator:
    """Get or create the global capsule orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CapsuleOrchestrator()
    return _orchestrator


__all__ = [
    "CapsuleOrchestrator",
    "get_capsule_orchestrator",
]
