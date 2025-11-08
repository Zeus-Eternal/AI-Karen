"""
BaseCapsule Abstract Class - Production Standards

Base interface that all capsule implementations must inherit from.
Provides standardized lifecycle, validation, and execution patterns.

Research Alignment:
- Gang of Four Template Method Pattern
- SOLID Principles (Interface Segregation, Dependency Inversion)
"""

import abc
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from ai_karen_engine.capsules.schemas import (
    CapsuleManifest,
    CapsuleContext,
    CapsuleResult,
)
from ai_karen_engine.capsules.security_common import (
    sanitize_dict_values,
    validate_prompt_safety,
    validate_allowed_tools,
    PromptSecurityError,
)

logger = logging.getLogger(__name__)


class CapsuleExecutionError(Exception):
    """Base exception for capsule execution failures"""
    pass


class CapsuleValidationError(Exception):
    """Exception for capsule validation failures"""
    pass


class BaseCapsule(abc.ABC):
    """
    Abstract base class for all Kari AI capsules.

    Capsules are self-contained cognitive skill modules with:
    - Manifest-driven configuration
    - Zero-trust security validation
    - Standardized I/O contracts
    - Built-in observability
    - Hardware isolation support

    Subclasses must implement:
    - _execute_core(): Core business logic
    - Optional: _pre_execution_hook(), _post_execution_hook()
    """

    def __init__(self, capsule_dir: Path):
        """
        Initialize capsule from directory containing manifest and resources.

        Args:
            capsule_dir: Path to capsule directory
        """
        self.capsule_dir = Path(capsule_dir)
        self.manifest: Optional[CapsuleManifest] = None
        self.prompt_template: Optional[str] = None
        self.execution_lock = threading.Lock()
        self._initialized = False

        # Load and validate manifest
        self._load_manifest()
        self._load_prompt()
        self._validate_structure()
        self._initialized = True

        logger.info(f"Capsule '{self.manifest.id}' initialized successfully")

    def _load_manifest(self) -> None:
        """Load and validate manifest using Pydantic schema"""
        manifest_path = self.capsule_dir / "manifest.yaml"

        if not manifest_path.exists():
            raise CapsuleValidationError(f"Manifest not found: {manifest_path}")

        try:
            with open(manifest_path, "r") as f:
                manifest_data = yaml.safe_load(f)

            # Validate using Pydantic
            self.manifest = CapsuleManifest(**manifest_data)

        except Exception as e:
            raise CapsuleValidationError(f"Manifest validation failed: {e}")

    def _load_prompt(self) -> None:
        """Load prompt template if specified"""
        if not self.manifest.prompt_file:
            self.prompt_template = None
            return

        prompt_path = self.capsule_dir / self.manifest.prompt_file

        if not prompt_path.exists():
            raise CapsuleValidationError(f"Prompt file not found: {prompt_path}")

        try:
            self.prompt_template = prompt_path.read_text(encoding="utf-8")

            # Validate prompt length
            max_length = 8192  # Standard max
            if len(self.prompt_template) > max_length:
                raise CapsuleValidationError(
                    f"Prompt template exceeds max length: {len(self.prompt_template)} > {max_length}"
                )

        except Exception as e:
            raise CapsuleValidationError(f"Prompt load failed: {e}")

    def _validate_structure(self) -> None:
        """Validate capsule directory structure"""
        required_files = [self.manifest.entrypoint]

        for file in required_files:
            file_path = self.capsule_dir / file
            if not file_path.exists():
                raise CapsuleValidationError(f"Required file not found: {file}")

    @abc.abstractmethod
    def _execute_core(self, context: CapsuleContext) -> Any:
        """
        Core execution logic - must be implemented by subclasses.

        Args:
            context: Validated and sanitized execution context

        Returns:
            Execution result (any type)

        Raises:
            CapsuleExecutionError: On execution failure
        """
        pass

    def _pre_execution_hook(self, context: CapsuleContext) -> None:
        """
        Optional pre-execution hook for setup tasks.

        Args:
            context: Execution context
        """
        pass

    def _post_execution_hook(self, result: Any, context: CapsuleContext) -> None:
        """
        Optional post-execution hook for cleanup tasks.

        Args:
            result: Execution result
            context: Execution context
        """
        pass

    def _validate_rbac(self, user_ctx: Dict[str, Any]) -> None:
        """
        Validate user has required roles for capsule execution.

        Args:
            user_ctx: User context with roles

        Raises:
            CapsuleExecutionError: If RBAC validation fails
        """
        user_roles = set(user_ctx.get("roles", []))
        required_roles = set(self.manifest.required_roles)

        if not user_roles.issuperset(required_roles):
            missing_roles = required_roles - user_roles
            raise CapsuleExecutionError(
                f"Insufficient privileges. Missing roles: {missing_roles}"
            )

    def _sanitize_input(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize input request using security common module.

        Args:
            request: Raw request data

        Returns:
            Sanitized request

        Raises:
            CapsuleExecutionError: If sanitization fails
        """
        try:
            return sanitize_dict_values(request, max_length=8192)
        except PromptSecurityError as e:
            raise CapsuleExecutionError(f"Input sanitization failed: {e}")

    def _enforce_timeout(self) -> None:
        """
        Enforce execution timeout from security policy.

        Note: This is a placeholder - actual timeout enforcement
        should be handled at the orchestrator level.
        """
        max_time = self.manifest.security_policy.max_execution_time
        logger.debug(f"Capsule max execution time: {max_time}s")

    def execute(
        self,
        request: Dict[str, Any],
        user_ctx: Dict[str, Any],
        correlation_id: str,
        memory_context: Optional[List[Dict[str, Any]]] = None,
    ) -> CapsuleResult:
        """
        Main execution entry point with full security and observability.

        This method implements the template method pattern, calling:
        1. RBAC validation
        2. Input sanitization
        3. Pre-execution hook
        4. Core execution (_execute_core)
        5. Post-execution hook
        6. Result packaging

        Args:
            request: Request payload
            user_ctx: User context (must include 'roles')
            correlation_id: Correlation ID for tracing
            memory_context: Optional memory context

        Returns:
            CapsuleResult with standardized output

        Raises:
            CapsuleExecutionError: On execution failure
        """
        if not self._initialized:
            raise CapsuleExecutionError("Capsule not initialized")

        start_time = time.time()

        try:
            with self.execution_lock:
                # Phase 1: RBAC Validation
                self._validate_rbac(user_ctx)

                # Phase 2: Input Sanitization
                sanitized_request = self._sanitize_input(request)

                # Phase 3: Build Context
                context = CapsuleContext(
                    user_ctx=user_ctx,
                    request=sanitized_request,
                    correlation_id=correlation_id,
                    memory_context=memory_context,
                )

                # Phase 4: Pre-execution Hook
                self._pre_execution_hook(context)

                # Phase 5: Core Execution
                result = self._execute_core(context)

                # Phase 6: Post-execution Hook
                self._post_execution_hook(result, context)

                # Phase 7: Package Result
                execution_time = time.time() - start_time

                return CapsuleResult(
                    result=result,
                    metadata={
                        "capsule_id": self.manifest.id,
                        "capsule_version": self.manifest.version,
                        "execution_time": execution_time,
                    },
                    security={
                        "correlation_id": correlation_id,
                        "user": user_ctx.get("sub", "unknown"),
                    },
                    metrics={
                        "execution_time_seconds": execution_time,
                    },
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Capsule '{self.manifest.id}' execution failed: {e}",
                extra={"correlation_id": correlation_id},
            )
            raise CapsuleExecutionError(f"Execution failed: {e}") from e

    def get_manifest(self) -> CapsuleManifest:
        """Get capsule manifest"""
        return self.manifest

    def get_capabilities(self) -> list[str]:
        """Get capsule capabilities"""
        return self.manifest.capabilities

    def get_id(self) -> str:
        """Get capsule ID"""
        return self.manifest.id

    def get_version(self) -> str:
        """Get capsule version"""
        return self.manifest.version

    def __repr__(self) -> str:
        return f"<Capsule id={self.manifest.id} version={self.manifest.version}>"


__all__ = [
    "BaseCapsule",
    "CapsuleExecutionError",
    "CapsuleValidationError",
]
