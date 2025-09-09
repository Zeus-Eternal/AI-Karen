"""
AI-Karen plugins package - symlink to root plugins directory.
This provides backward compatibility for imports expecting ai_karen_engine.plugins.
"""

# Re-export from the unified plugins system
import sys
from pathlib import Path

# Add the root plugins directory to the path
plugins_root = Path(__file__).parent.parent.parent.parent / "plugins"
if str(plugins_root) not in sys.path:
    sys.path.insert(0, str(plugins_root))

# Import and re-export from the unified plugins system
try:
    from router import PluginRouter
    from manager import PluginManager
    
    __all__ = ["PluginRouter", "PluginManager"]
    
except ImportError as e:
    # Fallback for missing components
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to import from unified plugins system: {e}")
    
    # Provide minimal stubs
    class PluginRouter:
        def __init__(self):
            pass
    
    class PluginManager:
        def __init__(self):
            pass
    
    __all__ = ["PluginRouter", "PluginManager"]
