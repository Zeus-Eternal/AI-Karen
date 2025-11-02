"""
Compatibility layer for plugin sandbox imports.
Re-exports from the consolidated plugin system.
"""

try:
    from src.extensions.plugins.core.sandbox import run_in_sandbox
    
    __all__ = ["run_in_sandbox"]
    
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to import plugin sandbox from consolidated system: {e}")
    
    # Provide minimal stub
    async def run_in_sandbox(*args, **kwargs):
        pass
    
    __all__ = ["run_in_sandbox"]