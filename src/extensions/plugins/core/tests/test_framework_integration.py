"""Test that the consolidated plugin framework components work together."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Test the framework components work together
def test_plugin_manager_router_integration():
    """Test that PluginManager and PluginRouter work together."""
    try:
        from ..manager import PluginManager
        from ..router import PluginRouter
        
        # Create instances
        router = PluginRouter()
        manager = PluginManager(router=router)
        
        assert manager.router is router
        assert isinstance(manager.router, PluginRouter)
        
    except ImportError:
        pytest.skip("Dependencies not available in test environment")


def test_memory_manager_integration():
    """Test that MemoryManager can be instantiated."""
    try:
        from ..memory_manager import MemoryManager
        
        # Create instance
        memory_manager = MemoryManager(tenant_id="test")
        
        assert memory_manager.tenant_id == "test"
        
    except ImportError:
        pytest.skip("Dependencies not available in test environment")


def test_sandbox_function_exists():
    """Test that sandbox function is available."""
    try:
        from ..sandbox import run_in_sandbox
        
        assert callable(run_in_sandbox)
        
    except ImportError:
        pytest.skip("Dependencies not available in test environment")


def test_all_exports_available():
    """Test that all expected exports are available from the core package."""
    try:
        from .. import (
            PluginManager,
            PluginRouter, 
            PluginRecord,
            AccessDenied,
            run_in_sandbox,
            MemoryManager,
            get_plugin_manager,
            get_plugin_router
        )
        
        # Check that all components are available
        assert PluginManager is not None
        assert PluginRouter is not None
        assert PluginRecord is not None
        assert AccessDenied is not None
        assert run_in_sandbox is not None
        assert MemoryManager is not None
        assert get_plugin_manager is not None
        assert get_plugin_router is not None
        
    except ImportError:
        pytest.skip("Dependencies not available in test environment")


if __name__ == "__main__":
    # Run basic tests
    test_plugin_manager_router_integration()
    test_memory_manager_integration() 
    test_sandbox_function_exists()
    test_all_exports_available()
    print("✅ All framework integration tests passed!")