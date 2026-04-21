"""
Execution Engine Module

Handles task execution with policy enforcement and error handling.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as ConcurrentTimeoutError,
)

from .execution_policy import (
    ExecutionPolicy,
    ExecutionMode,
    ExecutionPriority,
    execution_policy,
)
from ..contracts.execution_action import ExecutionAction
from ..contracts.runtime_response import RuntimeResponse, ResponseStatus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Execution result container."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    retry_count: int = 0


class ExecutionEngine:
    """Task execution engine with policy enforcement."""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.policy = execution_policy
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def execute_action(
        self, action: ExecutionAction, context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute an action with policy enforcement."""
        start_time = time.time()

        try:
            # Validate execution policy
            if not self.policy.validate_execution(
                action.action_type, action.parameters
            ):
                return ExecutionResult(
                    success=False,
                    error="Execution parameters violate policy",
                    duration=time.time() - start_time,
                )

            # Determine execution mode
            mode = self.policy.get_execution_mode(action.action_type, action.parameters)

            # Execute based on mode
            if mode == ExecutionMode.SYNCHRONOUS:
                result = await self._execute_sync(action, context)
            elif mode == ExecutionMode.ASYNCHRONOUS:
                result = await self._execute_async(action, context)
            elif mode == ExecutionMode.STREAMING:
                result = await self._execute_streaming(action, context)
            elif mode == ExecutionMode.BATCH:
                result = await self._execute_batch(action, context)
            else:
                raise ValueError(f"Unsupported execution mode: {mode}")

            result.duration = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"Execution failed for {action.action_type}: {e}")
            return ExecutionResult(
                success=False, error=str(e), duration=time.time() - start_time
            )

    async def _execute_sync(
        self, action: ExecutionAction, context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute synchronously in thread pool."""
        constraint = self.policy.get_constraint(action.action_type)

        try:
            # Run in thread pool for CPU-bound work
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, self._execute_action_impl, action, context
            )

            return ExecutionResult(success=True, data=result)

        except ConcurrentTimeoutError:
            return ExecutionResult(
                success=False,
                error="Execution timeout",
                retry_count=constraint.max_retries,
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def _execute_async(
        self, action: ExecutionAction, context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute asynchronously."""
        constraint = self.policy.get_constraint(action.action_type)

        try:
            # Check if action handler exists
            handler = self._get_action_handler(action.action_type)
            if not handler:
                return ExecutionResult(success=False, error="No handler found")

            # Execute with timeout
            result = await asyncio.wait_for(
                handler(action, context), timeout=constraint.timeout or 30.0
            )

            return ExecutionResult(success=True, data=result)

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error="Async execution timeout",
                retry_count=constraint.max_retries,
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def _execute_streaming(
        self, action: ExecutionAction, context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute with streaming support."""
        constraint = self.policy.get_constraint(action.action_type)

        try:
            handler = self._get_streaming_handler(action.action_type)
            if not handler:
                return ExecutionResult(
                    success=False, error="No streaming handler found"
                )

            # Execute with streaming
            async for chunk in handler(action, context):
                # Process chunks (could be sent to client)
                pass

            return ExecutionResult(success=True, data="Streaming completed")

        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def _execute_batch(
        self, action: ExecutionAction, context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute batch of actions."""
        constraint = self.policy.get_constraint(action.action_type)

        try:
            # Extract batch items from parameters
            batch_items = action.parameters.get("batch_items", [])
            if not batch_items:
                return ExecutionResult(success=False, error="No batch items provided")

            results = []
            for item in batch_items:
                item_action = ExecutionAction(
                    action_type=action.action_type,
                    parameters=item,
                    metadata=action.metadata,
                )

                item_result = await self._execute_async(item_action, context)
                results.append(item_result)

            return ExecutionResult(success=True, data={"results": results})

        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    def _execute_action_impl(
        self, action: ExecutionAction, context: Dict[str, Any]
    ) -> Any:
        """Synchronous action implementation."""
        handler = self._get_action_handler(action.action_type)
        if not handler:
            raise ValueError(f"No handler found for {action.action_type}")

        return handler(action, context)

    def _get_action_handler(self, action_type: str) -> Optional[Callable]:
        """Get action handler for given type."""
        # This should be implemented with actual action registry
        # For now, return None to be implemented by the runtime
        return None

    def _get_streaming_handler(self, action_type: str) -> Optional[Callable]:
        """Get streaming handler for given type."""
        # This should be implemented with actual streaming registry
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
            return True
        return False

    def get_running_tasks(self) -> Dict[str, Any]:
        """Get information about running tasks."""
        return {
            task_id: {
                "status": task.get_status(),
                "created_at": task.get_coro().cr_frame.f_code.co_name
                if hasattr(task.get_coro(), "cr_frame")
                else "unknown",
            }
            for task_id, task in self._running_tasks.items()
        }


# Global execution engine instance
execution_engine = ExecutionEngine()
