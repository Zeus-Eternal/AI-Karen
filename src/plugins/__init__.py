"""
AI Karen Plugins - Focused Function Implementations

This package contains all plugin implementations for AI Karen.
Plugins are simple, focused functions suitable for:
- Single-purpose utilities
- Quick integrations
- Simple transformations
- Lightweight tools
- External API calls
- Data processing functions

Directory Structure:
-------------------
plugins/
├── ai/                    # AI and LLM plugins
├── automation/            # Automation and workflow plugins
├── integrations/          # Third-party service integrations
├── system/                # Core system plugins
├── examples/              # Example plugins and templates
├── __meta/                # Plugin system metadata
└── memory_manager.py      # Plugin memory management helper

Framework Location:
------------------
The core plugin framework is located in:
    src/ai_karen_engine/plugins/

Import the framework classes from there:
    from ai_karen_engine.plugins import PluginRouter, PluginManager

Plugin Discovery:
----------------
Plugins are automatically discovered by the PluginRouter.
Each plugin should have:
- plugin_manifest.json  # Plugin configuration
- handler.py            # Main plugin logic with async run() function
- README.md             # Documentation

Development:
-----------
To create a new plugin:
1. Choose category: ai, automation, integrations, system, or examples
2. Create directory: src/plugins/[category]/[name]/
3. Add plugin_manifest.json
4. Add handler.py with async def run(params) function
5. Add README.md
6. Plugin is auto-discovered by PluginRouter

See STRUCTURE.md for more details.
"""

# Framework is in ai_karen_engine.plugins
# This __init__ is for plugin implementations only

# Import memory manager helper for plugins
from .memory_manager import MemoryManager

__all__ = [
    "MemoryManager",
    # Plugin implementations are discovered dynamically by PluginRouter
]

# Version info
__version__ = "1.0.0"
__author__ = "AI Karen Team"
