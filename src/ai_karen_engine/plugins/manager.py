"""
Compatibility layer for plugin manager imports.
Re-exports from the consolidated plugin system.
"""

try:
    from ai_karen_engine.plugin_manager import (
        PluginManager,
        get_plugin_manager,
        create_plugin_manager,
        PLUGIN_CALLS,
        PLUGIN_FAILURES,
        MEMORY_WRITES
    )
    
    __all__ = [
        "PluginManager",
        "get_plugin_manager",
        "create_plugin_manager",
        "PLUGIN_CALLS",
        "PLUGIN_FAILURES", 
        "MEMORY_WRITES"
    ]
    
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to import plugin manager from consolidated system: {e}")
    
    # Provide minimal stubs
    class PluginManager:
        def __init__(self):
            pass
    
    class _DummyMetric:
        def labels(self, **kw): 
            return self
        def inc(self, n: int = 1): 
            pass
    
    PLUGIN_CALLS = _DummyMetric()
    PLUGIN_FAILURES = _DummyMetric()
    MEMORY_WRITES = _DummyMetric()
    
    def get_plugin_manager():
        return PluginManager()
    
    def create_plugin_manager():
        return PluginManager()
    
    __all__ = [
        "PluginManager",
        "get_plugin_manager",
        "create_plugin_manager",
        "PLUGIN_CALLS",
        "PLUGIN_FAILURES", 
        "MEMORY_WRITES"
    ]
