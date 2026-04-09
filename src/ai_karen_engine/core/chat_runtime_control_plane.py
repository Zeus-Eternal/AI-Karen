"""
Chat Runtime Control Plane Service
Central authority for managing chat runtime modes and maintenance states.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from contextlib import asynccontextmanager

from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.database.models import (
    SystemRuntimeState,
    MaintenanceWindow,
    MaintenanceNotificationRequest,
    RuntimeDependencyHealth,
    ChatRuntimeEvent,
    AuthUser,
)
from ai_karen_engine.database.client import MultiTenantPostgresClient

logger = get_logger(__name__)


class RuntimeMode(str, Enum):
    """Runtime mode enumeration."""

    NORMAL = "normal"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    EMERGENCY_FALLBACK = "emergency_fallback"


class DependencyStatus(str, Enum):
    """Dependency health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class MaintenanceResponse:
    """Structured maintenance response."""

    mode: str = "maintenance"
    message: str = "System is currently undergoing maintenance"
    estimated_completion_time: Optional[datetime] = None
    notification_supported: bool = True
    notification_request_allowed: bool = True
    retry_after_seconds: int = 300
    system_status_code: int = 503


@dataclass
class EmergencyFallbackResponse:
    """Emergency fallback response."""

    mode: str = "emergency_fallback"
    message: str = "Service temporarily unavailable"
    retry_after_seconds: int = 60
    system_status_code: int = 503


@dataclass
class DependencyHealth:
    """Dependency health information."""

    name: str
    status: DependencyStatus
    reason: Optional[str] = None
    checked_at: datetime = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()


