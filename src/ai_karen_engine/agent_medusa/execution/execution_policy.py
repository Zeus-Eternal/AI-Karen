"""
Execution Policy Module

Defines execution policies and constraints for AgentMedusa runtime.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionPriority(str, Enum):
    """Execution priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class ExecutionMode(str, Enum):
    """Execution modes for different scenarios."""

    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    STREAMING = "streaming"
    BATCH = "batch"


@dataclass
class ExecutionConstraint:
    """Execution constraint definition."""

    max_duration: Optional[float] = None  # Maximum execution time in seconds
    max_retries: int = 3
    timeout: Optional[float] = None
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    mode: ExecutionMode = ExecutionMode.ASYNCHRONOUS
    resource_limits: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None


class ExecutionPolicy:
    """Execution policy manager."""

    def __init__(self):
        self.constraints: Dict[str, ExecutionConstraint] = {}
        self.default_constraint = ExecutionConstraint()

    def add_constraint(self, task_type: str, constraint: ExecutionConstraint) -> None:
        """Add execution constraint for specific task type."""
        self.constraints[task_type] = constraint
        logger.debug(f"Added execution constraint for {task_type}")

    def get_constraint(self, task_type: str) -> ExecutionConstraint:
        """Get execution constraint for task type."""
        return self.constraints.get(task_type, self.default_constraint)

    def validate_execution(
        self, task_type: str, proposed_params: Dict[str, Any]
    ) -> bool:
        """Validate if execution parameters comply with policy."""
        constraint = self.get_constraint(task_type)

        # Check duration limits
        if constraint.max_duration and "duration" in proposed_params:
            if proposed_params["duration"] > constraint.max_duration:
                logger.warning(
                    f"Duration {proposed_params['duration']} exceeds max {constraint.max_duration}"
                )
                return False

        # Check priority compatibility
        if "priority" in proposed_params:
            if proposed_params["priority"] not in [p.value for p in ExecutionPriority]:
                logger.warning(f"Invalid priority: {proposed_params['priority']}")
                return False

        return True

    def get_execution_mode(
        self, task_type: str, params: Dict[str, Any]
    ) -> ExecutionMode:
        """Determine appropriate execution mode."""
        constraint = self.get_constraint(task_type)

        # Override with explicit mode in params
        if "mode" in params:
            try:
                return ExecutionMode(params["mode"])
            except ValueError:
                logger.warning(f"Invalid execution mode: {params['mode']}")

        return constraint.mode


# Global execution policy instance
execution_policy = ExecutionPolicy()


def initialize_execution_policy() -> None:
    """Initialize default execution policies."""
    # Add common task type constraints
    execution_policy.add_constraint(
        "tool_execution",
        ExecutionConstraint(
            max_duration=30.0,
            max_retries=2,
            priority=ExecutionPriority.HIGH,
            mode=ExecutionMode.ASYNCHRONOUS,
        ),
    )

    execution_policy.add_constraint(
        "memory_access",
        ExecutionConstraint(
            max_duration=10.0,
            max_retries=1,
            priority=ExecutionPriority.NORMAL,
            mode=ExecutionMode.SYNCHRONOUS,
        ),
    )

    execution_policy.add_constraint(
        "response_synthesis",
        ExecutionConstraint(
            max_duration=60.0,
            max_retries=1,
            priority=ExecutionPriority.HIGH,
            mode=ExecutionMode.SYNCHRONOUS,
        ),
    )

    execution_policy.add_constraint(
        "planning",
        ExecutionConstraint(
            max_duration=120.0,
            max_retries=1,
            priority=ExecutionPriority.NORMAL,
            mode=ExecutionMode.ASYNCHRONOUS,
        ),
    )


# Initialize on import
initialize_execution_policy()
