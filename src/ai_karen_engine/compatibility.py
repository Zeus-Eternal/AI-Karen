"""
Backward compatibility layer for directory structure reorganization.

This module provides temporary compatibility imports to ensure
existing code continues to work during the migration period.
"""

import warnings
from typing import Any, Dict
import sys
import importlib


def deprecated_import(old_path: str, new_path: str, removal_version: str = "0.5.0"):
    """
    Decorator to mark imports as deprecated.
    
    Args:
        old_path: The old import path being deprecated
        new_path: The new import path to use instead
        removal_version: Version when the compatibility will be removed
    """
    def decorator(func_or_class):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"Import from '{old_path}' is deprecated. "
                f"Use '{new_path}' instead. "
                f"This compatibility layer will be removed in version {removal_version}.",
                DeprecationWarning,
                stacklevel=3
            )
            return func_or_class(*args, **kwargs)
        
        # Preserve original attributes
        wrapper.__name__ = getattr(func_or_class, '__name__', 'unknown')
        wrapper.__doc__ = getattr(func_or_class, '__doc__', None)
        wrapper.__module__ = getattr(func_or_class, '__module__', None)
        
        return wrapper
    return decorator


class CompatibilityImportManager:
    """Manages compatibility imports during migration."""
    
    def __init__(self):
        self.import_mappings = {
            # Plugin system mappings
            "ai_karen_engine.plugin_manager": "ai_karen_engine.plugins.manager",
            "ai_karen_engine.plugin_router": "ai_karen_engine.plugins.router",
            
            # Individual plugin mappings (examples)
            "ai_karen_engine.plugins.hello_world": "plugins.examples.hello_world",
            "ai_karen_engine.plugins.time_query": "plugins.core.time_query",
            "ai_karen_engine.plugins.weather_query": "plugins.core.weather_query",
            "ai_karen_engine.plugins.autonomous_task_handler": "plugins.automation.autonomous_task_handler",
            "ai_karen_engine.plugins.desktop_agent": "plugins.integrations.desktop_agent",
            "ai_karen_engine.plugins.fine_tune_lnm": "plugins.ai.fine_tune_lnm",
            "ai_karen_engine.plugins.git_merge_safe": "plugins.automation.git_merge_safe",
            "ai_karen_engine.plugins.hf_llm": "plugins.ai.hf_llm",
            "ai_karen_engine.plugins.k8s_scale": "plugins.integrations.k8s_scale",
            "ai_karen_engine.plugins.llm_manager": "plugins.integrations.llm_manager",
            "ai_karen_engine.plugins.llm_services": "plugins.ai.llm_services",
            "ai_karen_engine.plugins.sandbox_fail": "plugins.examples.sandbox_fail",
            "ai_karen_engine.plugins.tui_fallback": "plugins.core.tui_fallback",
        }
        
        self.usage_tracking: Dict[str, int] = {}
    
    def track_usage(self, old_path: str) -> None:
        """Track usage of deprecated import paths."""
        self.usage_tracking[old_path] = self.usage_tracking.get(old_path, 0) + 1
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get report of deprecated import usage."""
        return {
            "total_deprecated_imports": len(self.usage_tracking),
            "usage_by_path": self.usage_tracking,
            "most_used": max(self.usage_tracking.items(), key=lambda x: x[1]) if self.usage_tracking else None
        }
    
    def create_compatibility_module(self, old_module_path: str, new_module_path: str) -> None:
        """Create a compatibility module that redirects to the new location."""
        try:
            # Import the new module
            new_module = __import__(new_module_path, fromlist=[''])
            
            # Create compatibility wrapper
            class CompatibilityModule:
                def __getattr__(self, name):
                    self.track_usage(f"{old_module_path}.{name}")
                    warnings.warn(
                        f"Import from '{old_module_path}' is deprecated. "
                        f"Use '{new_module_path}' instead.",
                        DeprecationWarning,
                        stacklevel=2
                    )
                    return getattr(new_module, name)
            
            # Install compatibility module
            sys.modules[old_module_path] = CompatibilityModule()
            
        except ImportError:
            # New module doesn't exist yet, skip compatibility
            pass


# Global compatibility manager instance
_compatibility_manager = CompatibilityImportManager()


# Plugin System Compatibility Imports
try:
    from ai_karen_engine.plugins.manager import PluginManager as _PluginManager
    from ai_karen_engine.plugins.manager import get_plugin_manager as _get_plugin_manager
    
    @deprecated_import("ai_karen_engine.plugin_manager", "ai_karen_engine.plugins.manager")
    class PluginManager(_PluginManager):
        """Compatibility wrapper for PluginManager."""
        pass
    
    @deprecated_import("ai_karen_engine.plugin_manager", "ai_karen_engine.plugins.manager")
    def get_plugin_manager(*args, **kwargs):
        """Compatibility wrapper for get_plugin_manager."""
        return _get_plugin_manager(*args, **kwargs)
    
except ImportError:
    # New plugin system not available yet
    PluginManager = None
    get_plugin_manager = None


try:
    from ai_karen_engine.plugins.router import PluginRouter as _PluginRouter
    from ai_karen_engine.plugins.router import PluginRecord as _PluginRecord
    from ai_karen_engine.plugins.router import AccessDenied as _AccessDenied
    from ai_karen_engine.plugins.router import get_plugin_router as _get_plugin_router
    
    @deprecated_import("ai_karen_engine.plugin_router", "ai_karen_engine.plugins.router")
    class PluginRouter(_PluginRouter):
        """Compatibility wrapper for PluginRouter."""
        pass
    
    @deprecated_import("ai_karen_engine.plugin_router", "ai_karen_engine.plugins.router")
    class PluginRecord(_PluginRecord):
        """Compatibility wrapper for PluginRecord."""
        pass
    
    @deprecated_import("ai_karen_engine.plugin_router", "ai_karen_engine.plugins.router")
    class AccessDenied(_AccessDenied):
        """Compatibility wrapper for AccessDenied."""
        pass
    
    @deprecated_import("ai_karen_engine.plugin_router", "ai_karen_engine.plugins.router")
    def get_plugin_router(*args, **kwargs):
        """Compatibility wrapper for get_plugin_router."""
        return _get_plugin_router(*args, **kwargs)
    
except ImportError:
    # New plugin system not available yet
    PluginRouter = None
    PluginRecord = None
    AccessDenied = None
    get_plugin_router = None


# Individual Plugin Compatibility
# Note: These will be created dynamically as plugins are moved

def create_plugin_compatibility_imports():
    """Create compatibility imports for individual plugins."""
    plugin_mappings = {
        "ai_karen_engine.plugins.hello_world": "plugins.examples.hello_world",
        "ai_karen_engine.plugins.time_query": "plugins.core.time_query",
        "ai_karen_engine.plugins.weather_query": "plugins.core.weather_query",
        # Add more as needed during migration
    }
    
    for old_path, new_path in plugin_mappings.items():
        try:
            # Try to import from new location
            __import__(new_path, fromlist=[""])

            # Create compatibility module
            _compatibility_manager.create_compatibility_module(old_path, new_path)
            
        except ImportError:
            # New location doesn't exist yet, skip
            continue


# Utility functions for migration support
def check_deprecated_imports() -> Dict[str, Any]:
    """Check for usage of deprecated imports."""
    return _compatibility_manager.get_usage_report()


def warn_about_deprecated_import(old_path: str, new_path: str) -> None:
    """Issue a deprecation warning for an import."""
    _compatibility_manager.track_usage(old_path)
    warnings.warn(
        f"Import from '{old_path}' is deprecated. Use '{new_path}' instead.",
        DeprecationWarning,
        stacklevel=3
    )


def is_migration_complete() -> bool:
    """Check if migration is complete by testing new import paths."""
    try:
        # Test key new imports without exposing them
        importlib.import_module("ai_karen_engine.plugins.manager")
        importlib.import_module("ai_karen_engine.plugins.router")
        return True
    except ImportError:
        return False


# Auto-setup compatibility imports when module is imported
if __name__ != "__main__":
    create_plugin_compatibility_imports()


# Export compatibility components
__all__ = [
    "PluginManager",
    "PluginRouter", 
    "PluginRecord",
    "AccessDenied",
    "get_plugin_manager",
    "get_plugin_router",
    "deprecated_import",
    "check_deprecated_imports",
    "warn_about_deprecated_import",
    "is_migration_complete",
]