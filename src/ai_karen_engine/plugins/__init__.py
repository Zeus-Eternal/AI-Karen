"""
AI-Karen plugins package - compatibility layer for consolidated plugin system.
This provides backward compatibility for imports expecting ai_karen_engine.plugins.
"""

# Re-export from the consolidated plugin system
try:
    from src.extensions.plugins.core.router import PluginRouter, get_plugin_router, AccessDenied, PluginRecord
    from src.extensions.plugins.core.manager import PluginManager, get_plugin_manager, create_plugin_manager
    from src.extensions.plugins.core.sandbox import run_in_sandbox
    from src.extensions.plugins.core.memory_manager import MemoryManager
    
    __all__ = [
        "PluginRouter", 
        "PluginManager", 
        "get_plugin_router", 
        "get_plugin_manager", 
        "create_plugin_manager",
        "AccessDenied", 
        "PluginRecord",
        "run_in_sandbox",
        "MemoryManager"
    ]
    
except ImportError as e:
    # Fallback for missing components
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to import from consolidated plugin system: {e}")
    
    # Provide minimal stubs
    class PluginRouter:
        def __init__(self):
            pass
    
    class PluginManager:
        def __init__(self):
            pass
    
    class AccessDenied(Exception):
        pass
    
    class PluginRecord:
        def __init__(self):
            pass
    
    class MemoryManager:
        def __init__(self):
            pass
    
    def get_plugin_router():
        return PluginRouter()
    
    def get_plugin_manager():
        return PluginManager()
    
    def create_plugin_manager():
        return PluginManager()
    
    async def run_in_sandbox(*args, **kwargs):
        pass
    
    __all__ = [
        "PluginRouter", 
        "PluginManager", 
        "get_plugin_router", 
        "get_plugin_manager", 
        "create_plugin_manager",
        "AccessDenied", 
        "PluginRecord",
        "run_in_sandbox",
        "MemoryManager"
    ]
