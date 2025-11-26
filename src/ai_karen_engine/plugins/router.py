"""
Compatibility layer for plugin router imports.
Re-exports from the consolidated plugin system.
"""

try:
    from ai_karen_engine.plugin_router import (
        PluginRouter,
        get_plugin_router,
        AccessDenied,
        PluginRecord,
        PLUGIN_IMPORT_ERRORS
    )
    
    __all__ = [
        "PluginRouter",
        "get_plugin_router", 
        "AccessDenied",
        "PluginRecord",
        "PLUGIN_IMPORT_ERRORS"
    ]
    
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to import plugin router from consolidated system: {e}")
    
    # Provide minimal stubs
    class PluginRouter:
        def __init__(self):
            pass
    
    class AccessDenied(Exception):
        pass
    
    class PluginRecord:
        def __init__(self):
            pass
    
    class _DummyMetric:
        def labels(self, **kw): 
            return self
        def inc(self, n: int = 1): 
            pass
    
    PLUGIN_IMPORT_ERRORS = _DummyMetric()
    
    def get_plugin_router():
        return PluginRouter()
    
    __all__ = [
        "PluginRouter",
        "get_plugin_router", 
        "AccessDenied",
        "PluginRecord",
        "PLUGIN_IMPORT_ERRORS"
    ]
