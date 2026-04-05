import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("kari.plugin_manager")

class PluginManager:
    """
    Unified Application Integration Layer for Karen AI Extensions.
    Coordinated by:
    - ExtensionLifecycleManager: State and Discovery
    - PermissionsManager: RBAC and Security
    - PluginRouter: AI Orchestration and Dispatch
    """
    def __init__(self, extensions_dir: str = "src/extensions"):
        from .permissions_manager import PermissionsManager
        from .sandbox_manager import SandboxManager
        from ..host.router import get_plugin_router
        from ..registry.plugin_registry import get_registry

        self.extensions_dir = extensions_dir
        self.registry = get_registry()
        self.router = get_plugin_router()
        self.permissions = PermissionsManager()
        self.sandbox = SandboxManager()
        self.lifecycle = None

    def _ensure_lifecycle_manager(self):
        if self.lifecycle is None:
            from .lifecycle_manager import ExtensionLifecycleManager

            self.lifecycle = ExtensionLifecycleManager(
                extensions_dir=self.extensions_dir,
                app_instance=None,  # Wired during app startup
            )
        return self.lifecycle

    async def initialize(self):
        """Perform full system initialization."""
        logger.info("Initializing Modular Extension Backbone...")
        lifecycle = self._ensure_lifecycle_manager()
        await lifecycle.initialize()
        await self.router.reload()
        logger.info("Modular Extension Backbone Ready.")

    async def run_plugin(
        self,
        name: str,
        params: Dict[str, Any],
        user_ctx: Dict[str, Any]
    ) -> Any:
        """
        Main execution entry point from the Engine.
        Enforces permissions and delegates to Router for dispatch.
        """
        # 1. Permission Check
        roles = user_ctx.get("roles", [])
        if not await self.permissions.check_permission(name, roles):
            raise PermissionError(f"User roles {roles} not permitted for extension {name}")

        # 2. Dispatch
        return await self.router.dispatch(name, params, roles=roles)

    def get_health_summary(self) -> Dict[str, Any]:
        """Summarize health across all extensions via LifecycleManager."""
        lifecycle = self.lifecycle
        active = lifecycle.get_active_extensions() if lifecycle else []
        total = len(self.registry.list_discovered())
        return {
            "status": "healthy" if len(active) > 0 or total == 0 else "degraded",
            "active_count": len(active),
            "discovered_count": total,
            "lifecycle_states": {
                name: state.value for name, state in lifecycle.extension_states.items()
            } if lifecycle else {},
        }

# Singleton accessor
_manager_instance: Optional[PluginManager] = None

def get_plugin_manager() -> PluginManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PluginManager()
    return _manager_instance
