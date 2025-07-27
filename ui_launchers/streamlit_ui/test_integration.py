#!/usr/bin/env python3
"""
Simple integration test to verify backend connectivity
"""

import sys
import os
import asyncio
import logging

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from ai_karen_engine.services.backend_integration import get_backend_service
        print("✅ Backend integration service imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import backend integration: {e}")
        return False
    
    try:
        from ai_karen_engine.services.data_flow_manager import (
            get_data_flow_manager,
            get_streamlit_bridge,
        )
        print("✅ Data flow manager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import data flow manager: {e}")
        return False
    
    try:
        from components.backend_components import (
            render_memory_explorer,
            render_plugin_manager,
            render_system_health
        )
        print("✅ Backend components imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import backend components: {e}")
        return False
    
    return True


def test_backend_service():
    """Test backend service initialization."""
    print("\n🔧 Testing backend service...")
    
    try:
        from ai_karen_engine.services.backend_integration import get_backend_service
        backend = get_backend_service()
        
        # Test service adapters
        assert backend.memory is not None, "Memory adapter not initialized"
        assert backend.plugins is not None, "Plugin adapter not initialized"
        assert backend.pages is not None, "Page adapter not initialized"
        assert backend.analytics is not None, "Analytics adapter not initialized"
        
        print("✅ Backend service initialized successfully")
        print(f"   - Tenant ID: {backend.config.tenant_id}")
        print(f"   - Caching enabled: {backend.config.enable_caching}")
        
        return True
    except Exception as e:
        print(f"❌ Backend service test failed: {e}")
        return False


def test_data_flow_manager():
    """Test data flow manager initialization."""
    print("\n🔄 Testing data flow manager...")
    
    try:
        from ai_karen_engine.services.data_flow_manager import (
            get_data_flow_manager,
            get_streamlit_bridge,
        )
        
        dfm = get_data_flow_manager()
        bridge = get_streamlit_bridge()
        
        assert dfm is not None, "Data flow manager not initialized"
        assert bridge is not None, "Streamlit bridge not initialized"
        
        # Test sync status
        status = dfm.get_sync_status()
        assert isinstance(status, dict), "Sync status should be a dictionary"
        
        print("✅ Data flow manager initialized successfully")
        print(f"   - Cache size: {status.get('cache_size', 0)}")
        print(f"   - Queue size: {status.get('queue_size', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Data flow manager test failed: {e}")
        return False


async def test_async_operations():
    """Test async operations."""
    print("\n⚡ Testing async operations...")
    
    try:
        from ai_karen_engine.services.backend_integration import get_backend_service
        backend = get_backend_service()
        
        # Test memory stats (async operation)
        stats = await backend.memory.get_memory_stats()
        assert isinstance(stats, dict), "Memory stats should be a dictionary"
        
        # Test analytics (async operation)
        metrics = await backend.analytics.get_system_metrics()
        assert isinstance(metrics, dict), "System metrics should be a dictionary"
        
        # Test health check
        health = await backend.health_check()
        assert isinstance(health, dict), "Health check should return a dictionary"
        assert "overall" in health, "Health check should include overall status"
        
        print("✅ Async operations working correctly")
        print(f"   - Health status: {health.get('overall', 'unknown')}")
        print(f"   - Services checked: {len(health.get('services', {}))}")
        
        return True
    except Exception as e:
        print(f"❌ Async operations test failed: {e}")
        return False


def test_ui_logic_integration():
    """Test integration with existing UI logic."""
    print("\n🎨 Testing UI logic integration...")
    
    try:
        # Test if we can import existing pages
        try:
            from src.ui_logic.pages.home import home_page
            from src.ui_logic.pages.memory import memory_page
            from src.ui_logic.config.pages_manifest import PAGES
            print("✅ Existing UI logic pages imported successfully")
            print(f"   - Available pages: {len(PAGES)}")
            backend_available = True
        except ImportError:
            print("⚠️ Existing UI logic not available (using fallbacks)")
            backend_available = False
        
        # Test page service integration
        from ai_karen_engine.services.backend_integration import get_backend_service
        backend = get_backend_service()
        
        pages = backend.pages.get_available_pages()
        print(f"✅ Page service integration working")
        print(f"   - Available pages from service: {len(pages)}")
        
        return True
    except Exception as e:
        print(f"❌ UI logic integration test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🧪 AI Karen Backend Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Backend Service", test_backend_service),
        ("Data Flow Manager", test_data_flow_manager),
        ("UI Logic Integration", test_ui_logic_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} encountered an error: {e}")
            results.append((test_name, False))
    
    # Run async tests
    print("\n⚡ Running async tests...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async_result = loop.run_until_complete(test_async_operations())
        results.append(("Async Operations", async_result))
        loop.close()
    except Exception as e:
        print(f"❌ Async tests failed: {e}")
        results.append(("Async Operations", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend integration is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)