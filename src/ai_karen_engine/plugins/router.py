"""
Plugin Router - symlink to unified plugins router.
Provides backward compatibility for ai_karen_engine.plugins.router imports.
"""

import sys
from pathlib import Path

# Add the root plugins directory to the path
plugins_root = Path(__file__).parent.parent.parent.parent / "plugins"
if str(plugins_root) not in sys.path:
    sys.path.insert(0, str(plugins_root))

# Import and re-export the PluginRouter from unified system
try:
    from router import PluginRouter as UnifiedPluginRouter
    
    # Alias for backward compatibility
    PluginRouter = UnifiedPluginRouter
    
    __all__ = ["PluginRouter"]
    
except ImportError:
    # Fallback stub if unified system not available
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Unified plugin router not found, using fallback stub")
    
    class PluginRouter:
        """Fallback PluginRouter stub for compatibility"""
        
        def __init__(self):
            self.routes = {}
            
        def register_plugin(self, plugin_name: str, plugin_instance):
            """Register a plugin"""
            self.routes[plugin_name] = plugin_instance
            
        def get_plugin(self, plugin_name: str):
            """Get a registered plugin"""
            return self.routes.get(plugin_name)
            
        def list_plugins(self):
            """List all registered plugins"""
            return list(self.routes.keys())
    
    __all__ = ["PluginRouter"]
