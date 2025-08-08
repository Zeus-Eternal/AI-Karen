"""
HookMixin class that can be added to existing managers without code duplication.
"""
# mypy: ignore-errors

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from .hook_types import HookTypes
from .models import HookContext, HookExecutionSummary, HookResult

if TYPE_CHECKING:
    from .hook_manager import HookManager

logger = logging.getLogger(__name__)


class HookMixin:
    """
    Mixin class that adds hook capabilities to existing managers.

    This mixin can be added to PluginManager, ExtensionManager, and other
    components to provide unified hook functionality without code duplication.
    """

    def __init__(self, *args, **kwargs):
        """Initialize hook mixin."""
        super().__init__(*args, **kwargs)
        self._hook_manager: Optional[HookManager] = None
        self._hook_enabled = True
        self._hook_logger = logging.getLogger(f"{self.__class__.__name__}.hooks")

    @property
    def hook_manager(self) -> Optional[HookManager]:
        """Get the hook manager instance."""
        if self._hook_manager is None:
            try:
                from .hook_manager import get_hook_manager

                self._hook_manager = get_hook_manager()
            except Exception as e:
                self._hook_logger.warning(f"Failed to get hook manager: {e}")
        return self._hook_manager

    def set_hook_manager(self, hook_manager: HookManager) -> None:
        """Set the hook manager instance."""
        self._hook_manager = hook_manager

    def enable_hooks(self) -> None:
        """Enable hook execution."""
        self._hook_enabled = True
        self._hook_logger.info("Hooks enabled")

    def disable_hooks(self) -> None:
        """Disable hook execution."""
        self._hook_enabled = False
        self._hook_logger.info("Hooks disabled")

    def are_hooks_enabled(self) -> bool:
        """Check if hooks are enabled."""
        return self._hook_enabled and self.hook_manager is not None

    async def register_hook(
        self,
        hook_type: str,
        handler: Callable,
        priority: int = 50,
        conditions: Optional[Dict[str, Any]] = None,
        source_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Register a hook with the hook manager.

        Args:
            hook_type: Type of hook to register
            handler: Hook handler function
            priority: Hook priority (lower = higher priority)
            conditions: Conditions for hook execution
            source_name: Name of the source registering the hook

        Returns:
            Hook ID if successful, None otherwise
        """
        if not self.are_hooks_enabled():
            self._hook_logger.debug(
                f"Hooks disabled, skipping registration of {hook_type}"
            )
            return None

        try:
            return await self.hook_manager.register_hook(
                hook_type=hook_type,
                handler=handler,
                priority=priority,
                conditions=conditions or {},
                source_type=self.__class__.__name__.lower(),
                source_name=source_name or getattr(self, "name", "unknown"),
            )
        except Exception as e:
            self._hook_logger.error(f"Failed to register hook {hook_type}: {e}")
            return None

    async def unregister_hook(self, hook_id: str) -> bool:
        """
        Unregister a hook.

        Args:
            hook_id: ID of hook to unregister

        Returns:
            True if successful, False otherwise
        """
        if not self.are_hooks_enabled():
            return False

        try:
            return await self.hook_manager.unregister_hook(hook_id)
        except Exception as e:
            self._hook_logger.error(f"Failed to unregister hook {hook_id}: {e}")
            return False

    async def trigger_hooks(
        self,
        hook_type: str,
        data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 30.0,
    ) -> HookExecutionSummary:
        """
        Trigger all hooks of a specific type.

        Args:
            hook_type: Type of hooks to trigger
            data: Data to pass to hooks
            user_context: User context information
            timeout_seconds: Timeout for hook execution

        Returns:
            Summary of hook execution
        """
        if not self.are_hooks_enabled():
            self._hook_logger.debug(f"Hooks disabled, skipping trigger of {hook_type}")
            return HookExecutionSummary(
                hook_type=hook_type,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )

        try:
            context = HookContext(
                hook_type=hook_type,
                data=data,
                user_context=user_context,
                metadata={
                    "source_class": self.__class__.__name__,
                    "source_name": getattr(self, "name", "unknown"),
                },
            )

            return await self.hook_manager.trigger_hooks(context, timeout_seconds)

        except Exception as e:
            self._hook_logger.error(f"Failed to trigger hooks {hook_type}: {e}")
            return HookExecutionSummary(
                hook_type=hook_type,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=1,
                total_execution_time_ms=0.0,
                results=[HookResult.error_result("unknown", str(e))],
            )

    async def trigger_hook_safe(
        self,
        hook_type: str,
        data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        default_result: Any = None,
    ) -> Any:
        """
        Safely trigger hooks and return a default result if hooks fail.

        This method is useful for non-critical hook triggers where the
        calling code should continue even if hooks fail.

        Args:
            hook_type: Type of hooks to trigger
            data: Data to pass to hooks
            user_context: User context information
            default_result: Result to return if hooks fail

        Returns:
            Hook results or default_result if hooks fail
        """
        try:
            summary = await self.trigger_hooks(hook_type, data, user_context)
            if summary.successful_hooks > 0:
                return [result.result for result in summary.results if result.success]
            return default_result
        except Exception as e:
            self._hook_logger.debug(f"Safe hook trigger failed for {hook_type}: {e}")
            return default_result

    def get_hook_stats(self) -> Dict[str, Any]:
        """
        Get hook statistics for this component.

        Returns:
            Dictionary with hook statistics
        """
        if not self.are_hooks_enabled():
            return {"hooks_enabled": False, "registered_hooks": 0, "hook_types": []}

        try:
            source_type = self.__class__.__name__.lower()
            source_name = getattr(self, "name", "unknown")

            registered_hooks = self.hook_manager.get_hooks_by_source(
                source_type, source_name
            )
            hook_types = list(set(hook.hook_type for hook in registered_hooks))

            return {
                "hooks_enabled": True,
                "registered_hooks": len(registered_hooks),
                "hook_types": hook_types,
                "hook_manager_available": True,
            }
        except Exception as e:
            self._hook_logger.error(f"Failed to get hook stats: {e}")
            return {
                "hooks_enabled": False,
                "registered_hooks": 0,
                "hook_types": [],
                "error": str(e),
            }

    async def _register_lifecycle_hooks(self) -> None:
        """
        Register standard lifecycle hooks for this component.

        This method should be called during component initialization
        to register standard lifecycle hooks.
        """
        component_name = self.__class__.__name__.lower()

        # Register startup hook
        await self.register_hook(
            HookTypes.SYSTEM_STARTUP,
            self._on_startup_hook,
            priority=50,
            source_name=f"{component_name}_lifecycle",
        )

        # Register shutdown hook
        await self.register_hook(
            HookTypes.SYSTEM_SHUTDOWN,
            self._on_shutdown_hook,
            priority=50,
            source_name=f"{component_name}_lifecycle",
        )

    async def _on_startup_hook(self, context: HookContext) -> Dict[str, Any]:
        """Default startup hook handler."""
        return {
            "component": self.__class__.__name__,
            "status": "started",
            "timestamp": context.timestamp.isoformat(),
        }

    async def _on_shutdown_hook(self, context: HookContext) -> Dict[str, Any]:
        """Default shutdown hook handler."""
        return {
            "component": self.__class__.__name__,
            "status": "shutdown",
            "timestamp": context.timestamp.isoformat(),
        }

    def _get_hook_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Get standard context data for hook triggers.

        This method can be overridden by subclasses to provide
        component-specific context data.
        """
        return {
            "component": self.__class__.__name__,
            "component_name": getattr(self, "name", "unknown"),
            **kwargs,
        }