class ChatRuntimeControlPlane(BaseService):
    """
    Central authority for chat runtime mode management and maintenance control.

    This service implements the runtime control plane requirements:
    - Single authoritative source for runtime state
    - Deterministic mode transitions
    - Maintenance override precedence
    - Dependency readiness validation
    """

    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="chat_runtime_control_plane"))

        # Runtime state
        self._current_mode: RuntimeMode = RuntimeMode.NORMAL
        self._maintenance_window: Optional[MaintenanceWindow] = None
        self._dependency_health: Dict[str, DependencyHealth] = {}

        # Configuration
        self._dependency_check_interval = 30  # seconds
        self._maintenance_recheck_interval = 60  # seconds
        self._health_stabilization_threshold = 3  # consecutive successes
        self._mode_transition_cooldown = 30  # seconds

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._maintenance_monitor_task: Optional[asyncio.Task] = None
        self._last_mode_transition: datetime = datetime.utcnow()

    async def initialize(self) -> None:
        """Initialize the runtime control plane."""
        logger.info("Initializing Chat Runtime Control Plane")

        # Load current state from database
        await self._load_runtime_state()

        # Start background monitoring
        await self._start_background_tasks()

        logger.info(
            f"Chat Runtime Control Plane initialized with mode: {self._current_mode}"
        )

    async def shutdown(self) -> None:
        """Shutdown the runtime control plane."""
        logger.info("Shutting down Chat Runtime Control Plane")

        # Stop background tasks
        await self._stop_background_tasks()

        logger.info("Chat Runtime Control Plane shutdown complete")

    # Core Runtime Mode Management

    async def get_current_mode(self) -> RuntimeMode:
        """Get the current runtime mode."""
        return self._current_mode

    async def transition_mode(self, new_mode: RuntimeMode, reason: str) -> bool:
        """Transition to a new runtime mode."""
        if new_mode == self._current_mode:
            return True

        # Validate transition
        if not self._is_valid_transition(self._current_mode, new_mode):
            logger.warning(
                f"Invalid mode transition: {self._current_mode} -> {new_mode}"
            )
            return False

        # Check cooldown
        if (
            datetime.utcnow() - self._last_mode_transition
        ).seconds < self._mode_transition_cooldown:
            logger.warning("Mode transition too soon after previous transition")
            return False

        # Perform transition
        old_mode = self._current_mode
        self._current_mode = new_mode
        self._last_mode_transition = datetime.utcnow()

        # Persist state
        await self._persist_runtime_state(reason)

        # Log transition
        await self._log_runtime_event("mode_transition", new_mode.value, reason)

        logger.info(
            f"Runtime mode transition: {old_mode.value} -> {new_mode.value} ({reason})"
        )
        return True

    def _is_valid_transition(
        self, from_mode: RuntimeMode, to_mode: RuntimeMode
    ) -> bool:
        """Validate if a mode transition is allowed."""
        # Allow all transitions to emergency_fallback
        if to_mode == RuntimeMode.EMERGENCY_FALLBACK:
            return True

        # Allow transitions from any mode to maintenance
        if to_mode == RuntimeMode.MAINTENANCE:
            return True

        # Allow maintenance to exit to normal or degraded
        if from_mode == RuntimeMode.MAINTENANCE:
            return to_mode in (RuntimeMode.NORMAL, RuntimeMode.DEGRADED)

        # Allow normal <-> degraded transitions
        if from_mode in (RuntimeMode.NORMAL, RuntimeMode.DEGRADED):
            return to_mode in (RuntimeMode.NORMAL, RuntimeMode.DEGRADED)

        return False

    # Maintenance Management

    async def enable_maintenance(
        self,
        reason: str,
        message: str,
        estimated_completion_time: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ) -> bool:
        """Enable maintenance mode."""
        try:
            db_client = MultiTenantPostgresClient()
            async with db_client.get_session() as session:
                # Create maintenance window
                maintenance = MaintenanceWindow(
                    enabled=True,
                    reason=reason,
                    message=message,
                    estimated_completion_time=estimated_completion_time,
                    started_at=datetime.utcnow(),
                    created_by=created_by,
                    updated_by=created_by,
                )

                session.add(maintenance)
                await session.commit()
                await session.refresh(maintenance)

                self._maintenance_window = maintenance

                # Transition to maintenance mode
                await self.transition_mode(
                    RuntimeMode.MAINTENANCE, f"Maintenance enabled: {reason}"
                )

                logger.info(f"Maintenance mode enabled: {reason}")
                return True

        except Exception as e:
            logger.error(f"Failed to enable maintenance: {e}")
            return False

    async def disable_maintenance(self, updated_by: Optional[str] = None) -> bool:
        """Disable maintenance mode."""
        try:
            if not self._maintenance_window:
                return True

            db_client = MultiTenantPostgresClient()
            async with db_client.get_session() as session:
                # Update maintenance window
                stmt = (
                    update(MaintenanceWindow)
                    .where(MaintenanceWindow.id == self._maintenance_window.id)
                    .values(
                        enabled=False, ended_at=datetime.utcnow(), updated_by=updated_by
                    )
                )
                await session.execute(stmt)
                await session.commit()

                self._maintenance_window = None

                # Determine next mode based on readiness
                next_mode = await self._determine_optimal_mode()
                await self.transition_mode(next_mode, "Maintenance disabled")

                logger.info("Maintenance mode disabled")
                return True

        except Exception as e:
            logger.error(f"Failed to disable maintenance: {e}")
            return False

    # Dependency Health Management

    async def check_dependency_health(self, dependency_name: str) -> DependencyHealth:
        """Check health of a specific dependency."""
        # This is a placeholder - implement actual health checks
        health = DependencyHealth(
            name=dependency_name,
            status=DependencyStatus.HEALTHY,
            reason="Health check not implemented",
        )

        self._dependency_health[dependency_name] = health
        await self._persist_dependency_health(health)

        return health

    async def get_dependency_health(
        self, dependency_name: str
    ) -> Optional[DependencyHealth]:
        """Get health status of a dependency."""
        return self._dependency_health.get(dependency_name)

    # Runtime Decision Logic

    async def get_runtime_response(self, **context) -> Any:
        """
        Get the appropriate runtime response based on current state.

        Returns the response that should be sent to the client.
        """
        mode = await self.get_current_mode()

        if mode == RuntimeMode.MAINTENANCE:
            return await self._get_maintenance_response()
        elif mode == RuntimeMode.EMERGENCY_FALLBACK:
            return await self._get_emergency_fallback_response()
        elif mode == RuntimeMode.DEGRADED:
            return await self._get_degraded_response(**context)
        else:  # NORMAL
            return await self._get_normal_response(**context)

    async def _get_maintenance_response(self) -> MaintenanceResponse:
        """Get maintenance mode response."""
        response = MaintenanceResponse()

        if self._maintenance_window:
            response.message = self._maintenance_window.message or response.message
            response.estimated_completion_time = (
                self._maintenance_window.estimated_completion_time
            )

        return response

    async def _get_emergency_fallback_response(self) -> EmergencyFallbackResponse:
        """Get emergency fallback response."""
        return EmergencyFallbackResponse()

    async def _get_degraded_response(self, **context) -> Any:
        """Get degraded mode response."""
        # Placeholder - implement degraded logic
        return {"mode": "degraded", "message": "Service operating in degraded mode"}

    async def _get_normal_response(self, **context) -> Any:
        """Get normal mode response."""
        # This would delegate to the actual chat orchestrator
        return {"mode": "normal", "ready": True}

    async def _determine_optimal_mode(self) -> RuntimeMode:
        """Determine the optimal runtime mode based on current conditions."""
        # Check if maintenance is active
        if self._maintenance_window and self._maintenance_window.enabled:
            return RuntimeMode.MAINTENANCE

        # Check normal mode readiness
        normal_ready = await self._check_normal_readiness()
        if normal_ready:
            return RuntimeMode.NORMAL

        # Check degraded mode readiness
        degraded_ready = await self._check_degraded_readiness()
        if degraded_ready:
            return RuntimeMode.DEGRADED

        # Fallback to emergency
        return RuntimeMode.EMERGENCY_FALLBACK

    async def _check_normal_readiness(self) -> bool:
        """Check if normal mode is ready."""
        # Check critical dependencies
        critical_deps = ["chat_orchestrator", "database", "redis"]
        for dep in critical_deps:
            health = await self.check_dependency_health(dep)
            if health.status != DependencyStatus.HEALTHY:
                return False
        return True

    async def _check_degraded_readiness(self) -> bool:
        """Check if degraded mode is ready."""
        # Degraded mode requires at least database
        health = await self.check_dependency_health("database")
        return health.status == DependencyStatus.HEALTHY

    # Background Tasks

    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._maintenance_monitor_task = asyncio.create_task(
            self._maintenance_monitor_loop()
        )

    async def _stop_background_tasks(self) -> None:
        """Stop background monitoring tasks."""
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._maintenance_monitor_task:
            self._maintenance_monitor_task.cancel()

    async def _health_check_loop(self) -> None:
        """Background loop for dependency health checks."""
        while True:
            try:
                # Check critical dependencies
                await self.check_dependency_health("database")
                await self.check_dependency_health("redis")
                await self.check_dependency_health("chat_orchestrator")

                # Check if mode transition needed
                optimal_mode = await self._determine_optimal_mode()
                if (
                    optimal_mode != self._current_mode
                    and self._current_mode != RuntimeMode.MAINTENANCE
                ):
                    await self.transition_mode(
                        optimal_mode, "Automatic health-based transition"
                    )

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

            await asyncio.sleep(self._dependency_check_interval)

    async def _maintenance_monitor_loop(self) -> None:
        """Background loop for maintenance monitoring."""
        while True:
            try:
                # Check if maintenance should auto-end
                if (
                    self._maintenance_window
                    and self._maintenance_window.enabled
                    and self._maintenance_window.auto_end_policy != "manual"
                ):
                    if await self._should_end_maintenance():
                        await self.disable_maintenance("auto")

            except Exception as e:
                logger.error(f"Error in maintenance monitor loop: {e}")

            await asyncio.sleep(self._maintenance_recheck_interval)

    async def _should_end_maintenance(self) -> bool:
        """Check if maintenance should automatically end."""
        if not self._maintenance_window:
            return False

        policy = self._maintenance_window.auto_end_policy

        if policy == "after_healthy_check":
            return await self._check_normal_readiness()
        elif policy == "at_time" and self._maintenance_window.estimated_completion_time:
            return (
                datetime.utcnow() >= self._maintenance_window.estimated_completion_time
            )

        return False

    # Persistence Methods

    async def _load_runtime_state(self) -> None:
        """Load runtime state from database."""
        try:
            db_client = MultiTenantPostgresClient()
            async with db_client.get_session() as session:
                # Load current state
                result = await session.execute(
                    select(SystemRuntimeState)
                    .order_by(SystemRuntimeState.updated_at.desc())
                    .limit(1)
                )
                state = result.scalar_one_or_none()

                if state:
                    self._current_mode = RuntimeMode(state.current_mode)
                    logger.info(f"Loaded runtime state: {self._current_mode}")

                # Load active maintenance
                result = await session.execute(
                    select(MaintenanceWindow).where(MaintenanceWindow.enabled == True)
                )
                maintenance = result.scalar_one_or_none()

                if maintenance:
                    self._maintenance_window = maintenance
                    logger.info(f"Loaded active maintenance: {maintenance.reason}")

        except Exception as e:
            logger.error(f"Failed to load runtime state: {e}")

    async def _persist_runtime_state(self, reason: str) -> None:
        """Persist current runtime state to database."""
        try:
            db_client = MultiTenantPostgresClient()
            async with db_client.get_session() as session:
                # Update or create state record
                state = SystemRuntimeState(
                    current_mode=self._current_mode.value,
                    normal_ready=await self._check_normal_readiness(),
                    degraded_ready=await self._check_degraded_readiness(),
                    maintenance_enabled=self._maintenance_window is not None,
                    maintenance_reason=self._maintenance_window.reason
                    if self._maintenance_window
                    else None,
                    last_transition_reason=reason,
                )

                session.add(state)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to persist runtime state: {e}")

    async def _persist_dependency_health(self, health: DependencyHealth) -> None:
        """Persist dependency health to database."""
        try:
            db_client = MultiTenantPostgresClient()
            async with db_client.get_session() as session:
                health_record = RuntimeDependencyHealth(
                    dependency_name=health.name,
                    status=health.status.value,
                    reason=health.reason,
                    consecutive_successes=health.consecutive_successes,
                    consecutive_failures=health.consecutive_failures,
                    last_failure_at=health.checked_at
                    if health.status == DependencyStatus.UNHEALTHY
                    else None,
                )

                session.add(health_record)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to persist dependency health: {e}")

    async def _log_runtime_event(
        self, event_type: str, mode: str, details: Any
    ) -> None:
        """Log a runtime event."""
        try:
            db_client = MultiTenantPostgresClient()
            async with db_client.get_session() as session:
                event = ChatRuntimeEvent(
                    event_type=event_type,
                    mode=mode,
                    details_json=details
                    if isinstance(details, dict)
                    else {"message": str(details)},
                )

                session.add(event)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log runtime event: {e}")


# Global instance
_runtime_control_plane: Optional[ChatRuntimeControlPlane] = None


async def get_chat_runtime_control_plane() -> ChatRuntimeControlPlane:
    """Get the global chat runtime control plane instance."""
    global _runtime_control_plane

    if _runtime_control_plane is None:
        _runtime_control_plane = ChatRuntimeControlPlane()
        await _runtime_control_plane.initialize()

    return _runtime_control_plane


__all__ = [
    "ChatRuntimeControlPlane",
    "RuntimeMode",
    "DependencyStatus",
    "MaintenanceResponse",
    "EmergencyFallbackResponse",
    "DependencyHealth",
    "get_chat_runtime_control_plane",
]
